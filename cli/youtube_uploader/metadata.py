"""
Metadata collection and validation
"""
from typing import Optional
from pydantic import BaseModel, Field, validator


class VideoMetadata(BaseModel):
    """Video metadata model"""
    title: str = Field(description="Video title")
    description: str = Field(default="", description="Video description")
    privacy_status: str = Field(default="private", description="Privacy status: public, private, unlisted")
    tags: list[str] = Field(default_factory=list, description="Video tags")
    category_id: str = Field(default="22", description="YouTube category ID")

    @validator('privacy_status')
    def validate_privacy_status(cls, v):
        """Validate privacy status"""
        valid_statuses = ['public', 'private', 'unlisted']
        if v.lower() not in valid_statuses:
            raise ValueError(f"Privacy status must be one of: {', '.join(valid_statuses)}")
        return v.lower()

    @validator('title')
    def validate_title(cls, v):
        """Validate title length"""
        if not v or len(v.strip()) == 0:
            raise ValueError("Title cannot be empty")
        if len(v) > 100:
            raise ValueError("Title must be 100 characters or less")
        return v.strip()

    @validator('description')
    def validate_description(cls, v):
        """Validate description length"""
        if len(v) > 5000:
            raise ValueError("Description must be 5000 characters or less")
        return v


def collect_metadata_interactive() -> VideoMetadata:
    """
    Collect video metadata through interactive prompts

    Returns:
        VideoMetadata object
    """
    import click

    click.echo("\n" + "="*50)
    click.echo("Video Metadata Collection")
    click.echo("="*50 + "\n")

    # Title (required)
    while True:
        title = click.prompt("Video Title", type=str)
        try:
            VideoMetadata(title=title)
            break
        except ValueError as e:
            click.echo(f"Error: {str(e)}", err=True)

    # Description (optional)
    description = click.prompt(
        "Video Description (optional)",
        type=str,
        default="",
        show_default=False
    )

    # Privacy status
    privacy_status = click.prompt(
        "Privacy Status",
        type=click.Choice(['public', 'private', 'unlisted'], case_sensitive=False),
        default='private',
        show_default=True
    )

    # Tags (optional)
    tags_input = click.prompt(
        "Tags (comma-separated, optional)",
        type=str,
        default="",
        show_default=False
    )
    tags = [tag.strip() for tag in tags_input.split(',') if tag.strip()]

    # Category ID (optional, with common categories)
    click.echo("\nCommon YouTube Categories:")
    click.echo("  22 - People & Blogs")
    click.echo("  24 - Entertainment")
    click.echo("  26 - Howto & Style")
    click.echo("  28 - Science & Technology")

    category_id = click.prompt(
        "Category ID",
        type=str,
        default="22",
        show_default=True
    )

    metadata = VideoMetadata(
        title=title,
        description=description,
        privacy_status=privacy_status,
        tags=tags,
        category_id=category_id
    )

    # Confirmation
    click.echo("\n" + "="*50)
    click.echo("Metadata Summary:")
    click.echo("="*50)
    click.echo(f"Title: {metadata.title}")
    click.echo(f"Description: {metadata.description[:100]}{'...' if len(metadata.description) > 100 else ''}")
    click.echo(f"Privacy: {metadata.privacy_status}")
    click.echo(f"Tags: {', '.join(metadata.tags) if metadata.tags else 'None'}")
    click.echo(f"Category ID: {metadata.category_id}")
    click.echo("="*50 + "\n")

    if not click.confirm("Is this correct?", default=True):
        click.echo("Metadata collection cancelled. Please run the command again.")
        raise click.Abort()

    return metadata
