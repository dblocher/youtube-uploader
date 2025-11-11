variable "bucket_name" {
  description = "Name of the S3 bucket for video uploads"
  type        = string
}

variable "enable_deep_archive" {
  description = "Enable deep archive transition for long-term storage"
  type        = bool
  default     = false
}

variable "deep_archive_days" {
  description = "Number of days after which to move objects to Deep Archive"
  type        = number
  default     = 180
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}
