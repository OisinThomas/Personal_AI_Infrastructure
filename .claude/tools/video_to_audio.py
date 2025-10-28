#!/usr/bin/env python3
"""
Video to Audio Converter

A simple ffmpeg wrapper to extract audio from video files.
Pure function: video file → audio file, no side effects.

Usage:
    ./video_to_audio.py video.mp4
    ./video_to_audio.py video.mp4 --output audio.mp3
    ./video_to_audio.py video.mp4 --format wav --quality high
"""

import sys
import os
import subprocess
import argparse
from pathlib import Path


# Supported formats
VIDEO_FORMATS = ['.mp4', '.mov', '.avi', '.mkv', '.webm', '.flv', '.wmv', '.m4v']
AUDIO_FORMATS = {
    'mp3': {'codec': 'libmp3lame', 'ext': '.mp3'},
    'wav': {'codec': 'pcm_s16le', 'ext': '.wav'},
    'm4a': {'codec': 'aac', 'ext': '.m4a'},
    'flac': {'codec': 'flac', 'ext': '.flac'},
    'ogg': {'codec': 'libvorbis', 'ext': '.ogg'},
}

# Quality presets (bitrate for lossy formats)
QUALITY_PRESETS = {
    'high': '320k',
    'medium': '192k',
    'low': '128k',
}


def check_ffmpeg():
    """Check if ffmpeg is installed."""
    try:
        subprocess.run(
            ['ffmpeg', '-version'],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def convert_video_to_audio(
    video_path: str,
    output_path: str = None,
    audio_format: str = 'mp3',
    quality: str = 'medium'
) -> str:
    """
    Convert video file to audio file.
    
    Pure function: Takes video path, returns audio path.
    No side effects beyond creating the output file.
    
    Args:
        video_path: Path to input video file
        output_path: Optional output path (defaults to video_name.{format})
        audio_format: Output format (mp3, wav, m4a, flac, ogg)
        quality: Quality preset (high, medium, low) - only for lossy formats
        
    Returns:
        Path to created audio file
        
    Raises:
        FileNotFoundError: If video file doesn't exist
        ValueError: If format is unsupported
        RuntimeError: If conversion fails
    """
    # Validate input
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")
    
    video_ext = Path(video_path).suffix.lower()
    if video_ext not in VIDEO_FORMATS:
        raise ValueError(
            f"Unsupported video format: {video_ext}\n"
            f"Supported formats: {', '.join(VIDEO_FORMATS)}"
        )
    
    if audio_format not in AUDIO_FORMATS:
        raise ValueError(
            f"Unsupported audio format: {audio_format}\n"
            f"Supported formats: {', '.join(AUDIO_FORMATS.keys())}"
        )
    
    # Determine output path
    if output_path is None:
        video_name = Path(video_path).stem
        video_dir = Path(video_path).parent
        audio_ext = AUDIO_FORMATS[audio_format]['ext']
        output_path = str(video_dir / f"{video_name}{audio_ext}")
    
    # Get codec and quality settings
    codec = AUDIO_FORMATS[audio_format]['codec']
    
    # Build ffmpeg command
    cmd = [
        'ffmpeg',
        '-i', video_path,
        '-vn',  # No video
        '-acodec', codec,
    ]
    
    # Add quality settings for lossy formats
    if audio_format in ['mp3', 'm4a', 'ogg']:
        bitrate = QUALITY_PRESETS.get(quality, '192k')
        cmd.extend(['-b:a', bitrate])
    
    # Add output path
    cmd.extend(['-y', output_path])  # -y to overwrite
    
    # Execute conversion
    try:
        print(f"Converting {Path(video_path).name} to {audio_format.upper()}...")
        print(f"Quality: {quality} ({QUALITY_PRESETS.get(quality, 'default')})")
        
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        
        # Verify output was created
        if not os.path.exists(output_path):
            raise RuntimeError("Conversion completed but output file not found")
        
        file_size = os.path.getsize(output_path)
        print(f"✓ Created: {output_path} ({file_size:,} bytes)")
        
        return output_path
        
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr if e.stderr else str(e)
        raise RuntimeError(f"FFmpeg conversion failed: {error_msg}")


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Convert video files to audio files using ffmpeg',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s video.mp4
  %(prog)s video.mp4 --output audio.mp3
  %(prog)s video.mov --format wav --quality high
  %(prog)s lecture.mp4 --format m4a
  
Supported video formats: MP4, MOV, AVI, MKV, WebM, FLV, WMV, M4V
Supported audio formats: MP3, WAV, M4A, FLAC, OGG

Quality presets (for MP3/M4A/OGG):
  high   - 320kbps
  medium - 192kbps (default)
  low    - 128kbps
        """
    )
    
    parser.add_argument(
        'video_file',
        help='Path to video file'
    )
    
    parser.add_argument(
        '--output', '-o',
        help='Output audio file path (default: {video_name}.{format})'
    )
    
    parser.add_argument(
        '--format', '-f',
        choices=['mp3', 'wav', 'm4a', 'flac', 'ogg'],
        default='mp3',
        help='Output audio format (default: mp3)'
    )
    
    parser.add_argument(
        '--quality', '-q',
        choices=['high', 'medium', 'low'],
        default='medium',
        help='Audio quality for lossy formats (default: medium)'
    )
    
    args = parser.parse_args()
    
    # Check ffmpeg
    if not check_ffmpeg():
        print("Error: ffmpeg is not installed or not in PATH")
        print("\nInstall ffmpeg:")
        print("  macOS:  brew install ffmpeg")
        print("  Ubuntu: sudo apt-get install ffmpeg")
        print("  Fedora: sudo dnf install ffmpeg")
        sys.exit(1)
    
    # Convert
    try:
        output_path = convert_video_to_audio(
            video_path=args.video_file,
            output_path=args.output,
            audio_format=args.format,
            quality=args.quality
        )
        
        print(f"\n✓ Conversion complete!")
        print(f"  Input:  {args.video_file}")
        print(f"  Output: {output_path}")
        
        sys.exit(0)
        
    except (FileNotFoundError, ValueError, RuntimeError) as e:
        print(f"\n✗ Error: {e}")
        sys.exit(1)
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Conversion interrupted by user")
        sys.exit(1)
    
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
