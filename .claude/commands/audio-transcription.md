## Audio Transcription Command

Transcribe audio files using OpenAI's Whisper and GPT-4o models with multiple transcription modes.

## Quick Usage

```bash
# Basic usage (sliding_window mode - best quality)
~/.claude/tools/audio_transcription/main.py podcast.mp3

# Specify transcription mode
~/.claude/tools/audio_transcription/main.py lecture.wav --mode whisper_only

# Custom output location
~/.claude/tools/audio_transcription/main.py interview.m4a --output ~/transcripts/interview.json

# Performance tuning for long files
~/.claude/tools/audio_transcription/main.py long_audio.mp3 --workers 20 --chunk-minutes 3
```

## Installation

### 1. Install UV (if not already installed)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Install System Dependencies

The tool requires `ffmpeg` for audio processing:

```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt-get install ffmpeg

# Fedora
sudo dnf install ffmpeg

# Verify installation
ffmpeg -version
```

### 3. Install Python Dependencies

```bash
cd ~/.claude/tools/audio_transcription
uv sync
```

This will install all required dependencies in an isolated virtual environment.

## Configuration

Set your OpenAI API key:

```bash
# Add to ~/.claude/.env
OPENAI_API_KEY_DEFAULT="your-openai-api-key-here"

# Or export in your shell
export OPENAI_API_KEY_DEFAULT="your-openai-api-key-here"
```

### Optional Configuration

```bash
# Add to ~/.claude/.env for custom defaults

# Default transcription mode
AUDIO_TRANSCRIPTION_MODE="sliding_window"

# Chunk size (1-5 minutes recommended)
AUDIO_CHUNK_MINUTES="2"

# Number of parallel workers
AUDIO_MAX_WORKERS="10"

# Save intermediate outputs for debugging
SAVE_INTERMEDIATE_OUTPUTS="false"
```

## Transcription Modes

### 1. `sliding_window` (Default) ⭐

**Best for**: Maximum accuracy with perfect boundaries and timestamps

- **Models**: Whisper → GPT-4o (sequential)
- **Process**: 
  1. Transcribes with Whisper first
  2. Uses Whisper text as context for GPT-4o
  3. Maps Whisper timestamps to refined text
- **Output**: Sentence-level timestamps with perfect accuracy
- **Speed**: Medium
- **Cost**: ~$0.012/minute

**Example**:
```bash
~/.claude/tools/audio_transcription/main.py podcast.mp3
```

### 2. `hybrid`

**Best for**: Highest accuracy with sentence-level timestamps

- **Models**: GPT-4o-transcribe + Whisper (parallel)
- **Process**:
  1. Transcribes each chunk with both models simultaneously
  2. Uses LLM to combine results
  3. Favors GPT-4o for text accuracy, Whisper for timing
- **Output**: Sentence-level timestamps
- **Speed**: Medium
- **Cost**: ~$0.012/minute

**Example**:
```bash
~/.claude/tools/audio_transcription/main.py lecture.wav --mode hybrid
```

### 3. `whisper_only`

**Best for**: Fast transcription with word-level timestamps

- **Model**: Whisper-1 only
- **Output**: Word-level timestamps
- **Speed**: Fast
- **Cost**: ~$0.006/minute

**Example**:
```bash
~/.claude/tools/audio_transcription/main.py meeting.m4a --mode whisper_only
```

### 4. `no_timestamps`

**Best for**: Fast, high-accuracy text without timing

- **Model**: GPT-4o-transcribe only
- **Output**: Clean text, no timestamps
- **Speed**: Fast
- **Cost**: ~$0.006/minute

**Example**:
```bash
~/.claude/tools/audio_transcription/main.py interview.mp3 --mode no_timestamps
```

## Supported Audio Formats

- ✅ **MP3** - Most common format
- ✅ **WAV** - Uncompressed audio
- ✅ **M4A** - Apple/AAC format
- ✅ **FLAC** - Lossless compression
- ✅ **OGG** - Vorbis format
- ✅ **AAC** - Advanced Audio Coding

All formats are automatically converted to WAV internally for processing.

## Usage Examples

### Basic Transcription

```bash
# Transcribe podcast (default: sliding_window mode)
~/.claude/tools/audio_transcription/main.py podcast.mp3
# Output: podcast.json (next to podcast.mp3)
```

### Custom Output Location

```bash
# Save to specific location
~/.claude/tools/audio_transcription/main.py lecture.wav \
  --output ~/Documents/transcripts/lecture.json
```

### Different Modes

```bash
# Fast transcription without timestamps
~/.claude/tools/audio_transcription/main.py interview.mp3 \
  --mode no_timestamps

# Word-level timestamps
~/.claude/tools/audio_transcription/main.py meeting.m4a \
  --mode whisper_only

# Maximum accuracy with timestamps
~/.claude/tools/audio_transcription/main.py webinar.mp3 \
  --mode hybrid
```

### Performance Tuning

```bash
# Faster processing for long files
~/.claude/tools/audio_transcription/main.py long_audio.mp3 \
  --workers 20 \
  --chunk-minutes 3
```

### Batch Processing

```bash
# Process multiple files
for audio in ~/podcasts/*.mp3; do
  ~/.claude/tools/audio_transcription/main.py "$audio" \
    --output ~/transcripts/$(basename "$audio" .mp3).json
done
```

