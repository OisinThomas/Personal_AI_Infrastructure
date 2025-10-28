## Video to Audio Converter

Extract audio from video files using ffmpeg. Pure conversion tool with no dependencies.

## Quick Usage

```bash
# Basic usage - converts to MP3
~/.claude/tools/video_to_audio.py video.mp4
# Output: video.mp3 (next to video.mp4)

# Custom output location
~/.claude/tools/video_to_audio.py video.mp4 --output ~/audio/video.mp3

# Different format
~/.claude/tools/video_to_audio.py video.mov --format wav

# High quality
~/.claude/tools/video_to_audio.py lecture.mp4 --quality high
```

## Installation

### Install ffmpeg

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

No Python dependencies needed - uses only standard library.

## Supported Formats

### Input (Video)
- ✅ **MP4** - Most common
- ✅ **MOV** - Apple/QuickTime
- ✅ **AVI** - Windows video
- ✅ **MKV** - Matroska
- ✅ **WebM** - Web video
- ✅ **FLV** - Flash video
- ✅ **WMV** - Windows Media
- ✅ **M4V** - iTunes video

### Output (Audio)
- ✅ **MP3** - Universal (default)
- ✅ **WAV** - Lossless
- ✅ **M4A** - Apple/AAC
- ✅ **FLAC** - Lossless compression
- ✅ **OGG** - Vorbis

## Usage Examples

### Basic Conversion

```bash
# Convert to MP3 (default)
~/.claude/tools/video_to_audio.py lecture.mp4
# Output: lecture.mp3
```

### Custom Output Path

```bash
# Specify output location
~/.claude/tools/video_to_audio.py video.mp4 \
  --output ~/Documents/audio.mp3
```

### Different Formats

```bash
# Convert to WAV (lossless)
~/.claude/tools/video_to_audio.py video.mp4 --format wav

# Convert to M4A
~/.claude/tools/video_to_audio.py video.mov --format m4a

# Convert to FLAC (lossless compression)
~/.claude/tools/video_to_audio.py video.mkv --format flac
```

### Quality Settings

```bash
# High quality (320kbps for MP3/M4A/OGG)
~/.claude/tools/video_to_audio.py podcast.mp4 --quality high

# Medium quality (192kbps - default)
~/.claude/tools/video_to_audio.py lecture.mp4 --quality medium

# Low quality (128kbps - smaller file)
~/.claude/tools/video_to_audio.py meeting.mp4 --quality low
```

### Batch Processing

```bash
# Convert all MP4 files in a directory
for video in ~/Videos/*.mp4; do
  ~/.claude/tools/video_to_audio.py "$video"
done

# Convert to specific directory
for video in ~/Videos/*.mp4; do
  ~/.claude/tools/video_to_audio.py "$video" \
    --output ~/Audio/$(basename "$video" .mp4).mp3
done
```

## Quality Presets

| Quality | Bitrate | File Size (1hr) | Use Case |
|---------|---------|-----------------|----------|
| `high` | 320kbps | ~140 MB | Music, high-fidelity |
| `medium` | 192kbps | ~85 MB | Podcasts, lectures (default) |
| `low` | 128kbps | ~56 MB | Voice-only, minimize size |

*Quality settings only apply to lossy formats (MP3, M4A, OGG). WAV and FLAC are always lossless.*

## Command Reference

```bash
~/.claude/tools/video_to_audio.py [OPTIONS] VIDEO_FILE

Arguments:
  VIDEO_FILE              Path to video file

Options:
  -o, --output PATH       Output audio file path
  -f, --format FORMAT     Output format: mp3, wav, m4a, flac, ogg
  -q, --quality QUALITY   Quality: high, medium, low
  -h, --help             Show help message
```

## Integration with Audio Transcription

Chain with audio transcription for complete video → transcript workflow:

```bash
# Step 1: Extract audio
~/.claude/tools/video_to_audio.py lecture.mp4

# Step 2: Transcribe audio
~/.claude/tools/audio_transcription/main.py lecture.mp3

# Result: lecture.json with full transcript
```

Or use the video-transcription skill for automatic orchestration.

## Output Behavior

**Default output location**: Same directory as input video
**Default format**: MP3
**Default quality**: Medium (192kbps)
**Overwrite**: Yes (uses ffmpeg `-y` flag)

## Troubleshooting

### "ffmpeg not found"

```bash
# Install ffmpeg
brew install ffmpeg  # macOS
sudo apt-get install ffmpeg  # Linux

# Verify
ffmpeg -version
```

### "Unsupported video format"

The tool supports: MP4, MOV, AVI, MKV, WebM, FLV, WMV, M4V

Convert your video first:
```bash
ffmpeg -i input.3gp -c:v libx264 output.mp4
```

### "Conversion failed"

Check:
1. Video file is not corrupted
2. Sufficient disk space
3. Write permissions in output directory
4. ffmpeg is properly installed

### Large File Sizes

For smaller files:
```bash
# Use low quality
~/.claude/tools/video_to_audio.py video.mp4 --quality low

# Or use OGG format (better compression)
~/.claude/tools/video_to_audio.py video.mp4 --format ogg --quality low
```

## When to Use

### ✅ Perfect For

- Extracting audio from video lectures
- Converting video podcasts to audio
- Creating audio files for transcription
- Archiving audio from video content
- Reducing file sizes (video → audio)
- Preparing files for audio processing

### ⚠️ Limitations

- Audio-only output (no video)
- Requires ffmpeg installation
- No audio enhancement/filtering
- No batch mode built-in (use shell loops)

## Advanced Usage

### Custom Codec Settings

For advanced users, you can use ffmpeg directly:

```bash
# Custom bitrate
ffmpeg -i video.mp4 -vn -acodec libmp3lame -b:a 256k audio.mp3

# Specific sample rate
ffmpeg -i video.mp4 -vn -ar 44100 audio.wav

# Stereo to mono
ffmpeg -i video.mp4 -vn -ac 1 audio.mp3
```

### Extract Specific Time Range

```bash
# Extract 30 seconds starting at 1 minute
ffmpeg -i video.mp4 -ss 00:01:00 -t 00:00:30 -vn audio.mp3
```

### Preserve Metadata

```bash
# Keep video metadata in audio file
ffmpeg -i video.mp4 -vn -acodec copy -map_metadata 0 audio.m4a
```

## Performance

**Conversion Speed**: Typically 5-10x faster than real-time
- 1 hour video → ~6-12 minutes to convert
- Depends on: CPU speed, codec, quality settings

**Disk Space**:
- MP3 (192kbps): ~85 MB per hour
- WAV (lossless): ~600 MB per hour
- FLAC (lossless): ~300 MB per hour

## See Also

- [Audio Transcription](./audio-transcription.md) - Transcribe audio files
- [FFmpeg Documentation](https://ffmpeg.org/documentation.html)
- Video Transcription Skill - Orchestrates video → audio → transcript

## Pure Function Design

This tool is designed as a pure function:
- **Input**: Video file path
- **Output**: Audio file path
- **Side effect**: Creates audio file (intentional)
- **No dependencies**: Works standalone
- **No state**: Each conversion is independent
- **Composable**: Can be chained with other tools
