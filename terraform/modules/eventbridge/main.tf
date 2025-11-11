# EventBridge rule to trigger Step Functions on S3 upload
resource "aws_cloudwatch_event_rule" "s3_upload" {
  name        = "${var.project_name}-s3-upload-trigger"
  description = "Trigger Step Functions workflow when video is uploaded to S3"

  event_pattern = jsonencode({
    source      = ["aws.s3"]
    detail-type = ["Object Created"]
    detail = {
      bucket = {
        name = [var.s3_bucket_name]
      }
      object = {
        key = [
          {
            suffix = "metadata.json"
          }
        ]
      }
    }
  })

  tags = var.tags
}

# IAM role for EventBridge to invoke Step Functions
resource "aws_iam_role" "eventbridge_role" {
  name = "${var.project_name}-eventbridge-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "events.amazonaws.com"
        }
      }
    ]
  })

  tags = var.tags
}

# Policy for EventBridge to start Step Functions execution
resource "aws_iam_role_policy" "eventbridge_policy" {
  name = "${var.project_name}-eventbridge-policy"
  role = aws_iam_role.eventbridge_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "states:StartExecution"
        ]
        Resource = var.state_machine_arn
      }
    ]
  })
}

# EventBridge target - Step Functions state machine
resource "aws_cloudwatch_event_target" "step_functions" {
  rule      = aws_cloudwatch_event_rule.s3_upload.name
  target_id = "StepFunctionsTarget"
  arn       = var.state_machine_arn
  role_arn  = aws_iam_role.eventbridge_role.arn

  # Transform S3 event to extract user_id, channel_id, video_id from S3 key
  input_transformer {
    input_paths = {
      bucket = "$.detail.bucket.name"
      key    = "$.detail.object.key"
    }

    input_template = <<EOF
{
  "detail": {
    "bucket": {
      "name": <bucket>
    },
    "object": {
      "key": <key>,
      "key_parts": {
        "user_id": "$.match($.detail.object.key, '^([^/]+)/')[1]",
        "channel_id": "$.match($.detail.object.key, '^[^/]+/([^/]+)/')[1]",
        "video_id": "$.match($.detail.object.key, 'videos/([^/]+)/')[1]"
      }
    }
  }
}
EOF
  }
}
