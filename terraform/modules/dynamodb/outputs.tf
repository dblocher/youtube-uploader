output "table_name" {
  description = "Name of the DynamoDB table"
  value       = aws_dynamodb_table.youtube_uploader_state.name
}

output "table_arn" {
  description = "ARN of the DynamoDB table"
  value       = aws_dynamodb_table.youtube_uploader_state.arn
}
