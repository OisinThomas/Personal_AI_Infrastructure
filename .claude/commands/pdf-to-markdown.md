# PDF to Markdown Command

## Quick Usage
```bash
# Convert a PDF to markdown (default: Gemini 2.5 Flash, output next to PDF)
~/.claude/tools/pdf_to_markdown.py ~/Documents/report.pdf

# Use a different model
~/.claude/tools/pdf_to_markdown.py ~/Documents/report.pdf --model gemini-pro

# Specify custom output directory
~/.claude/tools/pdf_to_markdown.py ~/Documents/report.pdf --output-dir ~/Documents/markdown

# Use more workers for faster processing
~/.claude/tools/pdf_to_markdown.py ~/Documents/report.pdf --workers 20

# Retry failed pages (auto-detects from error markers in existing .md)
~/.claude/tools/pdf_to_markdown.py ~/Documents/report.pdf --retry

# Retry specific pages only
~/.claude/tools/pdf_to_markdown.py ~/Documents/report.pdf --retry-pages 27,28,80
```

## Installation

### 1. Install UV (if not already installed)
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Install System Dependencies
```bash
# macOS
brew install poppler

# Ubuntu/Debian
sudo apt-get install poppler-utils

# Fedora
sudo dnf install poppler-utils
```

### 3. Install Python Dependencies
```bash
cd ~/.claude
uv sync
```

This will install:
- `pdf2image` - PDF to image conversion
- `openai` - OpenAI API client (for GPT-4o models)
- `requests` - HTTP library (for OpenRouter models)
- `tqdm` - Progress bars
- `pillow` - Image processing

## Configuration

### API Keys

Set your API key(s) based on which models you want to use:

```bash
# For OpenRouter models (Gemini, Claude) - RECOMMENDED
export OPENROUTER_API_KEY="your-openrouter-api-key"

# For OpenAI models (GPT-4o)
export OPENAI_API_KEY="your-openai-api-key"

# Or add to ~/.claude/.env
echo 'OPENROUTER_API_KEY="sk-or-v1-..."' >> ~/.claude/.env
echo 'OPENAI_API_KEY="sk-..."' >> ~/.claude/.env
```

Get your OpenRouter API key at: https://openrouter.ai/keys

## Available Models

### Gemini (OpenRouter) - RECOMMENDED
- `google/gemini-3-flash-preview` or `gemini-flash` - **Default**, fast and cost-effective (~$0.001/page)
- `google/gemini-3-pro-preview` - More capable, higher quality (~$0.005/page)

### Claude (OpenRouter)
- `claude-sonnet-4.5` or `claude-sonnet` - High quality (~$0.015/page)
- `claude-haiku-4.5` or `claude-haiku` - Fast and efficient (~$0.004/page)

### OpenAI
- `gpt-4o` - Latest GPT-4 with vision (~$0.025/page)
- `gpt-4o-mini` - Smaller, faster GPT-4 (~$0.006/page)

## Usage Examples

### Basic Conversion (Default: Gemini Flash)
```bash
~/.claude/tools/pdf_to_markdown.py ~/Documents/research-paper.pdf
# Output: ~/Documents/research-paper.md (same directory as PDF)
# Temp files: /tmp/pdf_to_markdown_xyz123/ (auto-cleaned)
```

### Use Gemini Pro for Better Quality
```bash
~/.claude/tools/pdf_to_markdown.py ~/Documents/report.pdf --model gemini-pro
```

### Use Claude Sonnet for Highest Quality
```bash
~/.claude/tools/pdf_to_markdown.py ~/Documents/complex-doc.pdf --model claude-sonnet
```

### Use OpenAI GPT-4o
```bash
~/.claude/tools/pdf_to_markdown.py ~/Documents/report.pdf --model gpt-4o
```

### Custom Output Directory
```bash
~/.claude/tools/pdf_to_markdown.py ~/Documents/report.pdf \
  --output-dir ~/Documents/converted
# Output: ~/Documents/converted/report.md
```

### Faster Processing (More Workers)
```bash
# Use 20 parallel workers instead of default 10
~/.claude/tools/pdf_to_markdown.py ~/Documents/large-document.pdf \
  --model gemini-flash \
  --workers 20
```

### Batch Processing
```bash
# Process multiple PDFs with Gemini Flash
for pdf in ~/Documents/*.pdf; do
  ~/.claude/tools/pdf_to_markdown.py "$pdf" --model gemini-flash
done

# Or with custom output directory
for pdf in ~/Documents/*.pdf; do
  ~/.claude/tools/pdf_to_markdown.py "$pdf" \
    --model gemini-flash \
    --output-dir ~/Documents/markdown
done
```

### Retry Failed Pages

Sometimes pages fail due to transient network errors (SSL issues, timeouts, rate limits). The tool now supports automatic retry:

```bash
# Auto-detect and retry all failed pages
# (looks for "[Error transcribing page X:" markers in the markdown)
~/.claude/tools/pdf_to_markdown.py ~/Documents/report.pdf --retry

# Retry specific pages only
~/.claude/tools/pdf_to_markdown.py ~/Documents/report.pdf --retry-pages 27,28,80,81

# Increase retry attempts per page (default is 3)
~/.claude/tools/pdf_to_markdown.py ~/Documents/report.pdf --retry --max-retries 5
```

