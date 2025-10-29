# OpenRouter Call Tool

A flexible CLI tool for calling OpenRouter models with advanced prompt composition and conversation threading.

## Features

- 🤖 **Multiple Models** - Easy access to Gemini, Claude, and other OpenRouter models
- 📝 **Flexible Prompts** - Compose messages from text, files, JSON, or combinations
- 💬 **Conversation Threading** - Continue multi-turn conversations with automatic state management
- 🎯 **Structured Outputs** - Enforce JSON schemas for consistent responses
- 🛠️ **Tool Calling** - Support for function/tool calling workflows
- 📊 **Usage Tracking** - Token usage statistics for cost monitoring

## Installation

### Prerequisites

```bash
# Install required Python package
pip install requests

# Set your OpenRouter API key
export OPENROUTER_API_KEY='your-key-here'
```

Add the export to your `~/.zshrc` or `~/.bashrc` to make it permanent.

### Verify Installation

```bash
cd Personal_AI_Infrastructure/.claude/tools
./openrouter_call.py --help
```

## Quick Start

### Simple Call

```bash
./openrouter_call.py \
  --model gemini-flash \
  --user "Explain quantum computing in simple terms" \
  --output tmp/quantum.md
```

### With System Message

```bash
./openrouter_call.py \
  --model claude-sonnet \
  --system "You are a helpful Python coding assistant" \
  --user "Write a function to calculate fibonacci numbers" \
  --output tmp/fibonacci.py
```

### Continue a Conversation

```bash
# First message
./openrouter_call.py \
  --model gemini-pro \
  --user "What are the main features of Python?" \
  --output tmp/python1.md

# Continue (use the thread ID from output)
./openrouter_call.py \
  --model gemini-pro \
  --continue-thread 20250129-223045-a3f2 \
  --user "Can you give examples of each feature?" \
  --output tmp/python2.md
```

## Available Models

### Shortcuts

The tool provides convenient shortcuts for common models:

| Shortcut | Full Model ID |
|----------|---------------|
| `gemini-flash` | `google/gemini-2.5-flash` |
| `gemini-pro` | `google/gemini-2.5-pro` |
| `gemini-2.5-flash` | `google/gemini-2.5-flash` |
| `gemini-2.5-pro` | `google/gemini-2.5-pro` |
| `claude-sonnet` | `anthropic/claude-sonnet-4.5` |
| `claude-haiku` | `anthropic/claude-haiku-4.5` |
| `claude-sonnet-4.5` | `anthropic/claude-sonnet-4.5` |
| `claude-haiku-4.5` | `anthropic/claude-haiku-4.5` |

### Adding New Models

Edit the `MODELS` dictionary in `openrouter_call.py`:

```python
MODELS = {
    'my-model': 'provider/model-name',
    # ... existing models
}
```

You can also use the full OpenRouter model ID directly without adding a shortcut.

## Advanced Usage

### Multi-Part Message Composition

Compose messages from multiple sources:

```bash
./openrouter_call.py \
  --model claude-sonnet \
  --system '[
    {"type": "file", "path": "prompts/expert_coder.md"},
    {"type": "text", "content": "\n\n## Project Context:\n"},
    {"type": "files", "paths": ["src/main.py", "src/utils.py"], "separator": "\n----\n"}
  ]' \
  --user "Refactor this code for better performance" \
  --output tmp/refactor.md
```

#### Composition Part Types

**1. Plain Text**
```json
{"type": "text", "content": "Your text here"}
```

**2. Single File**
```json
{"type": "file", "path": "relative/path/to/file.md"}
```

**3. JSON Extraction**
```json
{"type": "json", "path": "data.json", "key": "nested.key.path"}
```

**4. Multiple Files with Separator**
```json
{
  "type": "files",
  "paths": ["file1.md", "file2.md", "file3.md"],
  "separator": "\n\n---\n\n"
}
```

### Structured Output (JSON Schema)

Enforce a specific JSON structure in the response:

```bash
./openrouter_call.py \
  --model gemini-pro \
  --user "Extract the main points from this article: $(cat article.md)" \
  --schema '{
    "type": "object",
    "properties": {
      "title": {"type": "string"},
      "main_points": {
        "type": "array",
        "items": {"type": "string"}
      },
      "summary": {"type": "string"}
    },
    "required": ["title", "main_points", "summary"]
  }' \
  --output tmp/extracted.json
```

### Tool/Function Calling

Define tools for the model to use:

**tools.json:**
```json
[
  {
    "type": "function",
    "function": {
      "name": "search_database",
      "description": "Search for information in the database",
      "parameters": {
        "type": "object",
        "properties": {
          "query": {
            "type": "string",
            "description": "Search query"
          }
        },
        "required": ["query"]
      }
    }
  }
]
```

**Usage:**
```bash
./openrouter_call.py \
  --model claude-sonnet \
  --user "Find information about quantum computing" \
  --tools '{"type": "file", "path": "tools.json"}' \
  --output tmp/search_result.md
```

Or inline:
```bash
./openrouter_call.py \
  --model claude-sonnet \
  --user "Find information about quantum computing" \
  --tools '[{"type": "function", "function": {...}}]' \
  --output tmp/search_result.md
```

### Temperature and Max Tokens

Control response randomness and length:

```bash
./openrouter_call.py \
  --model gemini-flash \
  --user "Write a creative story about AI" \
  --temperature 1.5 \
  --max-tokens 2000 \
  --output tmp/story.md
```

