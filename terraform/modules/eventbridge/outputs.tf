output "event_rule_arn" {
  description = "ARN of the EventBridge rule"
  value       = aws_cloudwatch_event_rule.s3_upload.arn
}

output "event_rule_name" {
  description = "Name of the EventBridge rule"
  value       = aws_cloudwatch_event_rule.s3_upload.name
}
