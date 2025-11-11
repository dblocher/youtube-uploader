terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    null = {
      source  = "hashicorp/null"
      version = "~> 3.0"
    }
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project   = "youtube-uploader"
      ManagedBy = "Terraform"
    }
  }
}

# Get current AWS account ID
data "aws_caller_identity" "current" {}

# DynamoDB table
module "dynamodb" {
  source = "./modules/dynamodb"

  table_name = var.dynamodb_table_name
  tags       = var.tags
}

# S3 bucket
module "s3" {
  source = "./modules/s3"

  bucket_name                = var.s3_bucket_name
  enable_lifecycle_policy    = var.enable_lifecycle_policy
  lifecycle_expiration_days  = var.lifecycle_expiration_days
  tags                       = var.tags
}

# SSM Parameters for secrets
module "secrets" {
  source = "./modules/secrets"

  user_ids = var.user_ids
  tags     = var.tags
}

# Lambda functions
module "lambda" {
  source = "./modules/lambda"

  project_name        = var.project_name
  s3_bucket_name      = module.s3.bucket_name
  s3_bucket_arn       = module.s3.bucket_arn
  dynamodb_table_name = module.dynamodb.table_name
  dynamodb_table_arn  = module.dynamodb.table_arn
  aws_region          = var.aws_region
  aws_account_id      = data.aws_caller_identity.current.account_id
  ecr_image_uris      = var.ecr_image_uris
  tags                = var.tags

  lambda_functions = {
    transcript_generator = {
      timeout             = 900  # 15 minutes for video processing
      memory_size         = 3008
      use_container_image = false
      environment_variables = {
        BEDROCK_MODEL_ID = "anthropic.claude-3-5-sonnet-20241022-v2:0"
      }
    }
    video_uploader = {
      timeout             = 900  # 15 minutes for YouTube upload
      memory_size         = 2048
      use_container_image = true
      environment_variables = {}
    }
    github_sync = {
      timeout             = 300  # 5 minutes
      memory_size         = 512
      use_container_image = false
      environment_variables = {}
    }
  }
}

# Step Functions state machine
module "step_functions" {
  source = "./modules/step-functions"

  project_name         = var.project_name
  lambda_function_arns = module.lambda.lambda_function_arns
  dynamodb_table_name  = module.dynamodb.table_name
  dynamodb_table_arn   = module.dynamodb.table_arn
  tags                 = var.tags
}

# EventBridge rule
module "eventbridge" {
  source = "./modules/eventbridge"

  project_name      = var.project_name
  s3_bucket_name    = module.s3.bucket_name
  state_machine_arn = module.step_functions.state_machine_arn
  tags              = var.tags
}
