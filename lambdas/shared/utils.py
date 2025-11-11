"""
Shared utility functions for Lambda functions
"""
import json
import boto3
from typing import Dict, Any


def get_ssm_parameter(parameter_name: str, decrypt: bool = True) -> str:
    """
    Retrieve a parameter from AWS Systems Manager Parameter Store

    Args:
        parameter_name: Name of the parameter to retrieve
        decrypt: Whether to decrypt SecureString parameters

    Returns:
        Parameter value as string
    """
    ssm = boto3.client('ssm')
    response = ssm.get_parameter(Name=parameter_name, WithDecryption=decrypt)
    return response['Parameter']['Value']


def update_dynamodb_status(
    table_name: str,
    user_id: str,
    video_id: str,
    status: str,
    additional_attributes: Dict[str, Any] = None
) -> None:
    """
    Update video processing status in DynamoDB

    Args:
        table_name: Name of the DynamoDB table
        user_id: User ID
        video_id: Video ID
        status: Processing status
        additional_attributes: Additional attributes to update
    """
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(table_name)

    update_expression = "SET upload_status = :status"
    expression_values = {":status": status}

    if additional_attributes:
        for key, value in additional_attributes.items():
            update_expression += f", {key} = :{key}"
            expression_values[f":{key}"] = value

    table.update_item(
        Key={
            'user_id': user_id,
            'video_id': video_id
        },
        UpdateExpression=update_expression,
        ExpressionAttributeValues=expression_values
    )


def parse_s3_key(s3_key: str) -> Dict[str, str]:
    """
    Parse S3 key to extract user_id, channel_id, and video_id

    Expected format: {user_id}/{channel_id}/videos/{video_id}/filename

    Args:
        s3_key: S3 object key

    Returns:
        Dictionary with user_id, channel_id, and video_id
    """
    parts = s3_key.split('/')

    if len(parts) < 5:
        raise ValueError(f"Invalid S3 key format: {s3_key}")

    return {
        'user_id': parts[0],
        'channel_id': parts[1],
        'video_id': parts[3]
    }
