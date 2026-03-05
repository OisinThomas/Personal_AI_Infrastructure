# Mermaid Diagram to Image Converter

Convert Mermaid diagrams to images (PNG/SVG/PDF) with support for individual diagrams, markdown files, or batch directory processing.

## Quick Usage

```bash
# Process a single markdown file and update with image references
bun ~/.claude/tools/mermaid-to-image.ts --file diagram.md --update-markdown

# Process all diagrams in a directory
bun ~/.claude/tools/mermaid-to-image.ts --dir ./diagrams/ --format png --theme dark --update-markdown

# Process individual mermaid diagrams from JSON
bun ~/.claude/tools/mermaid-to-image.ts --diagrams '[
  {"mermaid": "graph TD\nA-->B", "output": "./diagram.png"}
]'
```

## Installation

The tool requires `@mermaid-js/mermaid-cli` to be installed:

```bash
npm install -g @mermaid-js/mermaid-cli
```

## Command Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--file <path>` | Process a single markdown file | - |
| `--dir <path>` | Process all markdown files in directory | - |
| `--diagrams <json>` | Process diagrams from JSON array | - |
| `--format <type>` | Output format: `png`, `svg`, `pdf` | `png` |
| `--theme <theme>` | Mermaid theme: `default`, `dark`, `forest`, `neutral` | `default` |
| `--background <color>` | Background color (e.g., `transparent`, `white`, `#ffffff`) | `transparent` |
| `--update-markdown` | Update markdown files with image references | `false` |
| `--help`, `-h` | Show help message | - |

## Usage Modes

### 1. Single Markdown File

Process a markdown file, extract all mermaid diagrams, and generate images:

```bash
bun ~/.claude/tools/mermaid-to-image.ts \
  --file ./documentation.md \
  --format png \
  --theme dark \
  --background transparent
```

**With markdown updates:**
```bash
bun ~/.claude/tools/mermaid-to-image.ts \
  --file ./documentation.md \
  --update-markdown
```

This will:
1. Extract all `mermaid` code blocks from the file
2. Generate PNG images (e.g., `documentation-1.png`, `documentation-2.png`)
3. Insert `![Diagram](./documentation-1.png)` after each mermaid block (if `--update-markdown` is used)

### 2. Directory Processing

Process all markdown files in a directory:

```bash
bun ~/.claude/tools/mermaid-to-image.ts \
  --dir ./diagrams/ \
  --format svg \
  --theme forest \
  --update-markdown
```

This will:
1. Find all `.md` files in the directory
2. Extract mermaid diagrams from each file
3. Generate images in the same directory
4. Update markdown files with image references

### 3. Individual Diagrams (JSON)

Process specific mermaid diagrams using JSON configuration:

```bash
bun ~/.claude/tools/mermaid-to-image.ts --diagrams '[
  {
    "mermaid": "graph TD\n    A[Start] --> B[End]",
    "output": "./flowchart.png",
    "format": "png",
    "theme": "dark"
  },
  {
    "mermaid": "sequenceDiagram\n    Alice->>Bob: Hello",
    "output": "./sequence.svg",
    "format": "svg"
  }
]'
```

Each diagram object can have:
- `mermaid` (required): The mermaid diagram string
- `output` (required): Output file path
- `format` (optional): `png`, `svg`, or `pdf`
- `theme` (optional): Mermaid theme
- `backgroundColor` (optional): Background color

## Examples

### Example 1: Convert Research Documentation

Convert all diagrams in research documentation with dark theme:

```bash
bun ~/.claude/tools/mermaid-to-image.ts \
  --dir ~/Developer/project/docs/ \
  --format png \
  --theme dark \
  --background transparent \
  --update-markdown
```

### Example 2: Generate High-Quality SVGs

Generate SVG files for web embedding:

```bash
bun ~/.claude/tools/mermaid-to-image.ts \
  --file architecture.md \
  --format svg \
  --theme default
```

### Example 3: Create PDF for Presentation

Create PDF diagrams for presentations:

```bash
bun ~/.claude/tools/mermaid-to-image.ts \
  --file presentation-diagrams.md \
  --format pdf \
  --theme neutral \
  --background white
```

### Example 4: Batch Process with Custom Outputs

Use JSON mode for fine-grained control:

