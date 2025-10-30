---
name: extract-content-summarize
description: Extract structured insights and generate reflection questions from video/audio transcripts. Processes content through AI analysis to create comprehensive zettelkasten notes with summaries, key points, quotes, writing ideas, and reflection questions. USE WHEN user wants to process video/audio content into structured notes, extract insights from transcripts, create study materials from lectures, or build knowledge base entries from media content.
---

# Extract Content & Summarize

## When to Activate This Skill

- User wants to process video/audio content into structured notes
- User requests "summarize this video" or "extract insights from this podcast"
- Task involves creating zettelkasten notes from media content
- User wants reflection questions or study materials from content
- User provides transcript and wants comprehensive analysis
- User says "process this for my knowledge base"

## Overview

This skill orchestrates a complete workflow for transforming raw video/audio content into structured, actionable zettelkasten notes. It combines transcription, AI analysis, and document assembly to create comprehensive learning materials.

## Complete Workflow

### Step 1: Content Acquisition

**For YouTube Videos:**
```bash
yt-dlp -x --audio-format mp3 "https://youtube.com/watch?v=VIDEO_ID" -o "~/Downloads/%(title)s.%(ext)s"
```

**For Video Files:**
```bash
~/.claude/tools/video_to_audio.py video.mp4
# Creates: video.mp3
```

**For Audio Files:**
Use directly (skip to Step 2)

### Step 2: Transcription

```bash
~/.claude/tools/audio_transcription/main.py audio.mp3 --output tmp/transcript.json
```

**Output**: JSON file with timestamped transcript

**Note**: The `markdown_builder.py` can extract specific keys from JSON files, so we'll use `"key": "transcript"` to extract just the transcript text when assembling the final document.

### Step 3: AI Analysis (Parallel Processing)

Run both analyses simultaneously for efficiency:

**A. Content Summary & Extraction**
```bash
cd ~/.claude/tools
python openrouter_call.py \
  --model gemini-2.5-pro \
  --system '[{"type": "file", "path": "../skills/extract-content-summarize/prompts/content_extractor.md"}]' \
  --user '[
    {"type": "text", "content": "Analyze this transcript:\n\n"},
    {"type": "file", "path": "tmp/transcript.json"}
  ]' \
  --output tmp/summary_$(date +%Y%m%d-%H%M%S).md
```

**Extracts:**
- Metadata (title, author, date, duration)
- Executive summary
- Notable quotes with timestamps
- Key concepts and main ideas
- Important takeaways
- Potential writing topics
- Discussion points
- References and resources
- Suggested tags

**B. Reflection Questions**
```bash
cd ~/.claude/tools
python openrouter_call.py \
  --model gemini-2.5-pro \
  --system '[{"type": "file", "path": "../skills/extract-content-summarize/prompts/reflection_generator.md"}]' \
  --user '[
    {"type": "text", "content": "Generate reflection questions for this transcript:\n\n"},
    {"type": "file", "path": "tmp/transcript.json"}
  ]' \
  --output tmp/questions_$(date +%Y%m%d-%H%M%S).md
```

**Generates:**
- Comprehension & understanding questions
- Analysis & critical thinking questions
- Application & practice questions
- Synthesis & connection questions
- Evaluation & judgment questions
- Metacognition & self-reflection questions
- Action & implementation questions

### Step 4: Document Assembly

```bash
cd ~/.claude/tools
python markdown_builder.py \
  --title "Video Title" \
  --frontmatter '{
    "status": ["inbox"],
    "tags": ["video", "learning", "extracted-tags"],
    "template": ["zettelkasten"],
    "processed": false,
    "source_url": "https://youtube.com/watch?v=...",
    "source_type": "video",
    "duration": "45:30",
    "ai_threads": {
      "summary": "THREAD_ID_1",
      "questions": "THREAD_ID_2"
    },
    "created_date": "2025-10-29"
  }' \
  --body '[
    {"header": "Summary", "type": "file", "path": "tmp/summary_TIMESTAMP.md"},
    {"header": "Reflection Questions", "type": "file", "path": "tmp/questions_TIMESTAMP.md"},
    {"header": "Transcript", "type": "json", "path": "tmp/transcript.json", "keys": ["transcript"]}
  ]' \
  --output ~/Documents/caideiseach/inbox/2025-10-29_video-title.md
```

**Note**: The `"type": "json"` with `"keys": ["transcript"]` extracts only the transcript text from the JSON file, not the entire JSON object.

## Model Selection

**Recommended Models:**
- **Gemini 2.5 Pro** - 2M context window, excellent for long transcripts
- **Claude Sonnet 4.5** - 1M context window, superior analysis quality

**Usage:**
```bash
--model gemini-2.5-pro  # or gemini-pro (shortcut)
--model claude-sonnet-4.5  # or claude-sonnet (shortcut)
```

## Output Structure

Final zettelkasten note includes:

```markdown
---
status:
  - inbox
tags:
  - video
  - [extracted-tags]
template:
  - zettelkasten
processed: false
source_url: https://youtube.com/...
source_type: video
duration: "45:30"
ai_threads:
  summary: 20251029-230145-a3f2
  questions: 20251029-230147-b8e1
created_date: 2025-10-29
---

# Video Title

## Summary

[AI-generated executive summary with metadata, key concepts, takeaways, etc.]

## Reflection Questions

[AI-generated questions organized by category]

## Transcript

[Full timestamped transcript extracted from JSON]
```

## Thread ID Tracking

The `ai_threads` frontmatter field stores OpenRouter conversation thread IDs:
- **summary**: Thread ID from content extraction
- **questions**: Thread ID from reflection questions

