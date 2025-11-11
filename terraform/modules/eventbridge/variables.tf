variable "project_name" {
  description = "Project name prefix"
  type        = string
}

variable "s3_bucket_name" {
  description = "Name of the S3 bucket to monitor"
  type        = string
}

variable "state_machine_arn" {
  description = "ARN of the Step Functions state machine to trigger"
  type        = string
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}
