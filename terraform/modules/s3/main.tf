resource "aws_s3_bucket" "video_uploads" {
  bucket = var.bucket_name

  tags = var.tags
}

resource "aws_s3_bucket_versioning" "video_uploads" {
  bucket = aws_s3_bucket.video_uploads.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "video_uploads" {
  bucket = aws_s3_bucket.video_uploads.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "video_uploads" {
  bucket = aws_s3_bucket.video_uploads.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# EventBridge notifications
resource "aws_s3_bucket_notification" "video_uploads" {
  bucket      = aws_s3_bucket.video_uploads.id
  eventbridge = true
}

# Optional: Lifecycle policy for old videos
resource "aws_s3_bucket_lifecycle_configuration" "video_uploads" {
  count  = var.enable_lifecycle_policy ? 1 : 0
  bucket = aws_s3_bucket.video_uploads.id

  rule {
    id     = "delete-old-videos"
    status = "Enabled"

    filter {
      prefix = "*/videos/"
    }

    expiration {
      days = var.lifecycle_expiration_days
    }

    noncurrent_version_expiration {
      noncurrent_days = 30
    }
  }
}
