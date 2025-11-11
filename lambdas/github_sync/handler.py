"""
Lambda function to sync transcripts to GitHub
"""
import json
import os
import boto3
import tempfile
from typing import Dict, Any
from github import Github, GithubException


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Sync video transcripts to GitHub repository

    Args:
        event: Lambda event containing s3_bucket, user_id, video_id, channel_id,
               transcript paths, youtube_video_id
        context: Lambda context

    Returns:
        Dictionary with commit SHA and repository URL
    """
    s3_bucket = event['s3_bucket']
    user_id = event['user_id']
    video_id = event['video_id']
    channel_id = event['channel_id']
    transcript_vtt_path = event.get('transcript_vtt')
    transcript_md_path = event.get('transcript_md')
    youtube_video_id = event.get('youtube_video_id')

    print(f"Syncing transcripts to GitHub for video: {video_id}")

    s3 = boto3.client('s3')
    ssm = boto3.client('ssm')

    try:
        # Download transcript files from S3
        vtt_content = None
        md_content = None

        if transcript_vtt_path:
            print(f"Downloading VTT transcript: {transcript_vtt_path}")
            vtt_obj = s3.get_object(Bucket=s3_bucket, Key=transcript_vtt_path)
            vtt_content = vtt_obj['Body'].read().decode('utf-8')

        if transcript_md_path:
            print(f"Downloading Markdown transcript: {transcript_md_path}")
            md_obj = s3.get_object(Bucket=s3_bucket, Key=transcript_md_path)
            md_content = md_obj['Body'].read().decode('utf-8')

        # Get GitHub credentials from SSM
        github_token_param = f"/youtube-uploader/{user_id}/github-token"
        github_repo_param = f"/youtube-uploader/{user_id}/github-repo"

        print(f"Retrieving GitHub credentials from SSM")
        github_token = ssm.get_parameter(
            Name=github_token_param,
            WithDecryption=True
        )['Parameter']['Value']

        github_repo = ssm.get_parameter(
            Name=github_repo_param,
            WithDecryption=False
        )['Parameter']['Value']

        # Initialize GitHub client
        g = Github(github_token)
        repo = g.get_repo(github_repo)

        # Prepare file paths in GitHub
        github_base_path = f"{user_id}/{channel_id}/{video_id}"
        vtt_github_path = f"{github_base_path}/transcript.vtt"
        md_github_path = f"{github_base_path}/transcript.md"
        metadata_github_path = f"{github_base_path}/metadata.json"

        # Create metadata for GitHub
        github_metadata = {
            "video_id": video_id,
            "channel_id": channel_id,
            "user_id": user_id,
            "youtube_video_id": youtube_video_id,
            "youtube_url": f"https://www.youtube.com/watch?v={youtube_video_id}" if youtube_video_id else None,
            "transcript_vtt": vtt_github_path,
            "transcript_md": md_github_path
        }

        # Commit message
        commit_message = f"Add transcript for video {video_id}\n\nYouTube Video ID: {youtube_video_id}"

        # Check if files already exist and update or create
        files_to_commit = []

        if vtt_content:
            files_to_commit.append({
                'path': vtt_github_path,
                'content': vtt_content
            })

        if md_content:
            files_to_commit.append({
                'path': md_github_path,
                'content': md_content
            })

        files_to_commit.append({
            'path': metadata_github_path,
            'content': json.dumps(github_metadata, indent=2)
        })

        # Get default branch
        default_branch = repo.default_branch
        branch_ref = repo.get_git_ref(f"heads/{default_branch}")
        base_commit = repo.get_git_commit(branch_ref.object.sha)

        # Create blobs for each file
        blobs = []
        for file_info in files_to_commit:
            blob = repo.create_git_blob(file_info['content'], "utf-8")
            blobs.append({
                'path': file_info['path'],
                'mode': '100644',
                'type': 'blob',
                'sha': blob.sha
            })

        # Get base tree
        base_tree = base_commit.tree

        # Create new tree
        new_tree = repo.create_git_tree(blobs, base_tree)

        # Create commit
        new_commit = repo.create_git_commit(
            message=commit_message,
            tree=new_tree,
            parents=[base_commit]
        )

        # Update reference
        branch_ref.edit(new_commit.sha)

        commit_sha = new_commit.sha
        commit_url = f"https://github.com/{github_repo}/commit/{commit_sha}"

        print(f"Successfully synced to GitHub: {commit_url}")

        return {
            'statusCode': 200,
            'commit_sha': commit_sha,
            'commit_url': commit_url,
            'repository': github_repo
        }

    except GithubException as e:
        print(f"GitHub API error: {str(e)}")
        raise
    except Exception as e:
        print(f"Error syncing to GitHub: {str(e)}")
        raise
