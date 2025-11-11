output "youtube_api_credentials_parameter_names" {
  description = "Map of user IDs to YouTube API credentials parameter names"
  value = {
    for user_id in var.user_ids :
    user_id => aws_ssm_parameter.youtube_api_credentials_placeholder[user_id].name
  }
}

output "github_token_parameter_names" {
  description = "Map of user IDs to GitHub token parameter names"
  value = {
    for user_id in var.user_ids :
    user_id => aws_ssm_parameter.github_token_placeholder[user_id].name
  }
}