**How retry works:**
1. Reads the existing markdown file
2. Finds pages with error markers (or uses the pages you specified)
3. Re-converts just those pages from the PDF
4. Patches the successful transcriptions into the markdown
5. Reports remaining failures (if any)

**Built-in retry during initial conversion:**
- Each page automatically retries up to 3 times on failure
- Uses exponential backoff (2s, 4s, 6s delays)
- Only marks as failed after all retries exhausted

## How It Works

1. **PDF → Images**: Converts each PDF page to a JPEG image (200 DPI)
2. **System Temp Storage**: Images stored in `/tmp/pdf_to_markdown_xyz/` (auto-cleanup)
3. **Parallel Processing**: Processes multiple pages simultaneously using ThreadPoolExecutor
4. **AI Vision**: Each image is sent to selected AI model with vision capabilities
5. **Markdown Assembly**: Transcribed pages are assembled in order with headers
6. **Smart Output**: Saves markdown next to source PDF (or custom directory)
7. **Cleanup**: Temporary files automatically removed from system temp

## Output Format

```markdown
# document-name

## Page 1

[Transcribed content from page 1]

---

## Page 2

[Transcribed content from page 2]

---
```

## Performance

- **Default**: 10 parallel workers
- **Speed**: 
  - Gemini Flash: ~1-2 seconds per page
  - Gemini Pro: ~2-3 seconds per page
  - Claude Sonnet: ~2-4 seconds per page
  - GPT-4o: ~2-5 seconds per page
- **Quality**: All models provide high-quality transcription including:
  - Tables → Markdown tables
  - Mathematical expressions
  - Document structure preservation
  - Clean formatting

## Troubleshooting

### "pdf2image not found"
```bash
cd ~/.claude && uv sync
```

### "poppler not installed"
```bash
# macOS
brew install poppler

# Linux
sudo apt-get install poppler-utils
```

### "OPENROUTER_API_KEY not set"
```bash
# Add to ~/.claude/.env
echo 'OPENROUTER_API_KEY="sk-or-v1-..."' >> ~/.claude/.env

# Or export in shell
export OPENROUTER_API_KEY="sk-or-v1-..."
```

### "OPENAI_API_KEY not set" (only if using GPT-4o)
```bash
# Add to ~/.claude/.env
echo 'OPENAI_API_KEY="sk-..."' >> ~/.claude/.env
```

### Rate Limits
If you hit API rate limits, reduce workers:
```bash
~/.claude/tools/pdf_to_markdown.py document.pdf --workers 5
```

## When to Use

- ✅ Research paper analysis
- ✅ Financial document processing
- ✅ Technical documentation conversion
- ✅ Archiving PDF content as searchable markdown
- ✅ Building knowledge bases from PDFs
- ✅ Batch processing large document collections

## Cost Comparison

**Per page estimates (approximate):**

| Model | Cost/Page | Speed | Quality | Best For |
|-------|-----------|-------|---------|----------|
| Gemini Flash | ~$0.001 | ⚡⚡⚡ | ⭐⭐⭐ | **Default choice, bulk processing** |
| Gemini Pro | ~$0.005 | ⚡⚡ | ⭐⭐⭐⭐ | Complex documents, better accuracy |
| Claude Haiku | ~$0.004 | ⚡⚡⚡ | ⭐⭐⭐⭐ | Fast + high quality |
| Claude Sonnet | ~$0.015 | ⚡⚡ | ⭐⭐⭐⭐⭐ | Highest quality, complex layouts |
| GPT-4o Mini | ~$0.006 | ⚡⚡ | ⭐⭐⭐ | OpenAI ecosystem |
| GPT-4o | ~$0.025 | ⚡ | ⭐⭐⭐⭐ | Premium quality |

**Recommendation**: Start with **Gemini Flash** (default) for most use cases. Upgrade to Gemini Pro or Claude Sonnet for complex documents with tables, diagrams, or technical content.

## Advanced Usage

### Override Provider Detection
```bash
# Force OpenRouter even with a GPT model name
~/.claude/tools/pdf_to_markdown.py document.pdf \
  --model gpt-4o \
  --provider openrouter
```

### Use Custom OpenRouter Model
```bash
# Use any OpenRouter model by full ID
~/.claude/tools/pdf_to_markdown.py document.pdf \
  --model google/gemini-2.0-flash-exp
```

## Model Selection Guide

**Choose Gemini Flash when:**
- Processing many documents
- Cost is a concern
- Documents are straightforward text

**Choose Gemini Pro when:**
- Documents have complex tables
- Higher accuracy needed
- Technical/scientific content

**Choose Claude Sonnet when:**
- Maximum quality required
- Complex layouts and diagrams
- Critical accuracy needed

**Choose GPT-4o when:**
- Already using OpenAI ecosystem
- Need consistency with other GPT-4 workflows
