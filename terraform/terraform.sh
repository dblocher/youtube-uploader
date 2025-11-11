#!/bin/bash
#
# Terraform wrapper script that automatically uses your AWS SSO profile
# Usage: ./terraform.sh <terraform-command> [args...]
# Examples:
#   ./terraform.sh init
#   ./terraform.sh plan
#   ./terraform.sh apply
#   ./terraform.sh destroy

# Get the first available AWS profile
PROFILE=$(aws configure list-profiles 2>/dev/null | head -n 1)

if [ -z "$PROFILE" ]; then
    echo "Error: No AWS profiles found. Please configure AWS CLI first:"
    echo "  aws configure sso"
    exit 1
fi

echo "=========================================="
echo "Using AWS Profile: $PROFILE"
echo "=========================================="
echo ""

# Export the profile for Terraform
export TF_VAR_aws_profile="$PROFILE"
export AWS_PROFILE="$PROFILE"

# Check if AWS session is valid
if ! aws sts get-caller-identity --profile "$PROFILE" &>/dev/null; then
    echo "AWS session expired or invalid. Attempting to login..."
    aws sso login --profile "$PROFILE"

    # Check again
    if ! aws sts get-caller-identity --profile "$PROFILE" &>/dev/null; then
        echo "Error: Failed to authenticate with AWS"
        exit 1
    fi
fi

# Display current AWS identity
echo "Authenticated as:"
aws sts get-caller-identity --profile "$PROFILE" --output table
echo ""

# Run terraform with all provided arguments
terraform "$@"
