"""
Audio extraction utility for video files
"""
import subprocess
import tempfile
import shutil
from pathlib import Path
from typing import Optional
import click


def check_ffmpeg_installed() -> bool:
    """
    Check if ffmpeg is installed and available

    Returns:
        True if ffmpeg is available, False otherwise
    """
    return shutil.which('ffmpeg') is not None


def extract_audio(
    video_path: Path,
    output_path: Optional[Path] = None,
    audio_format: str = 'mp3',
    sample_rate: int = 16000,
    channels: int = 1
) -> Path:
    """
    Extract audio from video file using ffmpeg

    Args:
        video_path: Path to video file
        output_path: Optional output path for audio file
        audio_format: Audio format (mp3, wav, etc.)
        sample_rate: Audio sample rate in Hz (default: 16000 for transcription)
        channels: Number of audio channels (default: 1 for mono)

    Returns:
        Path to extracted audio file

    Raises:
        RuntimeError: If ffmpeg is not installed or extraction fails
        FileNotFoundError: If video file doesn't exist
    """
    if not check_ffmpeg_installed():
        raise RuntimeError(
            "ffmpeg is not installed. Please install ffmpeg:\n"
            "  macOS: brew install ffmpeg\n"
            "  Ubuntu/Debian: sudo apt-get install ffmpeg\n"
            "  Windows: Download from https://ffmpeg.org/download.html"
        )

    if not video_path.exists():
        raise FileNotFoundError(f"Video file not found: {video_path}")

    # Create output path if not provided
    if output_path is None:
        temp_dir = Path(tempfile.gettempdir())
        output_path = temp_dir / f"{video_path.stem}.{audio_format}"

    click.echo(f"Extracting audio from video...")

    try:
        # Extract audio using ffmpeg
        # -i: input file
        # -vn: no video
        # -acodec: audio codec
        # -ar: audio sample rate
        # -ac: audio channels
        # -y: overwrite output file
        subprocess.run([
            'ffmpeg',
            '-i', str(video_path),
            '-vn',  # No video
            '-acodec', audio_format if audio_format == 'mp3' else 'pcm_s16le',
            '-ar', str(sample_rate),
            '-ac', str(channels),
            '-y',  # Overwrite output
            str(output_path)
        ], check=True, capture_output=True, text=True)

        click.echo(f"✓ Audio extracted: {output_path.name}")
        return output_path

    except subprocess.CalledProcessError as e:
        error_msg = e.stderr if e.stderr else str(e)
        raise RuntimeError(f"Failed to extract audio: {error_msg}")


def get_video_duration(video_path: Path) -> float:
    """
    Get video duration in seconds using ffprobe

    Args:
        video_path: Path to video file

    Returns:
        Duration in seconds

    Raises:
        RuntimeError: If ffprobe fails
    """
    try:
        result = subprocess.run([
            'ffprobe',
            '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            str(video_path)
        ], check=True, capture_output=True, text=True)

        return float(result.stdout.strip())

    except (subprocess.CalledProcessError, ValueError) as e:
        raise RuntimeError(f"Failed to get video duration: {str(e)}")
