---
name: video-transcription
description: Transcribe video files to text with timestamps. Automatically extracts audio from video then transcribes using OpenAI Whisper and GPT-4o. Supports MP4, MOV, AVI, MKV, WebM. USE WHEN user says 'transcribe video', 'video to text', 'get transcript from video', provides video file for transcription, or wants to extract text/speech from video.
---

# Video Transcription

## When to Activate This Skill
- User wants to transcribe a video file
- User says "transcribe video.mp4" or "get transcript from video"
- User requests "video to text" conversion
- Task involves extracting speech/text from video
- User provides video file and wants text output

## Two-Step Workflow

This skill orchestrates two independent tools in sequence:

### Step 1: Extract Audio from Video
**Tool**: `~/.claude/tools/video_to_audio.py`

Convert video to audio (MP3 by default):
```bash
~/.claude/tools/video_to_audio.py video.mp4
```

**Output**: `video.mp3` (same location as video)

### Step 2: Transcribe Audio
**Tool**: `~/.claude/tools/audio_transcription/main.py`

Transcribe the extracted audio:
```bash
~/.claude/tools/audio_transcription/main.py video.mp3
```

**Output**: `video.json` with timestamped transcript

## Supported Video Formats

**Input**: MP4, MOV, AVI, MKV, WebM, FLV, WMV, M4V
**Output**: JSON with timestamped transcript

## Transcription Modes

Choose transcription quality (defaults to `sliding_window`):

- **`sliding_window`** (default) - Best quality, perfect boundaries + timestamps
- **`hybrid`** - High accuracy + sentence timestamps
- **`whisper_only`** - Fast with word-level timestamps
- **`no_timestamps`** - Fast, text only

## Usage Examples

### Basic Video Transcription

```bash
# Step 1: Extract audio
~/.claude/tools/video_to_audio.py lecture.mp4
# Creates: lecture.mp3

# Step 2: Transcribe
~/.claude/tools/audio_transcription/main.py lecture.mp3
# Creates: lecture.json
```

### With Custom Transcription Mode

```bash
# Extract audio
~/.claude/tools/video_to_audio.py meeting.mov

# Transcribe with word-level timestamps
~/.claude/tools/audio_transcription/main.py meeting.mp3 --mode whisper_only
```

### High Quality Audio + Transcription

```bash
# Extract high-quality audio
~/.claude/tools/video_to_audio.py podcast.mp4 --quality high

# Transcribe with best accuracy
~/.claude/tools/audio_transcription/main.py podcast.mp3 --mode hybrid
```

### Custom Output Locations

```bash
# Extract to specific location
~/.claude/tools/video_to_audio.py video.mp4 --output ~/audio/video.mp3

# Transcribe to specific location
~/.claude/tools/audio_transcription/main.py ~/audio/video.mp3 \
  --output ~/transcripts/video.json
```

## Workflow Orchestration

When user requests video transcription:

1. **Identify video file** - Get path from user
2. **Extract audio** - Use `video_to_audio.py`
3. **Wait for completion** - Confirm audio file created
4. **Transcribe audio** - Use `audio_transcription/main.py`
5. **Return transcript** - Present JSON output to user

## Output Format

Final output is JSON with:
```json
{
  "source_file": "/path/to/video.mp3",
  "duration_seconds": 3425.5,
  "transcription_mode": "sliding_window",
  "transcript": "[00:00:00] Transcribed text...",
  "metadata": {
    "models_used": ["whisper-1", "gpt-4o-transcribe"],
    "chunks_processed": 28,
    "estimated_cost_usd": 0.85
  }
}
```

## Requirements

Both tools must be available:
- ✅ `~/.claude/tools/video_to_audio.py` (video → audio)
- ✅ `~/.claude/tools/audio_transcription/main.py` (audio → transcript)

System requirements:
- **ffmpeg** (for video conversion)
- **OpenAI API key** (for transcription)

## Tool Independence

**Important**: These tools are independent and composable:
- Each tool works standalone
- No dependencies between tools
- Pure functions with clear inputs/outputs
- Can be used separately or together

## Common Patterns

### Quick Transcription
```bash
# Default settings (MP3, sliding_window mode)
~/.claude/tools/video_to_audio.py video.mp4 && \
~/.claude/tools/audio_transcription/main.py video.mp3
```

### Batch Processing
```bash
# Process multiple videos
for video in ~/Videos/*.mp4; do
  ~/.claude/tools/video_to_audio.py "$video"
  audio="${video%.mp4}.mp3"
  ~/.claude/tools/audio_transcription/main.py "$audio"
done
```

### Cleanup After Transcription
```bash
# Extract, transcribe, then remove audio
~/.claude/tools/video_to_audio.py lecture.mp4
~/.claude/tools/audio_transcription/main.py lecture.mp3
rm lecture.mp3  # Keep only video and transcript
```

## Performance

**Total Time** (for 1-hour video):
- Audio extraction: ~6-12 minutes
- Transcription: ~10-15 minutes
- **Total**: ~16-27 minutes

**Cost** (for 1-hour video):
- Audio extraction: Free (local ffmpeg)
- Transcription: ~$0.36-$0.72 (depending on mode)

## Troubleshooting

### "ffmpeg not found"
Install ffmpeg: `brew install ffmpeg` (macOS)

### "OPENAI_API_KEY_DEFAULT not set"
Add to `~/.claude/.env`: `OPENAI_API_KEY_DEFAULT="sk-..."`

### Audio file too large
Use lower quality: `--quality low` when extracting audio

### Transcription too slow
Use faster mode: `--mode whisper_only` or `--mode no_timestamps`

## Related Documentation

- **Video to Audio**: `~/.claude/commands/video-to-audio.md`
- **Audio Transcription**: `~/.claude/commands/audio-transcription.md`

## Key Principles

1. **Two independent steps** - Extract audio, then transcribe
2. **Pure functions** - Each tool has clear input → output
3. **No dependencies** - Tools work standalone
4. **Composable** - Can chain or use separately
5. **Flexible** - Many options for quality and format
