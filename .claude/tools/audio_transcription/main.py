#!/usr/bin/env -S uv run python
"""
Audio Transcription CLI

Transcribe audio files using OpenAI's Whisper and GPT-4o models.
Supports multiple transcription modes for different use cases.

Usage:
    ./main.py audio.mp3
    ./main.py audio.mp3 --mode whisper_only
    ./main.py audio.mp3 --output transcript.json
"""

import sys
import os
import asyncio
import argparse
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from workflow.main_workflow import process_audio
from config import AudioTranscriptionConfig


def main():
    """Main CLI entry point."""
    
    parser = argparse.ArgumentParser(
        description='Transcribe audio files with multiple mode options',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Transcription Modes:
  no_timestamps    - Fast, high accuracy, no timing (gpt-4o-transcribe)
  whisper_only     - Fast, word-level timestamps (whisper-1)
  hybrid           - Best accuracy + sentence timestamps (both models)
  sliding_window   - Perfect boundaries + timestamps (default)

Examples:
  %(prog)s podcast.mp3
  %(prog)s lecture.wav --mode whisper_only
  %(prog)s interview.m4a --output ~/transcripts/interview.json
  %(prog)s long_audio.mp3 --workers 20 --chunk-minutes 3
        """
    )
    
    parser.add_argument(
        'audio_file',
        help='Path to audio file (MP3, WAV, M4A, FLAC, OGG, AAC)'
    )
    
    parser.add_argument(
        '--output', '-o',
        help='Output JSON file path (default: {audio_name}.json next to input)'
    )
    
    parser.add_argument(
        '--mode', '-m',
        choices=['no_timestamps', 'whisper_only', 'hybrid', 'sliding_window'],
        default=None,
        help=f'Transcription mode (default: {AudioTranscriptionConfig.DEFAULT_MODE})'
    )
    
    parser.add_argument(
        '--workers', '-w',
        type=int,
        default=None,
        help=f'Number of parallel workers (default: {AudioTranscriptionConfig.MAX_WORKERS})'
    )
    
    parser.add_argument(
        '--chunk-minutes', '-c',
        type=int,
        default=None,
        help=f'Chunk duration in minutes (default: {AudioTranscriptionConfig.CHUNK_MINUTES})'
    )
    
    args = parser.parse_args()
    
    # Validate audio file
    audio_path = args.audio_file
    if not os.path.exists(audio_path):
        print(f"Error: Audio file not found: {audio_path}")
        sys.exit(1)
    
    # Check file extension
    file_ext = Path(audio_path).suffix.lower()
    if file_ext not in AudioTranscriptionConfig.SUPPORTED_FORMATS:
        print(f"Error: Unsupported audio format: {file_ext}")
        print(f"Supported formats: {', '.join(AudioTranscriptionConfig.SUPPORTED_FORMATS)}")
        sys.exit(1)
    
    # Validate configuration
    try:
        AudioTranscriptionConfig.validate()
    except ValueError as e:
        print(f"Configuration error: {e}")
        print("\nPlease set the OPENAI_API_KEY_DEFAULT environment variable.")
        sys.exit(1)
    
    # Run transcription
    try:
        result = asyncio.run(process_audio(
            audio_path=audio_path,
            output_path=args.output,
            transcription_mode=args.mode,
            chunk_minutes=args.chunk_minutes,
            max_workers=args.workers
        ))
        
        if not result['success']:
            print(f"\n❌ Transcription failed: {result.get('error', 'Unknown error')}")
            sys.exit(1)
        
        # Show sample of transcript
        transcript = result.get('transcript', '')
        if transcript:
            lines = transcript.split('\n')[:5]
            print(f"\n📄 Sample transcript:")
            for line in lines:
                if line.strip():
                    print(f"  {line}")
            if len(transcript.split('\n')) > 5:
                print("  ...")
        
        sys.exit(0)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Process interrupted by user")
        sys.exit(1)
    
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
