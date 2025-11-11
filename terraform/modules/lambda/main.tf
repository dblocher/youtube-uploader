# IAM Role for Lambda functions
resource "aws_iam_role" "lambda_role" {
  for_each = var.lambda_functions

  name = "${var.project_name}-${each.key}-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })

  tags = var.tags
}

# Basic Lambda execution policy
resource "aws_iam_role_policy_attachment" "lambda_basic" {
  for_each = var.lambda_functions

  role       = aws_iam_role.lambda_role[each.key].name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Custom policy for Lambda functions
resource "aws_iam_role_policy" "lambda_policy" {
  for_each = var.lambda_functions

  name = "${var.project_name}-${each.key}-policy"
  role = aws_iam_role.lambda_role[each.key].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:ListBucket"
        ]
        Resource = [
          "${var.s3_bucket_arn}",
          "${var.s3_bucket_arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "dynamodb:PutItem",
          "dynamodb:GetItem",
          "dynamodb:UpdateItem",
          "dynamodb:Query"
        ]
        Resource = [
          var.dynamodb_table_arn,
          "${var.dynamodb_table_arn}/index/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "ssm:GetParameter",
          "ssm:GetParameters"
        ]
        Resource = "arn:aws:ssm:${var.aws_region}:${var.aws_account_id}:parameter/youtube-uploader/*"
      },
      # Bedrock access for transcript-generator
      {
        Effect = "Allow"
        Action = [
          "bedrock:InvokeModel"
        ]
        Resource = "arn:aws:bedrock:${var.aws_region}::foundation-model/anthropic.claude-*"
      }
    ]
  })
}

# Lambda functions
resource "aws_lambda_function" "functions" {
  for_each = var.lambda_functions

  function_name = "${var.project_name}-${each.key}"
  role          = aws_iam_role.lambda_role[each.key].arn

  # Use container image for video-uploader, zip for others
  package_type = each.value.use_container_image ? "Image" : "Zip"

  # For container images
  dynamic "image_config" {
    for_each = each.value.use_container_image ? [1] : []
    content {
      command = ["handler.lambda_handler"]
    }
  }

  # For zip deployments - placeholder (will be updated by CI/CD or manual deployment)
  filename         = each.value.use_container_image ? null : "${path.module}/dummy.zip"
  source_code_hash = each.value.use_container_image ? null : filebase64sha256("${path.module}/dummy.zip")

  # Image URI for container-based deployments (to be updated)
  image_uri = each.value.use_container_image ? var.ecr_image_uris[each.key] : null

  timeout     = each.value.timeout
  memory_size = each.value.memory_size

  environment {
    variables = merge(
      {
        DYNAMODB_TABLE_NAME = var.dynamodb_table_name
        S3_BUCKET_NAME      = var.s3_bucket_name
        AWS_REGION_NAME     = var.aws_region
      },
      each.value.environment_variables
    )
  }

  tags = var.tags
}

# Create dummy zip file for non-container Lambda functions
resource "null_resource" "create_dummy_zip" {
  provisioner "local-exec" {
    command = "echo 'def lambda_handler(event, context): pass' > /tmp/dummy.py && cd /tmp && zip ${path.module}/dummy.zip dummy.py"
  }
}
