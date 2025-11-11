# YouTube Uploader

A comprehensive CLI tool and AWS infrastructure for uploading videos to YouTube with automated transcript generation and GitHub synchronization.

## Architecture Overview

This project consists of three main components:

1. **CLI Tool** - Command-line interface for uploading videos
2. **AWS Infrastructure** - Terraform-managed cloud resources
3. **Lambda Functions** - Serverless processing pipeline

### Workflow

1. User uploads video via CLI → S3
2. S3 upload triggers EventBridge → Step Functions
3. Step Functions orchestrates three Lambda functions:
   - **transcript-generator**: Generates video transcript using Amazon Transcribe
   - **video-uploader**: Uploads video to YouTube with metadata
   - **github-sync**: Commits transcripts to GitHub repository
4. DynamoDB tracks processing state

## Prerequisites

- AWS Account with appropriate permissions
- AWS CLI configured with SSO
- Terraform >= 1.0
- Python >= 3.9
- **ffmpeg** (for local audio extraction - highly recommended)
- Docker (for building Lambda container images)
- YouTube Data API credentials
- GitHub Personal Access Token

### Installing ffmpeg

**macOS:**
```bash
brew install ffmpeg
```

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install ffmpeg
```

**Windows:**
Download from [ffmpeg.org](https://ffmpeg.org/download.html) and add to PATH

**Note:** While ffmpeg is optional, installing it locally provides:
- **50x faster** transcript processing (downloads audio only, not full video)
- **Lower AWS costs** (reduced Lambda execution time)
- **Better reliability** (less likely to hit Lambda timeout)
- **Immediate feedback** if audio extraction fails

## Quick Start

### 1. Configure AWS SSO

If you haven't already configured AWS SSO:

```bash
aws configure sso
```

Follow the prompts to set up your SSO profile. Make note of the profile name (e.g., `default`, `my-profile`).

To use your SSO profile:

```bash
aws sso login --profile YOUR_PROFILE_NAME
```

For more information on AWS SSO configuration, see the [AWS SSO documentation](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-sso.html).

### 2. Deploy Infrastructure

```bash
cd terraform

# Copy and edit the example tfvars file
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your configuration

# Initialize Terraform
terraform init

# Review the plan
terraform plan

# Deploy infrastructure
terraform apply
```

### 3. Configure Secrets in AWS SSM

After deploying infrastructure, configure the required secrets:

```bash
# YouTube API Credentials (OAuth 2.0 JSON)
aws ssm put-parameter \
  --name "/youtube-uploader/default/youtube-api-credentials" \
  --value '{"token": "YOUR_TOKEN", "refresh_token": "YOUR_REFRESH_TOKEN", "client_id": "YOUR_CLIENT_ID", "client_secret": "YOUR_CLIENT_SECRET"}' \
  --type SecureString \
  --overwrite

# YouTube Channel ID
aws ssm put-parameter \
  --name "/youtube-uploader/default/youtube-channel-id" \
  --value "YOUR_CHANNEL_ID" \
  --type String \
  --overwrite

# GitHub Personal Access Token
aws ssm put-parameter \
  --name "/youtube-uploader/default/github-token" \
  --value "YOUR_GITHUB_TOKEN" \
  --type SecureString \
  --overwrite

# GitHub Repository (format: owner/repo)
aws ssm put-parameter \
  --name "/youtube-uploader/default/github-repo" \
  --value "your-username/your-repo" \
  --type String \
  --overwrite
```

### 4. Build and Deploy Lambda Container Images

For the `video-uploader` Lambda function (uses YouTube API):

```bash
cd lambdas/video_uploader

# Get AWS account ID and region
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
AWS_REGION="us-east-1"  # or your preferred region

# Create ECR repository
aws ecr create-repository --repository-name youtube-uploader-video-uploader

# Build and push Docker image
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

