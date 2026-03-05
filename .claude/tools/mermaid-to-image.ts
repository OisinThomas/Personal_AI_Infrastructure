#!/usr/bin/env bun

/**
 * Mermaid Diagram to Image Converter
 *
 * Converts Mermaid diagrams to images (PNG/SVG/PDF) with support for:
 * - Individual mermaid diagram strings
 * - Batch processing from markdown files
 * - Directory processing
 * - Custom themes and backgrounds
 */

import { readFileSync, writeFileSync, mkdirSync, unlinkSync, readdirSync, statSync } from 'fs';
import { join, dirname, basename, extname } from 'path';
import { execSync } from 'child_process';
import { tmpdir } from 'os';

interface DiagramConfig {
  mermaid: string;
  output: string;
  format?: 'png' | 'svg' | 'pdf';
  theme?: 'default' | 'dark' | 'forest' | 'neutral';
  backgroundColor?: string;
}

interface CliOptions {
  file?: string;
  diagrams?: string;
  dir?: string;
  format?: 'png' | 'svg' | 'pdf';
  theme?: 'default' | 'dark' | 'forest' | 'neutral';
  background?: string;
  updateMarkdown?: boolean;
}

/**
 * Extract mermaid diagrams from markdown content
 */
function extractMermaidDiagrams(markdown: string): string[] {
  const regex = /```mermaid\n([\s\S]*?)```/g;
  const diagrams: string[] = [];
  let match;

  while ((match = regex.exec(markdown)) !== null) {
    diagrams.push(match[1].trim());
  }

  return diagrams;
}

/**
 * Convert a single mermaid diagram to an image
 */
function convertDiagramToImage(config: DiagramConfig): void {
  const {
    mermaid,
    output,
    format = 'png',
    theme = 'default',
    backgroundColor = 'transparent'
  } = config;

  // Create temp file for mermaid content
  const tempDir = tmpdir();
  const tempFile = join(tempDir, `mermaid-${Date.now()}.mmd`);

  try {
    // Write mermaid content to temp file
    writeFileSync(tempFile, mermaid, 'utf-8');

    // Ensure output directory exists
    const outputDir = dirname(output);
    mkdirSync(outputDir, { recursive: true });

    // Build mmdc command
    const cmd = [
      'mmdc',
      '-i', tempFile,
      '-o', output,
      '-t', theme,
      '-b', backgroundColor
    ];

    // Execute mmdc
    console.log(`Converting diagram to ${output}...`);
    execSync(cmd.join(' '), { stdio: 'inherit' });
    console.log(`✓ Generated: ${output}`);

  } catch (error) {
    console.error(`✗ Failed to convert diagram: ${error}`);
    throw error;
  } finally {
    // Clean up temp file
    try {
      unlinkSync(tempFile);
    } catch (e) {
      // Ignore cleanup errors
    }
  }
}

/**
 * Process a markdown file: extract diagrams, generate images, optionally update markdown
 */
function processMarkdownFile(
  filePath: string,
  options: {
    format?: 'png' | 'svg' | 'pdf';
    theme?: string;
    backgroundColor?: string;
    updateMarkdown?: boolean;
  }
): void {
  const { format = 'png', theme = 'default', backgroundColor = 'transparent', updateMarkdown = false } = options;

  console.log(`\nProcessing markdown file: ${filePath}`);

  // Read markdown content
  const markdown = readFileSync(filePath, 'utf-8');

  // Extract diagrams
  const diagrams = extractMermaidDiagrams(markdown);

  if (diagrams.length === 0) {
    console.log('  No mermaid diagrams found');
    return;
  }

  console.log(`  Found ${diagrams.length} mermaid diagram(s)`);

  // Get base filename without extension
  const dir = dirname(filePath);
  const baseFilename = basename(filePath, extname(filePath));

  // Generate images
  let updatedMarkdown = markdown;

  diagrams.forEach((diagram, index) => {
    // Determine output filename
    const outputFilename = diagrams.length === 1
      ? `${baseFilename}.${format}`
      : `${baseFilename}-${index + 1}.${format}`;

    const outputPath = join(dir, outputFilename);

    // Convert diagram
    convertDiagramToImage({
      mermaid: diagram,
      output: outputPath,
      format,
      theme: theme as any,
      backgroundColor
    });

    // Update markdown if requested
    if (updateMarkdown) {
      // Find the mermaid code block and add image reference after it
      const diagramPattern = new RegExp(`\`\`\`mermaid\\n${diagram.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\n\`\`\``, 'g');
      const imageReference = `\n\n![Diagram](./${outputFilename})\n`;

      // Only add if not already present
      if (!updatedMarkdown.includes(`![Diagram](./${outputFilename})`)) {
        updatedMarkdown = updatedMarkdown.replace(diagramPattern, `$&${imageReference}`);
      }
    }
  });

  // Write updated markdown if changes were made
  if (updateMarkdown && updatedMarkdown !== markdown) {
    writeFileSync(filePath, updatedMarkdown, 'utf-8');
    console.log(`✓ Updated markdown file with image references`);
  }
}

