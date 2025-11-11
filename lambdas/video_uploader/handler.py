"""
Lambda function to upload videos to YouTube
"""
import json
import os
import boto3
import tempfile
from typing import Dict, Any
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Upload video to YouTube with metadata and transcript

    Args:
        event: Lambda event containing s3_bucket, user_id, video_id, channel_id,
               transcript paths
        context: Lambda context

    Returns:
        Dictionary with YouTube video ID and URL
    """
    s3_bucket = event['s3_bucket']
    user_id = event['user_id']
    video_id = event['video_id']
    channel_id = event['channel_id']
    transcript_vtt_path = event.get('transcript_vtt')
    transcript_md_path = event.get('transcript_md')

    # Construct S3 paths
    video_prefix = f"{user_id}/{channel_id}/videos/{video_id}"
    video_key = f"{video_prefix}/video.mp4"
    metadata_key = f"{video_prefix}/metadata.json"
    thumbnail_key = f"{video_prefix}/thumbnail.jpg"

    print(f"Uploading video to YouTube: {video_key}")

    s3 = boto3.client('s3')
    ssm = boto3.client('ssm')

    try:
        # Download video file
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as video_file:
            video_path = video_file.name
            print(f"Downloading video from S3: {s3_bucket}/{video_key}")
            s3.download_file(s3_bucket, video_key, video_path)

        # Download metadata
        print(f"Downloading metadata from S3: {s3_bucket}/{metadata_key}")
        metadata_obj = s3.get_object(Bucket=s3_bucket, Key=metadata_key)
        metadata = json.loads(metadata_obj['Body'].read().decode('utf-8'))

        # Check if thumbnail exists
        thumbnail_path = None
        try:
            s3.head_object(Bucket=s3_bucket, Key=thumbnail_key)
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as thumb_file:
                thumbnail_path = thumb_file.name
                print(f"Downloading thumbnail from S3: {s3_bucket}/{thumbnail_key}")
                s3.download_file(s3_bucket, thumbnail_key, thumbnail_path)
        except s3.exceptions.NoSuchKey:
            print("No thumbnail found, skipping")

        # Download transcript for captions
        caption_path = None
        if transcript_vtt_path:
            try:
                with tempfile.NamedTemporaryFile(suffix='.vtt', delete=False) as caption_file:
                    caption_path = caption_file.name
                    print(f"Downloading transcript from S3: {s3_bucket}/{transcript_vtt_path}")
                    s3.download_file(s3_bucket, transcript_vtt_path, caption_path)
            except Exception as e:
                print(f"Could not download transcript: {str(e)}")

        # Get YouTube API credentials from SSM
        youtube_creds_param = f"/youtube-uploader/{user_id}/youtube-api-credentials"
        print(f"Retrieving YouTube credentials from SSM: {youtube_creds_param}")
        youtube_creds_json = ssm.get_parameter(
            Name=youtube_creds_param,
            WithDecryption=True
        )['Parameter']['Value']
        youtube_creds = json.loads(youtube_creds_json)

        # Create YouTube API client
        credentials = Credentials.from_authorized_user_info(youtube_creds)
        youtube = build('youtube', 'v3', credentials=credentials)

        # Prepare video metadata
        video_metadata = {
            'snippet': {
                'title': metadata.get('title', 'Untitled Video'),
                'description': metadata.get('description', ''),
                'tags': metadata.get('tags', []),
                'categoryId': metadata.get('category_id', '22')  # Default: People & Blogs
            },
            'status': {
                'privacyStatus': metadata.get('privacy_status', 'private'),
                'selfDeclaredMadeForKids': False
            }
        }

        # Upload video
        print("Uploading video to YouTube...")
        media = MediaFileUpload(
            video_path,
            mimetype='video/mp4',
            resumable=True,
            chunksize=1024*1024  # 1MB chunks
        )

        request = youtube.videos().insert(
            part='snippet,status',
            body=video_metadata,
            media_body=media
        )

        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                progress = int(status.progress() * 100)
                print(f"Upload progress: {progress}%")

        youtube_video_id = response['id']
        youtube_video_url = f"https://www.youtube.com/watch?v={youtube_video_id}"
        print(f"Video uploaded successfully: {youtube_video_url}")

        # Upload thumbnail if available
        if thumbnail_path:
            try:
                print("Uploading thumbnail...")
                youtube.thumbnails().set(
                    videoId=youtube_video_id,
                    media_body=MediaFileUpload(thumbnail_path, mimetype='image/jpeg')
                ).execute()
                print("Thumbnail uploaded successfully")
            except HttpError as e:
                print(f"Error uploading thumbnail: {str(e)}")

        # Upload captions if available
        if caption_path:
            try:
                print("Uploading captions...")
                youtube.captions().insert(
                    part='snippet',
                    body={
                        'snippet': {
                            'videoId': youtube_video_id,
                            'language': 'en',
                            'name': 'English',
                            'isDraft': False
                        }
                    },
                    media_body=MediaFileUpload(caption_path, mimetype='text/vtt')
                ).execute()
                print("Captions uploaded successfully")
            except HttpError as e:
                print(f"Error uploading captions: {str(e)}")

        return {
            'statusCode': 200,
            'youtube_video_id': youtube_video_id,
            'youtube_video_url': youtube_video_url
        }

    except HttpError as e:
        print(f"YouTube API error: {str(e)}")
        raise
    except Exception as e:
        print(f"Error uploading to YouTube: {str(e)}")
        raise

    finally:
        # Clean up local temp files
        if 'video_path' in locals() and os.path.exists(video_path):
            os.remove(video_path)
        if thumbnail_path and os.path.exists(thumbnail_path):
            os.remove(thumbnail_path)
        if caption_path and os.path.exists(caption_path):
            os.remove(caption_path)