docker build -t youtube-uploader-video-uploader .
docker tag youtube-uploader-video-uploader:latest $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/youtube-uploader-video-uploader:latest
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/youtube-uploader-video-uploader:latest
```

Update your `terraform.tfvars` with the ECR image URI and re-apply:

```hcl
ecr_image_uris = {
  video_uploader = "123456789012.dkr.ecr.us-east-1.amazonaws.com/youtube-uploader-video-uploader:latest"
}
```

Then run `terraform apply` again.

### 5. Install CLI Tool

```bash
cd cli
pip install -e .
```

### 6. Initialize CLI Configuration

```bash
youtube-uploader init
```

Follow the prompts to configure:
- AWS CLI profile name
- AWS region
- S3 bucket name
- User ID
- YouTube channel ID
- GitHub repository (optional)

### 7. Upload Your First Video

```bash
youtube-uploader upload path/to/video.mp4 --thumbnail path/to/thumbnail.jpg
```

The CLI will:
1. Prompt for video metadata (title, description, privacy status, tags, category)
2. Upload files to S3
3. Trigger the automated processing workflow

## Project Structure

```
youtube-uploader/
├── cli/                          # CLI tool
│   ├── youtube_uploader/
│   │   ├── cli.py               # Main CLI entry point
│   │   ├── config.py            # Configuration management
│   │   ├── metadata.py          # Metadata collection
│   │   └── s3_client.py         # S3 upload logic
│   ├── requirements.txt
│   └── setup.py
├── terraform/                    # Infrastructure as Code
│   ├── modules/
│   │   ├── dynamodb/            # DynamoDB table
│   │   ├── s3/                  # S3 bucket
│   │   ├── lambda/              # Lambda functions
│   │   ├── step-functions/      # Step Functions workflow
│   │   ├── secrets/             # SSM parameters
│   │   └── eventbridge/         # EventBridge rules
│   ├── main.tf
│   ├── variables.tf
│   └── outputs.tf
├── lambdas/
│   ├── transcript_generator/    # Transcript generation
│   ├── video_uploader/          # YouTube upload
│   └── github_sync/             # GitHub synchronization
└── README.md
```

## S3 Bucket Structure

```
s3://your-bucket/
└── {user_id}/
    └── {channel_id}/
        └── videos/
            └── {video_id}/
                ├── video.mp4
                ├── audio.mp3           # Pre-extracted audio (if ffmpeg available)
                ├── metadata.json
                ├── thumbnail.jpg       # Optional
                ├── transcript.vtt      # Generated by Lambda
                └── transcript.md       # Generated by Lambda
```

## DynamoDB Schema

Table: `youtube-uploader-state`

- **Partition Key**: `user_id` (String)
- **Sort Key**: `video_id` (String)
- **Attributes**:
  - `upload_status`: processing | completed | failed
  - `channel_id`: Channel ID
  - `s3_path`: S3 path to video
  - `youtube_video_id`: YouTube video ID
  - `github_commit_sha`: GitHub commit SHA
  - `processing_started`: Timestamp
  - `processing_completed`: Timestamp
  - `error_message`: Error details (if failed)

## CLI Commands

### `init`
Initialize CLI configuration

```bash
youtube-uploader init
```

### `upload`
Upload a video to YouTube

```bash
youtube-uploader upload VIDEO_FILE [--thumbnail THUMBNAIL_FILE]
```

### `config`
Display current configuration

```bash
youtube-uploader config
```

### `reset`
Reset CLI configuration

```bash
youtube-uploader reset
```

## Multi-Tenant Support

The infrastructure supports multiple users/tenants:

1. Each user has a unique `user_id`
2. S3 paths are organized by user: `{user_id}/{channel_id}/videos/{video_id}/`
3. SSM parameters are namespaced: `/youtube-uploader/{user_id}/...`
4. DynamoDB uses `user_id` as partition key for isolation

To add a new user:

1. Update `terraform.tfvars` with the new user ID in the `user_ids` list
2. Run `terraform apply` to create SSM parameter placeholders
3. Configure secrets for the new user (step 3 above)
4. User runs `youtube-uploader init` with their user ID

## Monitoring

### Step Functions Console
Monitor workflow executions: AWS Console → Step Functions → State machines → youtube-uploader-video-processing

### DynamoDB Console
Check processing status: AWS Console → DynamoDB → Tables → youtube-uploader-state

### CloudWatch Logs
View Lambda logs: AWS Console → CloudWatch → Log groups

## Troubleshooting

### Upload fails with "Access Denied"
- Verify AWS credentials: `aws sts get-caller-identity --profile YOUR_PROFILE`
- Check S3 bucket permissions
- Ensure IAM roles have correct policies

### Transcript generation fails
- Check Lambda timeout (15 minutes default)
- Verify Amazon Transcribe service is available in your region
- Check CloudWatch logs for detailed errors

### YouTube upload fails
- Verify YouTube API credentials in SSM
- Check YouTube API quotas
- Ensure video file meets YouTube requirements

### GitHub sync fails
- Verify GitHub token has `repo` scope
- Check repository exists and token has write access
- Verify repository name format: `owner/repo`

## Future Enhancements

- Video editing based on transcript changes (planned)
- Batch upload support
- Video analytics dashboard
- Automated tagging and categorization using AI
- Support for multiple video formats
- Progress tracking in CLI

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.

## License

MIT License
