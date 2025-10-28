# Markdown Builder

Build markdown files from multiple sources with structured frontmatter. **Solves the token limit problem** by referencing large files instead of holding everything in context.

## Quick Usage

```bash
# Simple inline content
~/.claude/tools/markdown_builder.py \
  --title "My Document" \
  --frontmatter '{"date": "2025-01-26"}' \
  --body '[{"header": "Intro", "type": "text", "content": "Hello!"}]' \
  --output doc.md

# Reference large files (avoids token limits!)
~/.claude/tools/markdown_builder.py \
  --title "Podcast Episode" \
  --frontmatter '{"guest": {"type": "file", "path": "guest.txt"}}' \
  --body '[{"header": "Transcript", "type": "file", "path": "transcript.md"}]' \
  --base-path /path/to/files \
  --output episode.md

# Extract from JSON
~/.claude/tools/markdown_builder.py \
  --title "Report" \
  --frontmatter '{"author": {"type": "json", "path": "meta.json", "key": "author.name"}}' \
  --body '[{"header": "Stats", "type": "json", "path": "data.json", "keys": ["count", "total"]}]' \
  --output report.md
```

## Why Use This Tool?

### The Token Limit Problem

In multi-step workflows (like podcast transcription), intermediate files can be HUGE:
- Transcript: 100KB+ markdown
- Metadata: JSON files
- Summaries: Generated text

**Problem**: Passing these through LLM context → token limits
**Solution**: Reference files by path → machine reads them directly

## Installation

**None needed!** Pure Python stdlib, no dependencies.

```bash
# Just make it executable (already done)
chmod +x ~/.claude/tools/markdown_builder.py

# Verify it works
~/.claude/tools/markdown_builder.py --help
```

## Core Concepts: Three Ways to Provide Content

### Frontmatter Value Types

#### 1. Plain Values
```json
{
  "date": "2025-01-26",
  "tags": ["podcast", "tech"],
  "processed": false
}
```

**WHEN to use**: Simple, static metadata that fits inline
**WHY**: Easy to write, no external files needed
**Examples**: Dates, tags, booleans, short strings

#### 2. File References
```json
{
  "guest": {
    "type": "file",
    "path": "guest_bio.txt"
  }
}
```

**WHEN to use**: Content exists as a file or is too large for command line
**WHY**: Avoids token limits, references existing files
**Examples**: Guest bios, descriptions, summaries
**Result**: File content becomes the frontmatter value

#### 3. JSON Extraction
```json
{
  "duration": {
    "type": "json",
    "path": "metadata.json",
    "key": "duration"
  },
  "guest_name": {
    "type": "json",
    "path": "metadata.json",
    "key": "guest.name"
  }
}
```

**WHEN to use**: Have structured data, need specific values
**WHY**: Extract without duplication, maintain single source of truth
**Examples**: API responses, transcription metadata
**Supports**: Dot notation for nested keys (`guest.name`, `stats.downloads`)

### Body Section Types

#### 1. Text Sections
```json
{
  "header": "Introduction",
  "type": "text",
  "content": "This is a short introduction paragraph..."
}
```

**WHEN to use**: Short content that fits inline
**WHY**: Simple, no external files needed
**Examples**: Introductions, short notes, instructions

#### 2. File Sections
```json
{
  "header": "Transcript",
  "type": "file",
  "path": "transcript.md"
}
```

**WHEN to use**: Large content, avoid token limits
**WHY**: Machine reads directly, no LLM context used
**Examples**: Transcripts, long articles, generated content
**Result**: Creates H2 header + full file content

#### 3. JSON Sections
```json
{
  "header": "Statistics",
  "type": "json",
  "path": "metadata.json",
  "keys": ["downloads", "rating", "duration"]
}
```

**WHEN to use**: Display structured data cleanly
**WHY**: Formats as readable YAML-style output
**Examples**: Stats, metadata display, data tables
**Supports**: Multiple keys, nested paths (`stats.downloads`)

## Real-World Examples

### Example 1: Simple Blog Post

```bash
~/.claude/tools/markdown_builder.py \
  --title "Getting Started with AI" \
  --frontmatter '{
    "date": "2025-01-26",
    "author": "John Doe",
    "tags": ["ai", "tutorial", "beginners"]
  }' \
  --body '[
    {
      "header": "Introduction",
      "type": "text",
      "content": "AI is transforming how we work..."
    },
    {
      "header": "Key Concepts",
      "type": "text",
      "content": "The three main concepts are..."
    }
  ]' \
  --output blog.md
```