**To continue conversations:**
```bash
python openrouter_call.py \
  --continue-thread 20251029-230145-a3f2 \
  --user "Can you expand on the concept of X?" \
  --output tmp/followup.md
```

## File Organization

**Working Files** (temporary):
- `~/.claude/tools/tmp/transcript.json` - Raw transcript
- `~/.claude/tools/tmp/summary_TIMESTAMP.md` - AI summary
- `~/.claude/tools/tmp/questions_TIMESTAMP.md` - AI questions
- `~/.claude/tools/tmp/threads/THREAD_ID.json` - Conversation history
- `~/.claude/tools/tmp/responses/THREAD_ID_response.json` - Raw API responses

**Final Output**:
- `~/Documents/caideiseach/inbox/YYYY-MM-DD_title.md` - Complete zettelkasten note

## Complete Example

```bash
# 1. Download YouTube video audio
yt-dlp -x --audio-format mp3 "https://youtube.com/watch?v=dQw4w9WgXcQ" -o "~/Downloads/%(title)s.%(ext)s"

# 2. Transcribe
~/.claude/tools/audio_transcription/main.py ~/Downloads/video.mp3 --output ~/.claude/tools/tmp/transcript.json

# 3. Extract content (in parallel with step 4)
cd ~/.claude/tools
python openrouter_call.py \
  --model gemini-pro \
  --system '[{"type": "file", "path": "../skills/extract-content-summarize/prompts/content_extractor.md"}]' \
  --user '[{"type": "text", "content": "Analyze:\n\n"}, {"type": "file", "path": "tmp/transcript.json"}]' \
  --output tmp/summary_20251029.md

# 4. Generate questions (in parallel with step 3)
python openrouter_call.py \
  --model gemini-pro \
  --system '[{"type": "file", "path": "../skills/extract-content-summarize/prompts/reflection_generator.md"}]' \
  --user '[{"type": "text", "content": "Questions for:\n\n"}, {"type": "file", "path": "tmp/transcript.json"}]' \
  --output tmp/questions_20251029.md

# 5. Assemble final document
python markdown_builder.py \
  --title "Rick Astley - Never Gonna Give You Up" \
  --frontmatter '{
    "status": ["inbox"],
    "tags": ["music", "video", "80s"],
    "template": ["zettelkasten"],
    "processed": false,
    "source_url": "https://youtube.com/watch?v=dQw4w9WgXcQ",
    "ai_threads": {"summary": "20251029-230145-a3f2", "questions": "20251029-230147-b8e1"}
  }' \
  --body '[
    {"header": "Summary", "type": "file", "path": "tmp/summary_20251029.md"},
    {"header": "Reflection Questions", "type": "file", "path": "tmp/questions_20251029.md"},
    {"header": "Transcript", "type": "file", "path": "tmp/transcript.json", "key": "transcript"}
  ]' \
  --output ~/Documents/caideiseach/inbox/2025-10-29_never-gonna-give-you-up.md
```

## Tool Dependencies

Required tools (all available):
- ✅ `yt-dlp` - YouTube download (install: `brew install yt-dlp`)
- ✅ `~/.claude/tools/video_to_audio.py` - Video → audio conversion
- ✅ `~/.claude/tools/audio_transcription/main.py` - Audio → transcript
- ✅ `~/.claude/tools/openrouter_call.py` - AI analysis
- ✅ `~/.claude/tools/markdown_builder.py` - Document assembly

System requirements:
- **ffmpeg** (for video conversion)
- **OpenAI API key** (for transcription)
- **OpenRouter API key** (for AI analysis)

## Environment Variables

```bash
# Required
export OPENAI_API_KEY_DEFAULT="sk-..."  # For transcription
export OPENROUTER_API_KEY="sk-..."      # For AI analysis
```

## Performance & Cost

**For 1-hour video:**
- Audio extraction: ~6-12 minutes (free, local)
- Transcription: ~10-15 minutes (~$0.36-$0.72)
- AI analysis (both): ~2-5 minutes (~$0.10-$0.30)
- Document assembly: <1 second (free, local)
- **Total time**: ~18-32 minutes
- **Total cost**: ~$0.46-$1.02

## Customization

### Custom Prompts

Edit the system prompts to change analysis focus:
- `prompts/content_extractor.md` - Modify what gets extracted
- `prompts/reflection_generator.md` - Change question types/categories

### Custom Output Format

Modify the `markdown_builder.py` call to:
- Add/remove sections
- Change frontmatter fields
- Adjust document structure
- Include additional metadata

### Different Models

Try different models for different needs:
- **Gemini Flash** - Faster, cheaper, good for simple content
- **Gemini Pro** - Best for long transcripts (2M context)
- **Claude Sonnet** - Superior analysis quality
- **Claude Haiku** - Fastest, cheapest, good for short content

## Troubleshooting

### "yt-dlp not found"
```bash
brew install yt-dlp
```

### "OPENROUTER_API_KEY not set"
```bash
export OPENROUTER_API_KEY='your-key-here'
# Add to ~/.zshrc or ~/.bashrc for persistence
```

### Transcript too long for model
Use Gemini 2.5 Pro (2M context) or split into chunks

### AI analysis too expensive
Use cheaper models (gemini-flash, claude-haiku) or reduce transcript length

## Related Skills

- **video-transcription** - Just transcription without AI analysis
- **PAI** - Personal AI Infrastructure core skill

## Key Principles

1. **Composable Tools** - Each step is independent and reusable
2. **Parallel Processing** - Run AI analyses simultaneously
3. **Thread Tracking** - Save conversation IDs for follow-up
4. **Structured Output** - Consistent zettelkasten format
5. **Cost Awareness** - Choose appropriate models for task
6. **Quality Focus** - Comprehensive analysis over speed