## Output Format

The tool creates a JSON file with the following structure:

```json
{
  "source_file": "/path/to/audio.mp3",
  "duration_seconds": 3425.5,
  "transcription_mode": "sliding_window",
  "created_at": "2025-01-25T20:00:00Z",
  "transcript": "[00:00:00] Welcome to the podcast.\n[00:00:05] Today we're discussing...",
  "metadata": {
    "transcription_mode": "sliding_window",
    "models_used": ["whisper-1", "gpt-4o-transcribe"],
    "chunks_processed": 28,
    "duration_seconds": 3425.5,
    "estimated_cost_usd": 0.85
  }
}
```

### Transcript Format

**With timestamps** (sliding_window, hybrid, whisper_only):
```
[00:00:00] Welcome to today's podcast.
[00:00:05] We're going to discuss artificial intelligence.
[00:00:12] Let's start with the basics.
```

**Without timestamps** (no_timestamps):
```
Welcome to today's podcast. We're going to discuss artificial intelligence. Let's start with the basics.
```

## Performance & Cost

### Processing Speed

| Mode | Speed | Typical Time (60 min audio) |
|------|-------|----------------------------|
| `no_timestamps` | Fast | ~5-8 minutes |
| `whisper_only` | Fast | ~5-8 minutes |
| `hybrid` | Medium | ~10-15 minutes |
| `sliding_window` | Medium | ~10-15 minutes |

*With 10 parallel workers. Increase `--workers` for faster processing.*

### Cost Estimates

| Mode | Cost per Minute | 60 min Audio |
|------|----------------|--------------|
| `no_timestamps` | $0.006 | $0.36 |
| `whisper_only` | $0.006 | $0.36 |
| `hybrid` | $0.012 | $0.72 |
| `sliding_window` | $0.012 | $0.72 |

*Estimates based on OpenAI pricing. Actual costs may vary.*

## Troubleshooting

### "ffmpeg not found"

```bash
# Install ffmpeg
brew install ffmpeg  # macOS
sudo apt-get install ffmpeg  # Linux
```

### "OPENAI_API_KEY_DEFAULT not set"

```bash
# Add to ~/.claude/.env
echo 'OPENAI_API_KEY_DEFAULT="sk-..."' >> ~/.claude/.env
```

### "Unsupported audio format"

The tool supports: MP3, WAV, M4A, FLAC, OGG, AAC

Convert your audio:
```bash
ffmpeg -i input.wma -acodec libmp3lame output.mp3
```

### Rate Limits

If you hit OpenAI rate limits:

```bash
# Reduce parallel workers
~/.claude/tools/audio_transcription/main.py audio.mp3 --workers 5

# Increase chunk size (fewer API calls)
~/.claude/tools/audio_transcription/main.py audio.mp3 --chunk-minutes 3
```

### Out of Memory

For very long files:

```bash
# Smaller chunks, fewer workers
~/.claude/tools/audio_transcription/main.py long.mp3 \
  --chunk-minutes 1 \
  --workers 5
```

## When to Use

### ✅ Perfect For

- Podcast transcription
- Lecture/webinar notes
- Interview transcripts
- Meeting minutes
- YouTube video captions
- Accessibility subtitles
- Content repurposing (blog posts from audio)

### ⚠️ Limitations

- Audio-only (no video processing)
- English optimized (other languages may vary)
- Requires internet connection (API-based)
- Costs scale with audio length

## Advanced Usage

### Custom Chunk Size

```bash
# Smaller chunks for better accuracy on complex audio
~/.claude/tools/audio_transcription/main.py technical_talk.mp3 \
  --chunk-minutes 1

# Larger chunks for faster processing
~/.claude/tools/audio_transcription/main.py simple_podcast.mp3 \
  --chunk-minutes 5
```

### Parallel Processing

```bash
# Maximum parallelization (requires good API rate limits)
~/.claude/tools/audio_transcription/main.py audio.mp3 --workers 30

# Conservative (avoid rate limits)
~/.claude/tools/audio_transcription/main.py audio.mp3 --workers 5
```

### Integration with Other Tools

```bash
# Extract audio from video first
ffmpeg -i video.mp4 -vn -acodec libmp3lame audio.mp3

# Then transcribe
~/.claude/tools/audio_transcription/main.py audio.mp3

# Clean up
rm audio.mp3
```

## Mode Selection Guide

| Use Case | Recommended Mode | Why |
|----------|-----------------|-----|
| YouTube subtitles | `sliding_window` | Perfect boundaries + timestamps |
| Blog post from podcast | `no_timestamps` | Fast, accurate text only |
| Video editing markers | `whisper_only` | Word-level timing |
| Educational content | `hybrid` | Accuracy + sentence timing |
| Quick transcription | `no_timestamps` | Fastest option |
| Accessibility captions | `sliding_window` | Best overall quality |

## Help

```bash
# Show all options
~/.claude/tools/audio_transcription/main.py --help
```

## See Also

- [PDF to Markdown](./pdf-to-markdown.md) - Convert PDFs to markdown
- [OpenAI Whisper API](https://platform.openai.com/docs/guides/speech-to-text)
- [FFmpeg Documentation](https://ffmpeg.org/documentation.html)
