output "bucket_name" {
  description = "Name of the S3 bucket"
  value       = aws_s3_bucket.video_uploads.id
}

output "bucket_arn" {
  description = "ARN of the S3 bucket"
  value       = aws_s3_bucket.video_uploads.arn
}

output "bucket_domain_name" {
  description = "Domain name of the S3 bucket"
  value       = aws_s3_bucket.video_uploads.bucket_domain_name
}
