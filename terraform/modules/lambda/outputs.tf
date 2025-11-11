output "lambda_function_arns" {
  description = "Map of Lambda function ARNs"
  value = {
    for k, v in aws_lambda_function.functions :
    k => v.arn
  }
}

output "lambda_function_names" {
  description = "Map of Lambda function names"
  value = {
    for k, v in aws_lambda_function.functions :
    k => v.function_name
  }
}

output "lambda_role_arns" {
  description = "Map of Lambda IAM role ARNs"
  value = {
    for k, v in aws_iam_role.lambda_role :
    k => v.arn
  }
}
