"""
Lambda function to generate video transcripts using Amazon Bedrock
"""
import json
import os
import boto3
import tempfile
import subprocess
from typing import Dict, Any
import webvtt


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Generate transcript from video using Amazon Bedrock

    Args:
        event: Lambda event containing s3_bucket, s3_key, user_id, video_id, channel_id
        context: Lambda context

    Returns:
        Dictionary with transcript file paths
    """
    s3_bucket = event['s3_bucket']
    user_id = event['user_id']
    video_id = event['video_id']
    channel_id = event['channel_id']

    # Construct S3 paths
    video_prefix = f"{user_id}/{channel_id}/videos/{video_id}"
    video_key = f"{video_prefix}/video.mp4"  # Assuming video.mp4, adjust as needed

    print(f"Processing transcript for video: {video_key}")

    s3 = boto3.client('s3')
    bedrock_runtime = boto3.client('bedrock-runtime')

    try:
        # Download video file to temp directory
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as video_file:
            video_path = video_file.name
            print(f"Downloading video from S3: {s3_bucket}/{video_key}")
            s3.download_file(s3_bucket, video_key, video_path)

        # Extract audio from video using ffmpeg
        audio_path = video_path.replace('.mp4', '.mp3')
        print("Extracting audio from video")
        subprocess.run([
            'ffmpeg', '-i', video_path,
            '-vn', '-acodec', 'mp3',
            '-ar', '16000', '-ac', '1',
            audio_path
        ], check=True, capture_output=True)

        # Get video duration for timestamp generation
        duration_result = subprocess.run([
            'ffprobe', '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            video_path
        ], capture_output=True, text=True, check=True)
        video_duration = float(duration_result.stdout.strip())

        # Read audio file and convert to base64
        with open(audio_path, 'rb') as audio_file:
            audio_data = audio_file.read()

        # Call Amazon Bedrock to generate transcript
        # Note: This is a simplified example. Bedrock may require chunking for long audio
        model_id = os.environ.get('BEDROCK_MODEL_ID', 'anthropic.claude-3-5-sonnet-20241022-v2:0')

        prompt = """Please transcribe the following audio and provide timestamps for each segment.
        Format your response as a JSON array with objects containing 'start_time', 'end_time', and 'text' fields.
        Times should be in seconds with decimal precision.

        Example format:
        [
          {"start_time": 0.0, "end_time": 5.2, "text": "Hello and welcome to this video."},
          {"start_time": 5.2, "end_time": 10.5, "text": "Today we'll be discussing..."}
        ]
        """

        # Note: Bedrock doesn't directly support audio transcription with Claude
        # This is a placeholder - in production, you'd use Amazon Transcribe for audio transcription
        # and then use Bedrock for post-processing/enhancement

        # For now, using Amazon Transcribe instead
        transcribe = boto3.client('transcribe')

        # Upload audio to S3 for Transcribe
        audio_s3_key = f"{video_prefix}/temp_audio.mp3"
        s3.upload_file(audio_path, s3_bucket, audio_s3_key)

        # Start transcription job
        job_name = f"transcript-{video_id}"
        transcribe.start_transcription_job(
            TranscriptionJobName=job_name,
            Media={'MediaFileUri': f"s3://{s3_bucket}/{audio_s3_key}"},
            MediaFormat='mp3',
            LanguageCode='en-US',
            OutputBucketName=s3_bucket,
            OutputKey=f"{video_prefix}/transcribe-output.json",
            Settings={
                'ShowSpeakerLabels': False,
                'MaxSpeakerLabels': 2
            }
        )

        # Wait for transcription to complete
        print(f"Waiting for transcription job: {job_name}")
        waiter = transcribe.get_waiter('transcription_job_complete')
        waiter.wait(TranscriptionJobName=job_name)

        # Get transcription results
        job = transcribe.get_transcription_job(TranscriptionJobName=job_name)
        transcript_uri = job['TranscriptionJob']['Transcript']['TranscriptFileUri']

        # Download transcription results
        transcript_key = f"{video_prefix}/transcribe-output.json"
        transcript_obj = s3.get_object(Bucket=s3_bucket, Key=transcript_key)
        transcript_data = json.loads(transcript_obj['Body'].read().decode('utf-8'))

        # Convert to WebVTT and Markdown formats
        vtt_content = generate_webvtt(transcript_data)
        md_content = generate_markdown(transcript_data)

        # Upload transcript files to S3
        vtt_key = f"{video_prefix}/transcript.vtt"
        md_key = f"{video_prefix}/transcript.md"

        s3.put_object(Bucket=s3_bucket, Key=vtt_key, Body=vtt_content, ContentType='text/vtt')
        s3.put_object(Bucket=s3_bucket, Key=md_key, Body=md_content, ContentType='text/markdown')

        # Clean up temp audio file from S3
        s3.delete_object(Bucket=s3_bucket, Key=audio_s3_key)
        s3.delete_object(Bucket=s3_bucket, Key=transcript_key)

        # Clean up transcription job
        transcribe.delete_transcription_job(TranscriptionJobName=job_name)

        print(f"Transcript generated successfully: {vtt_key}, {md_key}")

        return {
            'statusCode': 200,
            'transcript_vtt_path': vtt_key,
            'transcript_md_path': md_key,
            'video_duration': video_duration
        }

    except Exception as e:
        print(f"Error generating transcript: {str(e)}")
        raise

    finally:
        # Clean up local temp files
        if 'video_path' in locals() and os.path.exists(video_path):
            os.remove(video_path)
        if 'audio_path' in locals() and os.path.exists(audio_path):
            os.remove(audio_path)


def generate_webvtt(transcript_data: Dict[str, Any]) -> str:
    """
    Generate WebVTT format from transcription data

    Args:
        transcript_data: Transcription data from Amazon Transcribe

    Returns:
        WebVTT formatted string
    """
    vtt_lines = ["WEBVTT", ""]

    items = transcript_data['results']['items']
    current_segment = []
    segment_start = None
    segment_end = None

    for item in items:
        if item['type'] == 'pronunciation':
            if not segment_start:
                segment_start = float(item['start_time'])
            segment_end = float(item['end_time'])
            current_segment.append(item['alternatives'][0]['content'])

            # Create a new segment every ~5 seconds or at punctuation
            if segment_end - segment_start >= 5.0 or len(current_segment) >= 20:
                vtt_lines.append(format_timestamp(segment_start) + " --> " + format_timestamp(segment_end))
                vtt_lines.append(" ".join(current_segment))
                vtt_lines.append("")
                current_segment = []
                segment_start = None
        elif item['type'] == 'punctuation' and current_segment:
            current_segment[-1] += item['alternatives'][0]['content']

    # Add remaining segment
    if current_segment and segment_start and segment_end:
        vtt_lines.append(format_timestamp(segment_start) + " --> " + format_timestamp(segment_end))
        vtt_lines.append(" ".join(current_segment))
        vtt_lines.append("")

    return "\n".join(vtt_lines)


def generate_markdown(transcript_data: Dict[str, Any]) -> str:
    """
    Generate Markdown format from transcription data

    Args:
        transcript_data: Transcription data from Amazon Transcribe

    Returns:
        Markdown formatted string
    """
    md_lines = ["# Video Transcript", ""]

    items = transcript_data['results']['items']
    current_paragraph = []
    paragraph_start = None

    for item in items:
        if item['type'] == 'pronunciation':
            if not paragraph_start:
                paragraph_start = float(item['start_time'])
            current_paragraph.append(item['alternatives'][0]['content'])
        elif item['type'] == 'punctuation':
            if current_paragraph:
                current_paragraph[-1] += item['alternatives'][0]['content']

            # End of sentence - create new paragraph
            if item['alternatives'][0]['content'] in ['.', '!', '?']:
                if current_paragraph:
                    timestamp = format_timestamp(paragraph_start)
                    md_lines.append(f"**[{timestamp}]** {' '.join(current_paragraph)}")
                    md_lines.append("")
                    current_paragraph = []
                    paragraph_start = None

    # Add remaining paragraph
    if current_paragraph and paragraph_start:
        timestamp = format_timestamp(paragraph_start)
        md_lines.append(f"**[{timestamp}]** {' '.join(current_paragraph)}")
        md_lines.append("")

    return "\n".join(md_lines)


def format_timestamp(seconds: float) -> str:
    """
    Format seconds as HH:MM:SS.mmm timestamp

    Args:
        seconds: Time in seconds

    Returns:
        Formatted timestamp string
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60

    return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"