**WHY this approach**:
- All content is short → fits inline
- No external files needed
- Simple, self-contained

**Output**:
```markdown
---
date: 2025-01-26
author: John Doe
tags:
  - ai
  - tutorial
  - beginners
---

# Getting Started with AI

## Introduction

AI is transforming how we work...

## Key Concepts

The three main concepts are...
```

### Example 2: Podcast Episode Workflow (Your Use Case!)

**Scenario**: Downloaded podcast, transcribed it, generated metadata. Now need final markdown.

**Files created**:
- `transcript.md` - 150KB transcript (HUGE!)
- `metadata.json` - Episode info
- `summary.md` - AI-generated summary

```bash
~/.claude/tools/markdown_builder.py \
  --title "Lenny's Podcast - Building Products Users Love" \
  --frontmatter '{
    "date": "2025-01-26",
    "podcast": "Lennys Podcast",
    "episode": 142,
    "guest": {"type": "json", "path": "metadata.json", "key": "guest.name"},
    "duration": {"type": "json", "path": "metadata.json", "key": "duration"},
    "tags": ["podcast", "product", "management"],
    "processed": false
  }' \
  --body '[
    {
      "header": "Summary",
      "type": "file",
      "path": "summary.md"
    },
    {
      "header": "Key Takeaways",
      "type": "text",
      "content": "1. Focus on user pain points\n2. Ship early and iterate\n3. Measure what matters"
    },
    {
      "header": "Guest Information",
      "type": "json",
      "path": "metadata.json",
      "keys": ["guest.name", "guest.company", "guest.role"]
    },
    {
      "header": "Transcript",
      "type": "file",
      "path": "transcript.md"
    }
  ]' \
  --base-path /path/to/podcast/files \
  --output ~/Documents/caideiseach/inbox/20250126-lennys-podcast-ep142.md
```

**WHY this approach**:
- Transcript is 150KB → **file reference avoids token limits**
- Metadata in JSON → **extract values, don't duplicate**
- Summary exists → **reference it, don't regenerate**
- Mixed inline/file → **use best approach for each section**

**What gets created**:
```markdown
---
date: 2025-01-26
podcast: Lennys Podcast
episode: 142
guest: Jane Smith
duration: 3600
tags:
  - podcast
  - product
  - management
processed: false
---

# Lenny's Podcast - Building Products Users Love

## Summary

[Full summary from summary.md file]

## Key Takeaways

1. Focus on user pain points
2. Ship early and iterate
3. Measure what matters

## Guest Information

name: Jane Smith
company: TechCorp
role: VP of Product

## Transcript

[Full 150KB transcript from transcript.md]
```

### Example 3: Research Report with Mixed Sources

```bash
~/.claude/tools/markdown_builder.py \
  --title "Q4 2024 Analysis" \
  --frontmatter '{
    "date": {"type": "json", "path": "report_data.json", "key": "generated_date"},
    "author": "Analysis Team",
    "quarter": "Q4 2024"
  }' \
  --body '[
    {
      "header": "Executive Summary",
      "type": "file",
      "path": "executive_summary.md"
    },
    {
      "header": "Key Metrics",
      "type": "json",
      "path": "report_data.json",
      "keys": ["metrics.revenue", "metrics.growth", "metrics.users"]
    },
    {
      "header": "Methodology",
      "type": "text",
      "content": "Data collected from three primary sources..."
    },
    {
      "header": "Detailed Analysis",
      "type": "file",
      "path": "detailed_analysis.md"
    }
  ]' \
  --output quarterly_report.md
```

**WHY this approach**:
- Mix of inline, file, and JSON sources
- Date from JSON → **single source of truth**
- Long sections as files → **avoid bloat**
- Short sections inline → **keep simple**

### Example 4: Handling Missing Files

```bash
~/.claude/tools/markdown_builder.py \
  --title "Test Document" \
  --frontmatter '{"author": {"type": "file", "path": "missing.txt"}}' \
  --body '[{"header": "Content", "type": "file", "path": "also_missing.md"}]' \
  --output test.md
```

**Output shows errors FIRST**:
```
Building markdown document...
  Title: Test Document
  Frontmatter keys: 1
  Body sections: 1
  Base path: /current/dir

============================================================
⚠️  ERRORS FOUND - Document created with placeholders:
============================================================
  ✗ File not found: /current/dir/missing.txt
  ✗ File not found: /current/dir/also_missing.md
============================================================

✓ Created: test.md (with placeholders)
  Size: 156 bytes

⚠️  Fix the 2 error(s) above and rebuild.
```

