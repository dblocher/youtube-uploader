"""
Configuration management for YouTube Uploader CLI
"""
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field, validator


class Config(BaseModel):
    """Configuration model"""
    aws_profile: str = Field(description="AWS CLI profile name")
    aws_region: str = Field(default="us-east-1", description="AWS region")
    s3_bucket: str = Field(description="S3 bucket name for uploads")
    user_id: str = Field(description="User ID for multi-tenant isolation")
    channel_id: str = Field(description="YouTube channel ID")
    github_repo: Optional[str] = Field(default=None, description="GitHub repository (owner/repo)")

    @validator('github_repo')
    def validate_github_repo(cls, v):
        """Validate GitHub repo format"""
        if v and '/' not in v:
            raise ValueError("GitHub repo must be in format 'owner/repo'")
        return v


class ConfigManager:
    """Manage CLI configuration"""

    def __init__(self, config_dir: Optional[Path] = None):
        """
        Initialize configuration manager

        Args:
            config_dir: Directory to store configuration (default: ~/.youtube-uploader)
        """
        if config_dir is None:
            config_dir = Path.home() / '.youtube-uploader'

        self.config_dir = config_dir
        self.config_file = config_dir / 'config.json'

        # Create config directory if it doesn't exist
        self.config_dir.mkdir(parents=True, exist_ok=True)

    def load(self) -> Optional[Config]:
        """
        Load configuration from file

        Returns:
            Config object if exists, None otherwise
        """
        if not self.config_file.exists():
            return None

        try:
            with open(self.config_file, 'r') as f:
                data = json.load(f)
                return Config(**data)
        except Exception as e:
            raise ValueError(f"Failed to load configuration: {str(e)}")

    def save(self, config: Config) -> None:
        """
        Save configuration to file

        Args:
            config: Config object to save
        """
        with open(self.config_file, 'w') as f:
            json.dump(config.dict(), f, indent=2)

    def exists(self) -> bool:
        """
        Check if configuration file exists

        Returns:
            True if configuration exists, False otherwise
        """
        return self.config_file.exists()

    def delete(self) -> None:
        """Delete configuration file"""
        if self.config_file.exists():
            self.config_file.unlink()
