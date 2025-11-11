output "s3_bucket_name" {
  description = "Name of the S3 bucket for video uploads"
  value       = module.s3.bucket_name
}

output "dynamodb_table_name" {
  description = "Name of the DynamoDB table"
  value       = module.dynamodb.table_name
}

output "lambda_function_names" {
  description = "Names of the Lambda functions"
  value       = module.lambda.lambda_function_names
}

output "step_functions_state_machine_arn" {
  description = "ARN of the Step Functions state machine"
  value       = module.step_functions.state_machine_arn
}

output "ssm_parameter_instructions" {
  description = "Instructions for updating SSM parameters"
  value       = <<-EOT
    Please update the following SSM parameters with your actual values:

    For each user_id in ${jsonencode(var.user_ids)}:
    - /youtube-uploader/{user_id}/youtube-api-credentials
    - /youtube-uploader/{user_id}/youtube-channel-id
    - /youtube-uploader/{user_id}/github-token
    - /youtube-uploader/{user_id}/github-repo

    Use the AWS CLI or AWS Console to update these parameters.
  EOT
}