```bash
bun ~/.claude/tools/mermaid-to-image.ts --diagrams '[
  {
    "mermaid": "graph LR\n    A-->B-->C",
    "output": "./images/flow-1.png",
    "theme": "dark",
    "backgroundColor": "#1a1a1a"
  },
  {
    "mermaid": "pie title Metrics\n    \"A\" : 40\n    \"B\" : 60",
    "output": "./images/pie-chart.svg",
    "format": "svg",
    "theme": "default"
  }
]'
```

## Output Behavior

### File Naming

**Single diagram in file:**
- Input: `diagram.md`
- Output: `diagram.png`

**Multiple diagrams in file:**
- Input: `diagram.md`
- Output: `diagram-1.png`, `diagram-2.png`, `diagram-3.png`

### Markdown Updates

When `--update-markdown` is used, the tool inserts image references after each mermaid code block:

**Before:**
```markdown
## Architecture

```mermaid
graph TD
    A-->B
```

## Next Section
```

**After:**
```markdown
## Architecture

```mermaid
graph TD
    A-->B
```

![Diagram](./architecture.png)

## Next Section
```

## Supported Formats

| Format | Extension | Use Case |
|--------|-----------|----------|
| PNG | `.png` | General purpose, presentations, documentation |
| SVG | `.svg` | Web embedding, scalable graphics, high quality |
| PDF | `.pdf` | Print materials, presentations, archival |

## Supported Themes

| Theme | Description |
|-------|-------------|
| `default` | Standard mermaid theme with blue accents |
| `dark` | Dark theme with light text on dark background |
| `forest` | Green forest theme |
| `neutral` | Neutral grayscale theme |

## Troubleshooting

### Issue: "mmdc: command not found"

**Solution:** Install mermaid-cli globally:
```bash
npm install -g @mermaid-js/mermaid-cli
```

### Issue: "Error: Cannot find module 'puppeteer'"

**Solution:** Reinstall mermaid-cli:
```bash
npm uninstall -g @mermaid-js/mermaid-cli
npm install -g @mermaid-js/mermaid-cli
```

### Issue: Diagrams not rendering correctly

**Solution:** Check your mermaid syntax:
```bash
# Test mermaid syntax directly with mmdc
echo "graph TD\n    A-->B" > test.mmd
mmdc -i test.mmd -o test.png
```

### Issue: Permission denied

**Solution:** Make the tool executable:
```bash
chmod +x ~/.claude/tools/mermaid-to-image.ts
```

## Integration Examples

### Use in Claude Code

When working on documentation with mermaid diagrams:

```
User: "Convert all the mermaid diagrams in the diagrams folder to PNGs"

Claude: I'll convert all the mermaid diagrams in the diagrams folder to PNG images.

[Runs command]
bun ~/.claude/tools/mermaid-to-image.ts \
  --dir ./diagrams/ \
  --format png \
  --theme default \
  --background transparent \
  --update-markdown
```

### Automated Workflow

Create a script to convert diagrams as part of your build process:

```bash
#!/bin/bash
# build-docs.sh

echo "Converting mermaid diagrams..."
bun ~/.claude/tools/mermaid-to-image.ts \
  --dir ./docs/ \
  --format svg \
  --theme dark \
  --update-markdown

echo "Building static site..."
# ... rest of build process
```

## Technical Details

### Dependencies

- **@mermaid-js/mermaid-cli** - Mermaid command-line interface
- **Puppeteer** - Headless browser for rendering (bundled with mermaid-cli)
- **Bun** - TypeScript runtime

### How It Works

1. **Parse input**: Reads markdown files or JSON configuration
2. **Extract diagrams**: Uses regex to find `mermaid` code blocks
3. **Create temp files**: Writes mermaid content to temporary `.mmd` files
4. **Execute mmdc**: Shells out to `mmdc` command for rendering
5. **Update markdown**: Optionally inserts image references
6. **Cleanup**: Removes temporary files

### Performance

- **Single diagram**: ~1-2 seconds
- **Multiple diagrams**: ~1-2 seconds per diagram (sequential processing)
- **Large files**: Processing time scales linearly with number of diagrams

## Related Tools

- **mmdc** - Direct mermaid-cli command
- **markdown-builder** - Combine multiple markdown files
- **pdf-to-markdown** - Convert PDFs to markdown

## Version History

- **v1.0** (2024-10-30) - Initial release
  - Support for PNG/SVG/PDF formats
  - Markdown file processing
  - Directory batch processing
  - JSON diagram configuration
  - Theme and background customization
  - Automatic markdown updates

## License

Part of the Personal AI Infrastructure (PAI) toolkit.