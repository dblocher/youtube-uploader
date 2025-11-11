# YouTube Uploader CLI

Command-line interface for uploading videos to YouTube via AWS infrastructure.

## Installation

```bash
cd cli
pip install -e .
```

## Usage

### Initialize Configuration

```bash
youtube-uploader init
```

This will prompt you for:
- AWS CLI profile name
- AWS region
- S3 bucket name
- User ID
- YouTube channel ID
- GitHub repository (optional)

### Upload a Video

```bash
youtube-uploader upload VIDEO_FILE [--thumbnail THUMBNAIL_FILE]
```

This will:
1. Prompt you for video metadata (title, description, privacy status, tags, category)
2. Upload the video file and metadata to S3
3. Trigger the AWS Step Functions workflow for processing

### View Configuration

```bash
youtube-uploader config
```

### Reset Configuration

```bash
youtube-uploader reset
```

## Configuration File

Configuration is stored in `~/.youtube-uploader/config.json`
