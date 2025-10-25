# PDF to Markdown Command

## Quick Usage
```bash
# Convert a PDF to markdown
~/.claude/pai/tools/pdf_to_markdown.py ~/Documents/report.pdf

# Specify output directory
~/.claude/pai/tools/pdf_to_markdown.py ~/Documents/report.pdf --output-dir ~/Documents/markdown

# Use more workers for faster processing
~/.claude/pai/tools/pdf_to_markdown.py ~/Documents/report.pdf --workers 20
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
cd ~/.claude/pai
uv sync
```

This will install:
- `pdf2image` - PDF to image conversion
- `openai` - OpenAI API client
- `tqdm` - Progress bars
- `pillow` - Image processing

## Configuration

Set your OpenAI API key:
```bash
# Add to ~/.claude/pai/.env
OPENAI_API_KEY_DEFAULT="your-openai-api-key-here"

# Or export in your shell
export OPENAI_API_KEY_DEFAULT="your-openai-api-key-here"
```

## Usage Examples

### Basic Conversion
```bash
~/.claude/pai/tools/pdf_to_markdown.py ~/Documents/research-paper.pdf
# Output: ./pdf_output/research-paper.md
```

### Custom Output Directory
```bash
~/.claude/pai/tools/pdf_to_markdown.py ~/Documents/report.pdf \
  --output-dir ~/Documents/converted
```

### Faster Processing (More Workers)
```bash
# Use 20 parallel workers instead of default 10
~/.claude/pai/tools/pdf_to_markdown.py ~/Documents/large-document.pdf \
  --workers 20
```

### Batch Processing
```bash
# Process multiple PDFs
for pdf in ~/Documents/*.pdf; do
  ~/.claude/pai/tools/pdf_to_markdown.py "$pdf" --output-dir ~/Documents/markdown
done
```

## How It Works

1. **PDF → Images**: Converts each PDF page to a JPEG image (200 DPI)
2. **Parallel Processing**: Processes multiple pages simultaneously using ThreadPoolExecutor
3. **GPT-4o Vision**: Each image is sent to OpenAI's GPT-4o with vision capabilities
4. **Markdown Assembly**: Transcribed pages are assembled in order with headers
5. **Cleanup**: Temporary image files are automatically removed

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
- **Speed**: ~2-5 seconds per page (depending on complexity)
- **Quality**: GPT-4o provides high-quality transcription including:
  - Tables → Markdown tables
  - Mathematical expressions
  - Document structure preservation
  - Clean formatting

## Troubleshooting

### "pdf2image not found"
```bash
cd ~/.claude/pai && uv sync
```

### "poppler not installed"
```bash
# macOS
brew install poppler

# Linux
sudo apt-get install poppler-utils
```

### "OPENAI_API_KEY_DEFAULT not set"
```bash
# Add to ~/.claude/pai/.env
echo 'OPENAI_API_KEY_DEFAULT="sk-..."' >> ~/.claude/pai/.env
```

### Rate Limits
If you hit OpenAI rate limits, reduce workers:
```bash
~/.claude/pai/tools/pdf_to_markdown.py document.pdf --workers 5
```

## When to Use

- ✅ Research paper analysis
- ✅ Financial document processing
- ✅ Technical documentation conversion
- ✅ Archiving PDF content as searchable markdown
- ✅ Building knowledge bases from PDFs

## Cost Considerations

- Uses GPT-4o vision API
- Cost: ~$0.01-0.05 per page (depending on complexity)
- For large documents, consider processing in batches