**WHY this matters**:
- Errors printed **FIRST and prominently** → impossible to miss
- Document still created → **see what's missing**
- Placeholders in output → **know what to fix**
- Exit code 1 → **scripts can detect failure**

**Document created**:
```markdown
---
author: "[FILE NOT FOUND: /current/dir/missing.txt]"
---

# Test Document

## Content

[FILE NOT FOUND: /current/dir/also_missing.md]
```

## Complete Podcast Workflow

Step-by-step workflow showing how markdown_builder fits into a multi-step pipeline:

```bash
# Step 1: Download podcast audio
# (Using your podcast download tool/skill)
podcast_url="https://..."
output_file="episode_142.mp3"

# Step 2: Transcribe audio → transcript.md (HUGE FILE!)
~/.claude/tools/audio_transcription/main.py episode_142.mp3 \
  --mode sliding_window \
  --output transcription_output.json

# Extract transcript text to markdown
jq -r '.transcript' transcription_output.json > transcript.md
# Result: 150KB transcript file

# Step 3: Extract metadata → metadata.json
jq '{
  guest: {name: .guest_name, company: .guest_company, role: .guest_role},
  duration: .duration,
  published: .published_date
}' transcription_output.json > metadata.json

# Step 4: Generate summary (via LLM)
# summary.md created by AI skill

# Step 5: Build final markdown with markdown_builder
~/.claude/tools/markdown_builder.py \
  --title "Lenny's Podcast Ep 142" \
  --frontmatter '{
    "date": "2025-01-26",
    "podcast": "Lennys Podcast",
    "guest": {"type": "json", "path": "metadata.json", "key": "guest.name"},
    "duration": {"type": "json", "path": "metadata.json", "key": "duration"}
  }' \
  --body '[
    {"header": "Summary", "type": "file", "path": "summary.md"},
    {"header": "Transcript", "type": "file", "path": "transcript.md"}
  ]' \
  --output ~/Documents/caideiseach/inbox/episode_142.md

# Step 6: Cleanup intermediate files
rm episode_142.mp3 transcription_output.json
# Keep transcript.md, metadata.json for reference
```

**WHY this workflow works**:
- Each step creates **small, focused files**
- Transcript stays as file → **never enters LLM context**
- Metadata extracted once → **referenced multiple times**
- Final markdown is **composable from sources**
- No token limit issues → **machine handles I/O**

## Command Reference

```bash
~/.claude/tools/markdown_builder.py [OPTIONS]

Required Arguments:
  -t, --title TITLE           Document title (becomes H1 header)
  -o, --output PATH           Output file path (absolute, relative, or ~/)

Optional Arguments:
  -f, --frontmatter JSON      Frontmatter as JSON object (default: {})
  -b, --body JSON             Body sections as JSON array (default: [])
  --base-path PATH            Base path for resolving file references
                              (default: current working directory)
  -h, --help                  Show help message

Frontmatter Value Types:
  Plain:    "key": "value"
  File:     "key": {"type": "file", "path": "file.txt"}
  JSON:     "key": {"type": "json", "path": "data.json", "key": "path.to.key"}

Body Section Types:
  Text:     {"header": "Title", "type": "text", "content": "..."}
  File:     {"header": "Title", "type": "file", "path": "file.md"}
  JSON:     {"header": "Title", "type": "json", "path": "data.json", "keys": ["key1", "key2"]}
```

## Path Handling

### Relative Paths
```bash
# Relative to current directory
--output ./output.md

# Relative to base-path for file references
--base-path /path/to/files
--frontmatter '{"guest": {"type": "file", "path": "guest.txt"}}'
# Resolves to: /path/to/files/guest.txt
```

### Absolute Paths
```bash
# Full path
--output /Users/name/Documents/file.md

# Home directory expansion
--output ~/Documents/caideiseach/inbox/file.md
```

### Best Practice
- Use **absolute path** for `--output` → clear destination
- Use **relative paths** in frontmatter/body → portable
- Set `--base-path` to reference directory → clean JSON

## JSON Key Extraction

Supports dot notation for nested keys:

```json
// metadata.json
{
  "episode": {
    "title": "Episode 42",
    "guest": {
      "name": "John Doe",
      "company": "TechCorp"
    },
    "stats": {
      "downloads": 5000,
      "rating": 4.8
    }
  }
}
```

```bash
# Extract nested values
--frontmatter '{
  "guest_name": {"type": "json", "path": "metadata.json", "key": "episode.guest.name"},
  "downloads": {"type": "json", "path": "metadata.json", "key": "episode.stats.downloads"}
}'
```

