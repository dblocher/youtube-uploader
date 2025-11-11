variable "aws_region" {
  description = "AWS region to deploy resources"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project name prefix for all resources"
  type        = string
  default     = "youtube-uploader"
}

variable "s3_bucket_name" {
  description = "Name of the S3 bucket for video uploads (must be globally unique)"
  type        = string
}

variable "dynamodb_table_name" {
  description = "Name of the DynamoDB table"
  type        = string
  default     = "youtube-uploader-state"
}

variable "user_ids" {
  description = "List of user IDs to create SSM parameters for"
  type        = list(string)
  default     = ["default"]
}

variable "enable_lifecycle_policy" {
  description = "Enable S3 lifecycle policy to automatically delete old videos"
  type        = bool
  default     = false
}

variable "lifecycle_expiration_days" {
  description = "Number of days after which to expire S3 objects"
  type        = number
  default     = 365
}

variable "ecr_image_uris" {
  description = "Map of ECR image URIs for container-based Lambda functions"
  type        = map(string)
  default     = {}
}

variable "tags" {
  description = "Additional tags to apply to all resources"
  type        = map(string)
  default     = {}
}
