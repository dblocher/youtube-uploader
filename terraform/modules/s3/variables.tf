variable "bucket_name" {
  description = "Name of the S3 bucket for video uploads"
  type        = string
}

variable "enable_lifecycle_policy" {
  description = "Enable lifecycle policy to automatically delete old videos"
  type        = bool
  default     = false
}

variable "lifecycle_expiration_days" {
  description = "Number of days after which to expire objects"
  type        = number
  default     = 365
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}
