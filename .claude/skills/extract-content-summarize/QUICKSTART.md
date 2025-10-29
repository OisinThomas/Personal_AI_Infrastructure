# Extract Content & Summarize - Quick Start Guide

## One-Command Workflow (Copy & Paste)

### For YouTube Videos

```bash
# 1. Set your video URL
VIDEO_URL="https://youtube.com/watch?v=VIDEO_ID"

# 2. Download audio
yt-dlp -x --audio-format mp3 "$VIDEO_URL" -o "~/Downloads/%(title)s.%(ext)s"

# 3. Get the filename (adjust path if needed)
AUDIO_FILE="~/Downloads/your-video-title.mp3"

# 4. Transcribe
~/.claude/tools/audio_transcription/main.py "$AUDIO_FILE" --output ~/.claude/tools/tmp/transcript.json

# 5. Run AI analysis (both in parallel)
cd ~/.claude/tools

# Summary
python openrouter_call.py \
  --model gemini-pro \
  --system '[{"type": "file", "path": "../skills/extract-content-summarize/prompts/content_extractor.md"}]' \
  --user '[{"type": "text", "content": "Analyze this transcript:\n\n"}, {"type": "file", "path": "tmp/transcript.json"}]' \
  --output tmp/summary_$(date +%Y%m%d-%H%M%S).md &

# Questions (runs in parallel)
python openrouter_call.py \
  --model gemini-pro \
  --system '[{"type": "file", "path": "../skills/extract-content-summarize/prompts/reflection_generator.md"}]' \
  --user '[{"type": "text", "content": "Generate reflection questions for this transcript:\n\n"}, {"type": "file", "path": "tmp/transcript.json"}]' \
  --output tmp/questions_$(date +%Y%m%d-%H%M%S).md &

# Wait for both to complete
wait

# 6. Get thread IDs from the output above, then assemble
SUMMARY_FILE="tmp/summary_TIMESTAMP.md"  # Replace with actual filename
QUESTIONS_FILE="tmp/questions_TIMESTAMP.md"  # Replace with actual filename
THREAD_ID_SUMMARY="20251029-230145-a3f2"  # Replace with actual thread ID
THREAD_ID_QUESTIONS="20251029-230147-b8e1"  # Replace with actual thread ID

python markdown_builder.py \
  --title "Video Title Here" \
  --frontmatter "{
    \"status\": [\"inbox\"],
    \"tags\": [\"video\", \"learning\"],
    \"template\": [\"zettelkasten\"],
    \"processed\": false,
    \"source_url\": \"$VIDEO_URL\",
    \"ai_threads\": {
      \"summary\": \"$THREAD_ID_SUMMARY\",
      \"questions\": \"$THREAD_ID_QUESTIONS\"
    }
  }" \
  --body "[
    {\"header\": \"Summary\", \"type\": \"file\", \"path\": \"$SUMMARY_FILE\"},
    {\"header\": \"Reflection Questions\", \"type\": \"file\", \"path\": \"$QUESTIONS_FILE\"},
    {\"header\": \"Transcript\", \"type\": \"file\", \"path\": \"tmp/transcript.json\"}
  ]" \
  --output ~/Documents/caideiseach/inbox/$(date +%Y-%m-%d)_video-title.md
```

### For Local Video Files

```bash
# 1. Extract audio
~/.claude/tools/video_to_audio.py /path/to/video.mp4

# 2. Continue from step 4 above (transcribe)
```

### For Audio Files

```bash
# Start from step 4 (transcribe) - skip audio extraction
```

## Simplified Version (Step by Step)

### Step 1: Get Audio
```bash
# YouTube
yt-dlp -x --audio-format mp3 "URL" -o "~/Downloads/%(title)s.%(ext)s"

# OR Video file
~/.claude/tools/video_to_audio.py video.mp4
```

### Step 2: Transcribe
```bash
~/.claude/tools/audio_transcription/main.py audio.mp3 --output ~/.claude/tools/tmp/transcript.json
```

### Step 3: AI Analysis
```bash
cd ~/.claude/tools

# Summary
python openrouter_call.py \
  --model gemini-pro \
  --system '[{"type": "file", "path": "../skills/extract-content-summarize/prompts/content_extractor.md"}]' \
  --user '[{"type": "text", "content": "Analyze:\n\n"}, {"type": "file", "path": "tmp/transcript.json"}]' \
  --output tmp/summary.md

# Questions
python openrouter_call.py \
  --model gemini-pro \
  --system '[{"type": "file", "path": "../skills/extract-content-summarize/prompts/reflection_generator.md"}]' \
  --user '[{"type": "text", "content": "Questions:\n\n"}, {"type": "file", "path": "tmp/transcript.json"}]' \
  --output tmp/questions.md
```

### Step 4: Assemble Document
```bash
cd ~/.claude/tools

python markdown_builder.py \
  --title "Your Title" \
  --frontmatter '{"status": ["inbox"], "tags": ["video"], "template": ["zettelkasten"], "processed": false}' \
  --body '[
    {"header": "Summary", "type": "file", "path": "tmp/summary.md"},
    {"header": "Questions", "type": "file", "path": "tmp/questions.md"},
    {"header": "Transcript", "type": "file", "path": "tmp/transcript.json"}
  ]' \
  --output ~/Documents/caideiseach/inbox/note.md
```

## Model Options

**Fast & Cheap:**
```bash
--model gemini-flash  # or claude-haiku
```

**Best Quality:**
```bash
--model gemini-pro  # 2M context, great for long content
--model claude-sonnet  # Superior analysis quality
```

## Common Issues

### "yt-dlp not found"
```bash
brew install yt-dlp
```

### "OPENROUTER_API_KEY not set"
```bash
export OPENROUTER_API_KEY='your-key-here'
echo 'export OPENROUTER_API_KEY="your-key-here"' >> ~/.zshrc
```

### "OPENAI_API_KEY_DEFAULT not set"
```bash
export OPENAI_API_KEY_DEFAULT='sk-...'
echo 'export OPENAI_API_KEY_DEFAULT="sk-..."' >> ~/.zshrc
```

## Tips

1. **Run analyses in parallel** - Use `&` and `wait` to run summary and questions simultaneously
2. **Save thread IDs** - Copy them from output to include in frontmatter
3. **Use timestamps** - `$(date +%Y%m%d-%H%M%S)` for unique filenames
4. **Check tmp/ folder** - All intermediate files are saved there
5. **Continue conversations** - Use `--continue-thread THREAD_ID` to ask follow-up questions

## File Locations

- **Transcripts**: `~/.claude/tools/tmp/transcript.json`
- **Summaries**: `~/.claude/tools/tmp/summary_*.md`
- **Questions**: `~/.claude/tools/tmp/questions_*.md`
- **Threads**: `~/.claude/tools/tmp/threads/*.json`
- **API Responses**: `~/.claude/tools/tmp/responses/*.json`
- **Final Notes**: `~/Documents/caideiseach/inbox/*.md`

## Cost Estimate

For 1-hour video:
- Transcription: ~$0.36-$0.72
- AI Analysis: ~$0.10-$0.30
- **Total**: ~$0.46-$1.02

## Next Steps

After creating the note:
1. Review the summary and questions
2. Move from inbox to appropriate folder
3. Add additional tags
4. Link to related notes
5. Use thread IDs to ask follow-up questions
