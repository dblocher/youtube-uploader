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

# Lifecycle policy with Intelligent-Tiering
resource "aws_s3_bucket_lifecycle_configuration" "video_uploads" {
  bucket = aws_s3_bucket.video_uploads.id

  # Intelligent-Tiering for video files
  rule {
    id     = "intelligent-tiering-videos"
    status = "Enabled"

    filter {
      prefix = "*/videos/"
    }

    transition {
      days          = 0
      storage_class = "INTELLIGENT_TIERING"
    }

    noncurrent_version_transition {
      noncurrent_days = 30
      storage_class   = "GLACIER_IR"
    }

    noncurrent_version_expiration {
      noncurrent_days = 90
    }
  }

  # Optional: Archive old videos to Glacier Deep Archive
  dynamic "rule" {
    for_each = var.enable_deep_archive ? [1] : []
    content {
      id     = "archive-old-videos"
      status = "Enabled"

      filter {
        prefix = "*/videos/"
      }

      transition {
        days          = var.deep_archive_days
        storage_class = "DEEP_ARCHIVE"
      }
    }
  }
}
