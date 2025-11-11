"""
S3 client for uploading files
"""
import boto3
import os
from pathlib import Path
from typing import Optional
from botocore.exceptions import ClientError, NoCredentialsError
from rich.progress import (
    Progress,
    BarColumn,
    DownloadColumn,
    TransferSpeedColumn,
    TimeRemainingColumn,
    TextColumn
)


class S3Uploader:
    """Handle S3 uploads with progress tracking"""

    def __init__(self, bucket_name: str, profile_name: Optional[str] = None, region: str = "us-east-1"):
        """
        Initialize S3 uploader

        Args:
            bucket_name: Name of the S3 bucket
            profile_name: AWS CLI profile name
            region: AWS region
        """
        self.bucket_name = bucket_name

        # Create boto3 session with profile if provided
        session_kwargs = {'region_name': region}
        if profile_name:
            session_kwargs['profile_name'] = profile_name

        session = boto3.Session(**session_kwargs)
        self.s3_client = session.client('s3')

    def validate_credentials(self) -> bool:
        """
        Validate AWS credentials

        Returns:
            True if credentials are valid, False otherwise
        """
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            return True
        except NoCredentialsError:
            return False
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                raise ValueError(f"S3 bucket '{self.bucket_name}' does not exist")
            elif error_code == '403':
                raise ValueError(f"Access denied to S3 bucket '{self.bucket_name}'")
            else:
                raise

    def upload_file(
        self,
        file_path: Path,
        s3_key: str,
        content_type: Optional[str] = None,
        show_progress: bool = True
    ) -> str:
        """
        Upload a file to S3 with progress tracking

        Args:
            file_path: Local file path
            s3_key: S3 object key
            content_type: Content type for the uploaded file
            show_progress: Whether to show progress bar

        Returns:
            S3 URI of the uploaded file
        """
        file_size = os.path.getsize(file_path)

        extra_args = {}
        if content_type:
            extra_args['ContentType'] = content_type

        if show_progress and file_size > 1024 * 1024:  # Show progress for files > 1MB
            with Progress(
                TextColumn("[bold blue]{task.description}"),
                BarColumn(),
                DownloadColumn(),
                TransferSpeedColumn(),
                TimeRemainingColumn(),
            ) as progress:
                task = progress.add_task(
                    f"Uploading {file_path.name}",
                    total=file_size
                )

                def upload_progress(bytes_transferred):
                    progress.update(task, completed=bytes_transferred)

                self.s3_client.upload_file(
                    str(file_path),
                    self.bucket_name,
                    s3_key,
                    ExtraArgs=extra_args,
                    Callback=upload_progress
                )
        else:
            self.s3_client.upload_file(
                str(file_path),
                self.bucket_name,
                s3_key,
                ExtraArgs=extra_args
            )

        return f"s3://{self.bucket_name}/{s3_key}"

    def upload_video_package(
        self,
        user_id: str,
        channel_id: str,
        video_id: str,
        video_path: Path,
        metadata: dict,
        thumbnail_path: Optional[Path] = None,
        audio_path: Optional[Path] = None
    ) -> dict:
        """
        Upload complete video package (video, audio, metadata, optional thumbnail)

        Args:
            user_id: User ID
            channel_id: Channel ID
            video_id: Video ID
            video_path: Path to video file
            metadata: Video metadata dictionary
            thumbnail_path: Optional path to thumbnail
            audio_path: Optional path to extracted audio file

        Returns:
            Dictionary with S3 URIs of uploaded files
        """
        import json

        base_path = f"{user_id}/{channel_id}/videos/{video_id}"
        uploaded_files = {}

        # Upload video file
        video_key = f"{base_path}/video.mp4"
        print(f"\nUploading video to S3...")
        uploaded_files['video'] = self.upload_file(
            video_path,
            video_key,
            content_type='video/mp4',
            show_progress=True
        )

        # Upload audio file if provided
        if audio_path:
            audio_key = f"{base_path}/audio.mp3"
            print(f"\nUploading audio to S3...")
            uploaded_files['audio'] = self.upload_file(
                audio_path,
                audio_key,
                content_type='audio/mpeg',
                show_progress=False
            )

        # Upload thumbnail if provided
        if thumbnail_path:
            thumbnail_key = f"{base_path}/thumbnail.jpg"
            print(f"\nUploading thumbnail to S3...")
            uploaded_files['thumbnail'] = self.upload_file(
                thumbnail_path,
                thumbnail_key,
                content_type='image/jpeg',
                show_progress=False
            )

        # Upload metadata (this triggers the Step Functions workflow)
        metadata_key = f"{base_path}/metadata.json"
        metadata_json = json.dumps(metadata, indent=2)

        print(f"\nUploading metadata to S3...")
        self.s3_client.put_object(
            Bucket=self.bucket_name,
            Key=metadata_key,
            Body=metadata_json.encode('utf-8'),
            ContentType='application/json'
        )
        uploaded_files['metadata'] = f"s3://{self.bucket_name}/{metadata_key}"

        return uploaded_files
