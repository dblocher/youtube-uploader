variable "project_name" {
  description = "Project name prefix"
  type        = string
}

variable "lambda_functions" {
  description = "Map of Lambda function configurations"
  type = map(object({
    timeout                = number
    memory_size            = number
    use_container_image    = bool
    environment_variables  = map(string)
  }))
}

variable "s3_bucket_name" {
  description = "Name of the S3 bucket"
  type        = string
}

variable "s3_bucket_arn" {
  description = "ARN of the S3 bucket"
  type        = string
}

variable "dynamodb_table_name" {
  description = "Name of the DynamoDB table"
  type        = string
}

variable "dynamodb_table_arn" {
  description = "ARN of the DynamoDB table"
  type        = string
}

variable "aws_region" {
  description = "AWS region"
  type        = string
}

variable "aws_account_id" {
  description = "AWS account ID"
  type        = string
}

variable "ecr_image_uris" {
  description = "Map of ECR image URIs for container-based Lambda functions"
  type        = map(string)
  default     = {}
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}
