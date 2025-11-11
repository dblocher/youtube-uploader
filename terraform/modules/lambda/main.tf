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

  # For zip deployments - use dummy zip as placeholder
  filename         = each.value.use_container_image ? null : data.archive_file.lambda_zip[each.key].output_path
  source_code_hash = each.value.use_container_image ? null : data.archive_file.lambda_zip[each.key].output_base64sha256

  # Handler and runtime for ZIP packages
  handler = each.value.use_container_image ? null : "handler.lambda_handler"
  runtime = each.value.use_container_image ? null : "python3.11"

  # Image URI for container-based deployments (to be updated)
  image_uri = each.value.use_container_image ? lookup(var.ecr_image_uris, each.key, null) : null

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

# Create dummy Python file for non-container Lambda functions
resource "local_file" "dummy_lambda" {
  for_each = { for k, v in var.lambda_functions : k => v if !v.use_container_image }

  content  = "def lambda_handler(event, context):\n    return {'statusCode': 200, 'body': 'Placeholder function'}\n"
  filename = "${path.module}/dummy_${each.key}.py"
}

# Create zip archive for non-container Lambda functions
data "archive_file" "lambda_zip" {
  for_each = { for k, v in var.lambda_functions : k => v if !v.use_container_image }

  type        = "zip"
  source_file = local_file.dummy_lambda[each.key].filename
  output_path = "${path.module}/dummy_${each.key}.zip"

  depends_on = [local_file.dummy_lambda]
}
