variable "project_name" {
  description = "Project name prefix"
  type        = string
}

variable "lambda_function_arns" {
  description = "Map of Lambda function ARNs"
  type        = map(string)
}

variable "dynamodb_table_name" {
  description = "Name of the DynamoDB table"
  type        = string
}

variable "dynamodb_table_arn" {
  description = "ARN of the DynamoDB table"
  type        = string
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}
