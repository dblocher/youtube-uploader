variable "user_ids" {
  description = "List of user IDs to create SSM parameters for"
  type        = list(string)
  default     = ["default"]
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}
