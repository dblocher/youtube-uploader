# IAM role for Step Functions
resource "aws_iam_role" "step_functions_role" {
  name = "${var.project_name}-step-functions-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "states.amazonaws.com"
        }
      }
    ]
  })

  tags = var.tags
}

# Policy for Step Functions to invoke Lambda
resource "aws_iam_role_policy" "step_functions_policy" {
  name = "${var.project_name}-step-functions-policy"
  role = aws_iam_role.step_functions_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "lambda:InvokeFunction"
        ]
        Resource = [
          for arn in var.lambda_function_arns : arn
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "dynamodb:PutItem",
          "dynamodb:UpdateItem"
        ]
        Resource = var.dynamodb_table_arn
      }
    ]
  })
}

# Step Functions state machine
resource "aws_sfn_state_machine" "video_processing" {
  name     = "${var.project_name}-video-processing"
  role_arn = aws_iam_role.step_functions_role.arn

  definition = jsonencode({
    Comment = "YouTube video upload workflow"
    StartAt = "UpdateStatusProcessing"
    States = {
      UpdateStatusProcessing = {
        Type = "Task"
        Resource = "arn:aws:states:::dynamodb:updateItem"
        Parameters = {
          TableName = var.dynamodb_table_name
          Key = {
            user_id = {
              "S.$" = "$.detail.object.key.user_id"
            }
            video_id = {
              "S.$" = "$.detail.object.key.video_id"
            }
          }
          UpdateExpression = "SET upload_status = :status, processing_started = :timestamp"
          ExpressionAttributeValues = {
            ":status" = {
              S = "processing"
            }
            ":timestamp" = {
              "S.$" = "$$.State.EnteredTime"
            }
          }
        }
        Next = "GenerateTranscript"
        Catch = [
          {
            ErrorEquals = ["States.ALL"]
            Next         = "UpdateStatusFailed"
            ResultPath   = "$.error"
          }
        ]
      }

      GenerateTranscript = {
        Type     = "Task"
        Resource = "arn:aws:states:::lambda:invoke"
        Parameters = {
          FunctionName = var.lambda_function_arns["transcript_generator"]
          Payload = {
            "s3_bucket.$"  = "$.detail.bucket.name"
            "s3_key.$"     = "$.detail.object.key"
            "user_id.$"    = "$.detail.object.key.user_id"
            "video_id.$"   = "$.detail.object.key.video_id"
            "channel_id.$" = "$.detail.object.key.channel_id"
          }
        }
        ResultPath = "$.transcriptResult"
        Next       = "UploadToYouTube"
        Retry = [
          {
            ErrorEquals     = ["States.TaskFailed", "Lambda.ServiceException", "Lambda.TooManyRequestsException"]
            IntervalSeconds = 2
            MaxAttempts     = 3
            BackoffRate     = 2.0
          }
        ]
        Catch = [
          {
            ErrorEquals = ["States.ALL"]
            Next         = "UpdateStatusFailed"
            ResultPath   = "$.error"
          }
        ]
      }

      UploadToYouTube = {
        Type     = "Task"
        Resource = "arn:aws:states:::lambda:invoke"
        Parameters = {
          FunctionName = var.lambda_function_arns["video_uploader"]
          Payload = {
            "s3_bucket.$"       = "$.detail.bucket.name"
            "s3_key.$"          = "$.detail.object.key"
            "user_id.$"         = "$.detail.object.key.user_id"
            "video_id.$"        = "$.detail.object.key.video_id"
            "channel_id.$"      = "$.detail.object.key.channel_id"
            "transcript_vtt.$"  = "$.transcriptResult.Payload.transcript_vtt_path"
            "transcript_md.$"   = "$.transcriptResult.Payload.transcript_md_path"
          }
        }
        ResultPath = "$.youtubeResult"
        Next       = "SyncToGitHub"
        Retry = [
          {
            ErrorEquals     = ["States.TaskFailed"]
            IntervalSeconds = 5
            MaxAttempts     = 2
            BackoffRate     = 2.0
          }
        ]
        Catch = [
          {
            ErrorEquals = ["States.ALL"]
            Next         = "UpdateStatusFailed"
            ResultPath   = "$.error"
          }
        ]
      }

      SyncToGitHub = {
        Type     = "Task"
        Resource = "arn:aws:states:::lambda:invoke"
        Parameters = {
          FunctionName = var.lambda_function_arns["github_sync"]
          Payload = {
            "s3_bucket.$"       = "$.detail.bucket.name"
            "user_id.$"         = "$.detail.object.key.user_id"
            "video_id.$"        = "$.detail.object.key.video_id"
            "channel_id.$"      = "$.detail.object.key.channel_id"
            "transcript_vtt.$"  = "$.transcriptResult.Payload.transcript_vtt_path"
            "transcript_md.$"   = "$.transcriptResult.Payload.transcript_md_path"
            "youtube_video_id.$" = "$.youtubeResult.Payload.youtube_video_id"
          }
        }
        ResultPath = "$.githubResult"
        Next       = "UpdateStatusCompleted"
        Retry = [
          {
            ErrorEquals     = ["States.TaskFailed"]
            IntervalSeconds = 3
            MaxAttempts     = 2
            BackoffRate     = 2.0
          }
        ]
        Catch = [
          {
            ErrorEquals = ["States.ALL"]
            Next         = "UpdateStatusFailed"
            ResultPath   = "$.error"
          }
        ]
      }

      UpdateStatusCompleted = {
        Type = "Task"
        Resource = "arn:aws:states:::dynamodb:updateItem"
        Parameters = {
          TableName = var.dynamodb_table_name
          Key = {
            user_id = {
              "S.$" = "$.detail.object.key.user_id"
            }
            video_id = {
              "S.$" = "$.detail.object.key.video_id"
            }
          }
          UpdateExpression = "SET upload_status = :status, processing_completed = :timestamp, youtube_video_id = :youtube_id, github_commit_sha = :commit_sha"
          ExpressionAttributeValues = {
            ":status" = {
              S = "completed"
            }
            ":timestamp" = {
              "S.$" = "$$.State.EnteredTime"
            }
            ":youtube_id" = {
              "S.$" = "$.youtubeResult.Payload.youtube_video_id"
            }
            ":commit_sha" = {
              "S.$" = "$.githubResult.Payload.commit_sha"
            }
          }
        }
        End = true
      }

      UpdateStatusFailed = {
        Type = "Task"
        Resource = "arn:aws:states:::dynamodb:updateItem"
        Parameters = {
          TableName = var.dynamodb_table_name
          Key = {
            user_id = {
              "S.$" = "$.detail.object.key.user_id"
            }
            video_id = {
              "S.$" = "$.detail.object.key.video_id"
            }
          }
          UpdateExpression = "SET upload_status = :status, processing_failed = :timestamp, error_message = :error"
          ExpressionAttributeValues = {
            ":status" = {
              S = "failed"
            }
            ":timestamp" = {
              "S.$" = "$$.State.EnteredTime"
            }
            ":error" = {
              "S.$" = "States.Format('{}', $.error)"
            }
          }
        }
        End = true
      }
    }
  })

  tags = var.tags
}
