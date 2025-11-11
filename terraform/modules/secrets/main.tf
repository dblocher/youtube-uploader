resource "aws_ssm_parameter" "youtube_api_credentials_placeholder" {
  for_each = toset(var.user_ids)

  name        = "/youtube-uploader/${each.key}/youtube-api-credentials"
  description = "YouTube API credentials for user ${each.key}"
  type        = "SecureString"
  value       = "PLACEHOLDER_UPDATE_ME"

  lifecycle {
    ignore_changes = [value]
  }

  tags = merge(
    var.tags,
    {
      User = each.key
    }
  )
}

resource "aws_ssm_parameter" "youtube_channel_id_placeholder" {
  for_each = toset(var.user_ids)

  name        = "/youtube-uploader/${each.key}/youtube-channel-id"
  description = "YouTube channel ID for user ${each.key}"
  type        = "String"
  value       = "PLACEHOLDER_UPDATE_ME"

  lifecycle {
    ignore_changes = [value]
  }

  tags = merge(
    var.tags,
    {
      User = each.key
    }
  )
}

resource "aws_ssm_parameter" "github_token_placeholder" {
  for_each = toset(var.user_ids)

  name        = "/youtube-uploader/${each.key}/github-token"
  description = "GitHub personal access token for user ${each.key}"
  type        = "SecureString"
  value       = "PLACEHOLDER_UPDATE_ME"

  lifecycle {
    ignore_changes = [value]
  }

  tags = merge(
    var.tags,
    {
      User = each.key
    }
  )
}

resource "aws_ssm_parameter" "github_repo_placeholder" {
  for_each = toset(var.user_ids)

  name        = "/youtube-uploader/${each.key}/github-repo"
  description = "GitHub repository for transcripts (format: owner/repo)"
  type        = "String"
  value       = "PLACEHOLDER_UPDATE_ME"

  lifecycle {
    ignore_changes = [value]
  }

  tags = merge(
    var.tags,
    {
      User = each.key
    }
  )
}