## Thread Management

### List All Threads

```bash
./openrouter_call.py --list-threads
```

Output:
```
Available threads (3):

  20250129-223045-a3f2
    Model: google/gemini-2.5-pro
    Created: 2025-01-29T22:30:45.123456
    Messages: 4
    Preview: What are the main features of Python?

  20250129-220130-b7e9
    Model: anthropic/claude-sonnet-4.5
    Created: 2025-01-29T22:01:30.654321
    Messages: 2
    Preview: Explain quantum computing in simple terms

Continue a thread with: --continue-thread THREAD_ID
```

### Show Thread History

```bash
./openrouter_call.py --show-thread 20250129-223045-a3f2
```

### Delete a Thread

```bash
./openrouter_call.py --delete-thread 20250129-223045-a3f2
```

## File Paths and Base Path

By default, all file references are relative to the current working directory. You can change this with `--base-path`:

```bash
./openrouter_call.py \
  --model gemini-flash \
  --base-path /path/to/project \
  --user '{"type": "file", "path": "docs/requirements.md"}' \
  --output tmp/analysis.md
```

## Output Location

- Responses are saved to the path specified by `--output`
- Thread files are saved to `tmp/threads/{thread-id}.json`
- The `tmp/` directory is created automatically if it doesn't exist

## Examples

### Code Review

```bash
./openrouter_call.py \
  --model claude-sonnet \
  --system "You are an expert code reviewer" \
  --user '[
    {"type": "text", "content": "Review this code:\n\n"},
    {"type": "file", "path": "src/main.py"}
  ]' \
  --output tmp/code_review.md
```

### Document Summarization

```bash
./openrouter_call.py \
  --model gemini-pro \
  --user '[
    {"type": "text", "content": "Summarize these documents:\n\n"},
    {"type": "files", "paths": ["doc1.md", "doc2.md", "doc3.md"], "separator": "\n\n---\n\n"}
  ]' \
  --output tmp/summary.md
```

### Data Extraction

```bash
./openrouter_call.py \
  --model gemini-flash \
  --user "Extract structured data from this text: $(cat data.txt)" \
  --schema '{
    "type": "object",
    "properties": {
      "entities": {"type": "array", "items": {"type": "string"}},
      "dates": {"type": "array", "items": {"type": "string"}},
      "locations": {"type": "array", "items": {"type": "string"}}
    }
  }' \
  --output tmp/extracted.json
```

### Multi-Turn Research

```bash
# Start research
./openrouter_call.py \
  --model claude-sonnet \
  --user "What are the key challenges in quantum computing?" \
  --output tmp/research1.md

# Follow up (use thread ID from output)
./openrouter_call.py \
  --continue-thread 20250129-223045-a3f2 \
  --user "How are researchers addressing these challenges?" \
  --output tmp/research2.md

# Deep dive
./openrouter_call.py \
  --continue-thread 20250129-223045-a3f2 \
  --user "Can you provide specific examples of recent breakthroughs?" \
  --output tmp/research3.md
```

## Error Handling

The tool provides clear error messages:

- **Missing API Key**: Instructions to set `OPENROUTER_API_KEY`
- **File Not Found**: Shows which files couldn't be read
- **Invalid JSON**: Points to syntax errors in JSON parameters
- **API Errors**: Displays OpenRouter API error messages

Errors during message composition are reported but don't stop execution - placeholders are used instead.

## Tips

1. **Use Shortcuts**: `gemini-flash` is faster and cheaper than `gemini-pro` for simple tasks
2. **Thread Management**: Use threads for multi-turn conversations to maintain context
3. **File Composition**: Break large prompts into files for better organization
4. **Structured Output**: Use JSON schemas when you need consistent, parseable responses
5. **Temperature**: Lower (0.0-0.7) for factual tasks, higher (0.8-2.0) for creative tasks
6. **Token Limits**: Monitor usage stats to optimize costs

## Troubleshooting

### "OPENROUTER_API_KEY environment variable not set"

```bash
export OPENROUTER_API_KEY='your-key-here'
```

### "File not found" errors

Check that file paths are relative to your current directory or use `--base-path`.

### JSON parsing errors

Ensure JSON is properly escaped in shell:
```bash
# Good
--schema '{"type": "object"}'

# Bad (unescaped quotes)
--schema {"type": "object"}
```

### Thread not found

Use `--list-threads` to see available thread IDs.

## Integration with Other Tools

### With markdown_builder.py

```bash
# Generate content with OpenRouter
./openrouter_call.py \
  --model gemini-pro \
  --user "Write a blog post about AI" \
  --output tmp/blog_content.md

# Build final document
./markdown_builder.py \
  --title "AI Blog Post" \
  --frontmatter '{"date": "2025-01-29", "author": "AI"}' \
  --body '[{"header": "Content", "type": "file", "path": "tmp/blog_content.md"}]' \
  --output final_blog.md
```

### With pdf_to_markdown.py

```bash
# Convert PDF to markdown
./pdf_to_markdown.py document.pdf tmp/doc.md

# Analyze with OpenRouter
./openrouter_call.py \
  --model claude-sonnet \
  --user '[
    {"type": "text", "content": "Analyze this document:\n\n"},
    {"type": "file", "path": "tmp/doc.md"}
  ]' \
  --output tmp/analysis.md
```

## License

Part of the Personal AI Infrastructure project.
