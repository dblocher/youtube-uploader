resource "aws_dynamodb_table" "youtube_uploader_state" {
  name           = var.table_name
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "user_id"
  range_key      = "video_id"

  attribute {
    name = "user_id"
    type = "S"
  }

  attribute {
    name = "video_id"
    type = "S"
  }

  attribute {
    name = "upload_status"
    type = "S"
  }

  attribute {
    name = "channel_id"
    type = "S"
  }

  # GSI for querying by status
  global_secondary_index {
    name            = "StatusIndex"
    hash_key        = "upload_status"
    range_key       = "video_id"
    projection_type = "ALL"
  }

  # GSI for querying by channel
  global_secondary_index {
    name            = "ChannelIndex"
    hash_key        = "channel_id"
    range_key       = "video_id"
    projection_type = "ALL"
  }

  point_in_time_recovery {
    enabled = true
  }

  tags = var.tags
}
