"""
Main CLI application for YouTube Uploader
"""
import click
import uuid
from pathlib import Path
from rich.console import Console
from rich.panel import Panel

from .config import Config, ConfigManager
from .metadata import collect_metadata_interactive
from .s3_client import S3Uploader


console = Console()


@click.group()
@click.version_option(version='0.1.0')
def cli():
    """YouTube Uploader CLI - Upload videos to YouTube via AWS"""
    pass


@cli.command()
def init():
    """Initialize CLI configuration"""
    config_manager = ConfigManager()

    if config_manager.exists():
        if not click.confirm("Configuration already exists. Overwrite?", default=False):
            click.echo("Configuration initialization cancelled.")
            return

    console.print("\n[bold cyan]YouTube Uploader Configuration[/bold cyan]\n")

    # Collect configuration
    aws_profile = click.prompt("AWS CLI Profile Name", type=str, default="default")
    aws_region = click.prompt("AWS Region", type=str, default="us-east-1")
    s3_bucket = click.prompt("S3 Bucket Name", type=str)
    user_id = click.prompt("User ID", type=str, default="default")
    channel_id = click.prompt("YouTube Channel ID", type=str)
    github_repo = click.prompt(
        "GitHub Repository (owner/repo, optional)",
        type=str,
        default="",
        show_default=False
    )

    # Validate configuration
    try:
        config = Config(
            aws_profile=aws_profile,
            aws_region=aws_region,
            s3_bucket=s3_bucket,
            user_id=user_id,
            channel_id=channel_id,
            github_repo=github_repo if github_repo else None
        )
    except Exception as e:
        console.print(f"[red]Configuration validation failed: {str(e)}[/red]")
        return

    # Test AWS credentials
    console.print("\n[yellow]Testing AWS credentials...[/yellow]")
    try:
        uploader = S3Uploader(s3_bucket, aws_profile, aws_region)
        if uploader.validate_credentials():
            console.print("[green]✓ AWS credentials validated successfully[/green]")
        else:
            console.print("[red]✗ AWS credentials validation failed[/red]")
            return
    except Exception as e:
        console.print(f"[red]✗ AWS validation error: {str(e)}[/red]")
        return

    # Save configuration
    config_manager.save(config)
    console.print(f"\n[green]Configuration saved to {config_manager.config_file}[/green]")

    # Display next steps
    console.print("\n[bold cyan]Next Steps:[/bold cyan]")
    console.print("1. Ensure your AWS SSM parameters are configured:")
    console.print(f"   - /youtube-uploader/{user_id}/youtube-api-credentials")
    console.print(f"   - /youtube-uploader/{user_id}/youtube-channel-id")
    console.print(f"   - /youtube-uploader/{user_id}/github-token")
    console.print(f"   - /youtube-uploader/{user_id}/github-repo")
    console.print("\n2. Deploy infrastructure using Terraform")
    console.print("\n3. Upload videos using: youtube-uploader upload VIDEO_FILE")


@cli.command()
@click.argument('video_file', type=click.Path(exists=True, path_type=Path))
@click.option('--thumbnail', type=click.Path(exists=True, path_type=Path), help='Thumbnail image file')
def upload(video_file: Path, thumbnail: Path = None):
    """Upload a video to YouTube"""
    config_manager = ConfigManager()

    # Load configuration
    if not config_manager.exists():
        console.print("[red]Configuration not found. Please run 'youtube-uploader init' first.[/red]")
        return

    config = config_manager.load()

    # Display upload info
    console.print(Panel.fit(
        f"[bold]Video Upload[/bold]\n\n"
        f"Video: {video_file.name}\n"
        f"Thumbnail: {thumbnail.name if thumbnail else 'None'}\n"
        f"Bucket: {config.s3_bucket}\n"
        f"Channel: {config.channel_id}",
        title="Upload Configuration"
    ))

    # Collect metadata
    try:
        metadata = collect_metadata_interactive()
    except click.Abort:
        return

    # Generate video ID
    video_id = str(uuid.uuid4())
    console.print(f"\n[cyan]Generated Video ID: {video_id}[/cyan]")

    # Initialize S3 uploader
    try:
        uploader = S3Uploader(config.s3_bucket, config.aws_profile, config.aws_region)
    except Exception as e:
        console.print(f"[red]Failed to initialize S3 uploader: {str(e)}[/red]")
        return

    # Upload files
    try:
        console.print("\n[bold yellow]Starting upload...[/bold yellow]")

        uploaded = uploader.upload_video_package(
            user_id=config.user_id,
            channel_id=config.channel_id,
            video_id=video_id,
            video_path=video_file,
            metadata=metadata.dict(),
            thumbnail_path=thumbnail
        )

        console.print("\n[bold green]✓ Upload completed successfully![/bold green]")
        console.print("\n[cyan]Uploaded Files:[/cyan]")
        for key, uri in uploaded.items():
            console.print(f"  {key}: {uri}")

        console.print(f"\n[yellow]Video ID: {video_id}[/yellow]")
        console.print("\nThe video processing workflow has been triggered.")
        console.print("You can monitor the progress in the AWS Step Functions console.")

    except Exception as e:
        console.print(f"\n[red]Upload failed: {str(e)}[/red]")
        return


@cli.command()
def config():
    """Display current configuration"""
    config_manager = ConfigManager()

    if not config_manager.exists():
        console.print("[red]Configuration not found. Please run 'youtube-uploader init' first.[/red]")
        return

    config = config_manager.load()

    console.print(Panel.fit(
        f"[bold]Current Configuration[/bold]\n\n"
        f"AWS Profile: {config.aws_profile}\n"
        f"AWS Region: {config.aws_region}\n"
        f"S3 Bucket: {config.s3_bucket}\n"
        f"User ID: {config.user_id}\n"
        f"Channel ID: {config.channel_id}\n"
        f"GitHub Repo: {config.github_repo or 'Not configured'}\n\n"
        f"Config File: {config_manager.config_file}",
        title="Configuration"
    ))


@cli.command()
def reset():
    """Reset CLI configuration"""
    config_manager = ConfigManager()

    if not config_manager.exists():
        console.print("[yellow]No configuration found.[/yellow]")
        return

    if click.confirm("Are you sure you want to delete the configuration?", default=False):
        config_manager.delete()
        console.print("[green]Configuration deleted.[/green]")
    else:
        console.print("Reset cancelled.")


if __name__ == '__main__':
    cli()