/**
 * Process all markdown files in a directory
 */
function processDirectory(
  dirPath: string,
  options: {
    format?: 'png' | 'svg' | 'pdf';
    theme?: string;
    backgroundColor?: string;
    updateMarkdown?: boolean;
  }
): void {
  console.log(`\nProcessing directory: ${dirPath}`);

  const files = readdirSync(dirPath);
  const markdownFiles = files.filter(f => f.endsWith('.md'));

  console.log(`Found ${markdownFiles.length} markdown file(s)`);

  markdownFiles.forEach(file => {
    const filePath = join(dirPath, file);
    processMarkdownFile(filePath, options);
  });
}

/**
 * Parse CLI arguments
 */
function parseArgs(args: string[]): CliOptions {
  const options: CliOptions = {};

  for (let i = 0; i < args.length; i++) {
    const arg = args[i];

    switch (arg) {
      case '--file':
        options.file = args[++i];
        break;
      case '--diagrams':
        options.diagrams = args[++i];
        break;
      case '--dir':
        options.dir = args[++i];
        break;
      case '--format':
        options.format = args[++i] as any;
        break;
      case '--theme':
        options.theme = args[++i] as any;
        break;
      case '--background':
        options.background = args[++i];
        break;
      case '--update-markdown':
        options.updateMarkdown = true;
        break;
      case '--help':
      case '-h':
        printHelp();
        process.exit(0);
        break;
    }
  }

  return options;
}

/**
 * Print help message
 */
function printHelp(): void {
  console.log(`
Mermaid Diagram to Image Converter

USAGE:
  bun mermaid-to-image.ts [OPTIONS]

OPTIONS:
  --file <path>              Process a single markdown file
  --diagrams <json>          Process diagrams from JSON array
  --dir <path>               Process all markdown files in directory
  --format <png|svg|pdf>     Output format (default: png)
  --theme <theme>            Mermaid theme: default, dark, forest, neutral (default: default)
  --background <color>       Background color (default: transparent)
  --update-markdown          Update markdown files with image references
  --help, -h                 Show this help message

EXAMPLES:

  # Process a single markdown file
  bun mermaid-to-image.ts --file diagram.md --format png --theme dark --background transparent

  # Process and update markdown with image references
  bun mermaid-to-image.ts --file diagram.md --update-markdown

  # Process all markdown files in a directory
  bun mermaid-to-image.ts --dir ./diagrams/ --format png --theme default --update-markdown

  # Process individual diagrams from JSON
  bun mermaid-to-image.ts --diagrams '[
    {"mermaid": "graph TD\\nA-->B", "output": "./output1.png"},
    {"mermaid": "sequenceDiagram\\nA->>B: Hello", "output": "./output2.svg", "format": "svg"}
  ]'

FORMATS:
  png  - Portable Network Graphics (default)
  svg  - Scalable Vector Graphics
  pdf  - Portable Document Format

THEMES:
  default - Default mermaid theme
  dark    - Dark theme
  forest  - Forest theme
  neutral - Neutral theme
`);
}

/**
 * Main entry point
 */
function main(): void {
  const args = process.argv.slice(2);

  if (args.length === 0) {
    console.error('Error: No arguments provided');
    printHelp();
    process.exit(1);
  }

  const options = parseArgs(args);

  try {
    if (options.file) {
      // Process single file
      processMarkdownFile(options.file, {
        format: options.format,
        theme: options.theme,
        backgroundColor: options.background,
        updateMarkdown: options.updateMarkdown
      });

    } else if (options.dir) {
      // Process directory
      processDirectory(options.dir, {
        format: options.format,
        theme: options.theme,
        backgroundColor: options.background,
        updateMarkdown: options.updateMarkdown
      });

    } else if (options.diagrams) {
      // Process individual diagrams from JSON
      const diagrams: DiagramConfig[] = JSON.parse(options.diagrams);

      diagrams.forEach((diagram, index) => {
        console.log(`\nProcessing diagram ${index + 1}/${diagrams.length}`);
        convertDiagramToImage({
          ...diagram,
          format: diagram.format || options.format,
          theme: diagram.theme || options.theme,
          backgroundColor: diagram.backgroundColor || options.background
        });
      });

    } else {
      console.error('Error: Must specify --file, --dir, or --diagrams');
      printHelp();
      process.exit(1);
    }

    console.log('\n✓ All conversions completed successfully');

  } catch (error) {
    console.error('\n✗ Conversion failed:', error);
    process.exit(1);
  }
}

// Run main
main();