## Troubleshooting

### JSON Parsing Errors

**Error**: `Invalid JSON in --frontmatter`

**Solution**: Escape quotes properly or use heredoc
```bash
# BAD - shell interprets quotes wrong
--frontmatter '{"key": "value with "quotes"}'

# GOOD - escape inner quotes
--frontmatter '{"key": "value with \"quotes\""}'

# BETTER - use heredoc for complex JSON
markdown_builder.py \
  --title "Title" \
  --frontmatter "$(cat <<'EOF'
{
  "key": "value with \"quotes\"",
  "nested": {"more": "data"}
}
EOF
)" \
  --output out.md
```

### File Not Found Errors

Errors print FIRST with clear markers:
```
============================================================
⚠️  ERRORS FOUND - Document created with placeholders:
============================================================
  ✗ File not found: /path/to/missing.txt
============================================================
```

**Check**:
1. File exists: `ls -la /path/to/file`
2. Path is correct (relative to --base-path)
3. Permissions: readable by user

### JSON Key Errors

**Error**: `Key not found in metadata.json: KeyError('guest')`

**Solution**: Verify key path with jq
```bash
# Check key exists
jq '.guest.name' metadata.json

# List all keys
jq 'keys' metadata.json

# Navigate nested structure
jq '.episode | keys' metadata.json
```

### Empty Output

**Check**:
1. Title provided: `--title "Title"`
2. Body has sections: `--body '[{...}]'`
3. Frontmatter is valid: `--frontmatter '{}'`

## When to Use

### ✅ Perfect For

- **Multi-step workflows** with intermediate files
- **Large content** that would exceed token limits
- **Avoiding LLM context bloat** in AI pipelines
- **Structured data extraction** from JSON/APIs
- **Composable pipelines** with file I/O
- **Podcast transcription workflows**
- **Report generation** from multiple sources
- **Knowledge base creation** from existing files

### ⚠️ Not Ideal For

- Single-source documents (just write markdown directly)
- Real-time streaming (tool is file-based)
- Complex markdown generation (use templates instead)
- Interactive editing (use markdown editor)

## Integration Examples

### With Audio Transcription
```bash
# Transcribe → metadata + transcript
~/.claude/tools/audio_transcription/main.py audio.mp3

# Build markdown from outputs
~/.claude/tools/markdown_builder.py \
  --title "Transcription" \
  --body '[{"header": "Transcript", "type": "file", "path": "audio.json"}]' \
  --output transcript.md
```

### With PDF Conversion
```bash
# Convert PDF → markdown
~/.claude/tools/pdf_to_markdown.py document.pdf

# Add frontmatter and structure
~/.claude/tools/markdown_builder.py \
  --title "Research Paper" \
  --frontmatter '{"source": "document.pdf", "date": "2025-01-26"}' \
  --body '[{"header": "Content", "type": "file", "path": "pdf_output/document.md"}]' \
  --output structured_document.md
```

### In Shell Scripts
```bash
#!/bin/bash
# Automated report generation

# Collect data
./fetch_metrics.sh > metrics.json
./generate_summary.py > summary.md

# Build report
~/.claude/tools/markdown_builder.py \
  --title "Weekly Report - $(date +%Y-%m-%d)" \
  --frontmatter "{\"generated\": \"$(date -Iseconds)\"}" \
  --body '[
    {"header": "Summary", "type": "file", "path": "summary.md"},
    {"header": "Metrics", "type": "json", "path": "metrics.json", "keys": ["count", "total"]}
  ]' \
  --output "reports/weekly-$(date +%Y%m%d).md"
```

## Performance

**Speed**: Instant (file I/O only, no processing)
- 100KB file: < 10ms
- 1MB file: < 50ms
- No network calls
- No AI/LLM processing

**Memory**: Minimal (streams files, doesn't load all into RAM)

**Disk Space**: Output size = sum of input files

## Design Philosophy

**Pure Function**: Input files → Output file
- No state
- No side effects (except creating output file)
- Deterministic (same inputs → same output)
- Composable (can chain with other tools)

**Separation of Concerns**:
- Data collection: Other tools
- Data processing: Other tools
- Document assembly: **This tool**

**Why This Matters**:
- Each tool does one thing well
- Pipelines are clear and debuggable
- No token limit issues
- Scales to huge files

## See Also

- [Audio Transcription](./audio-transcription.md) - Transcribe audio files
- [PDF to Markdown](./pdf-to-markdown.md) - Convert PDFs to markdown
- [Video to Audio](./video-to-audio.md) - Extract audio from video
