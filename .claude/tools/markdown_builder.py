#!/usr/bin/env python3
"""
Markdown Builder

Build markdown files from multiple sources with structured frontmatter.
Solves the token limit problem by referencing intermediate files instead of
holding everything in context.

Usage:
    ./markdown_builder.py --title "Title" --frontmatter '{}' --body '[]' --output out.md

Examples:
    # Simple text content
    ./markdown_builder.py \
      --title "My Document" \
      --frontmatter '{"date": "2025-01-26", "tags": ["tech"]}' \
      --body '[{"header": "Intro", "type": "text", "content": "Hello"}]' \
      --output doc.md

    # Reference files
    ./markdown_builder.py \
      --title "Podcast Episode" \
      --frontmatter '{"guest": {"type": "file", "path": "guest.txt"}}' \
      --body '[{"header": "Transcript", "type": "file", "path": "transcript.md"}]' \
      --output episode.md

    # Extract from JSON
    ./markdown_builder.py \
      --title "Report" \
      --frontmatter '{"author": {"type": "json", "path": "meta.json", "key": "author.name"}}' \
      --body '[{"header": "Stats", "type": "json", "path": "data.json", "keys": ["count", "total"]}]' \
      --output report.md
"""

import sys
import json
import argparse
from pathlib import Path
from typing import Any, Dict, List, Union

# Global error tracking
errors = []


def format_yaml_value(value: Any, indent: int = 0) -> str:
    """
    Format a Python value as YAML.

    Args:
        value: The value to format (str, int, list, dict, etc.)
        indent: Current indentation level

    Returns:
        YAML-formatted string
    """
    indent_str = "  " * indent

    if value is None:
        return "null"
    elif isinstance(value, bool):
        return "true" if value else "false"
    elif isinstance(value, (int, float)):
        return str(value)
    elif isinstance(value, str):
        # Simple string - check if it needs quoting
        if any(c in value for c in [':', '#', '[', ']', '{', '}', '\n']):
            # Use quoted string
            escaped = value.replace('"', '\\"')
            return f'"{escaped}"'
        return value
    elif isinstance(value, list):
        if not value:
            return "[]"
        # Format as list
        result = []
        for item in value:
            result.append(f"{indent_str}- {format_yaml_value(item, indent + 1)}")
        return "\n" + "\n".join(result)
    elif isinstance(value, dict):
        if not value:
            return "{}"
        # Format as nested dict
        result = []
        for key, val in value.items():
            formatted_val = format_yaml_value(val, indent + 1)
            if '\n' in formatted_val:
                result.append(f"{indent_str}{key}:{formatted_val}")
            else:
                result.append(f"{indent_str}{key}: {formatted_val}")
        return "\n" + "\n".join(result)
    else:
        return str(value)


def format_yaml(data: Dict[str, Any]) -> str:
    """
    Format a dictionary as YAML frontmatter.

    Args:
        data: Dictionary to format

    Returns:
        YAML string without delimiters
    """
    if not data:
        return ""

    lines = []
    for key, value in data.items():
        formatted_value = format_yaml_value(value, indent=1)
        if '\n' in formatted_value:
            lines.append(f"{key}:{formatted_value}")
        else:
            lines.append(f"{key}: {formatted_value}")

    return "\n".join(lines)


def extract_json_keys(json_path: Path, keys: Union[str, List[str]]) -> Dict[str, Any]:
    """
    Extract specific keys from a JSON file using dot notation.

    Args:
        json_path: Path to JSON file
        keys: Single key or list of keys (supports dot notation like "nested.key.path")

    Returns:
        Dictionary with extracted key-value pairs

    Raises:
        FileNotFoundError: If JSON file doesn't exist
        json.JSONDecodeError: If JSON is invalid
        KeyError: If key path doesn't exist
    """
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Ensure keys is a list
    if isinstance(keys, str):
        keys = [keys]

    result = {}
    for key_path in keys:
        # Navigate nested keys using dot notation
        parts = key_path.split('.')
        value = data

        for part in parts:
            if isinstance(value, dict):
                value = value[part]
            else:
                raise KeyError(f"Cannot access key '{part}' in non-dict value at path '{key_path}'")

        # Use the last part as the result key
        result_key = parts[-1]
        result[result_key] = value

    return result


def resolve_frontmatter_value(value: Any, base_path: Path) -> Any:
    """
    Resolve a frontmatter value (plain value, file reference, or JSON reference).

    Args:
        value: The value to resolve (can be plain value or dict with type)
        base_path: Base path for resolving relative file paths

    Returns:
        Resolved value
    """
    # If it's not a dict, return as-is
    if not isinstance(value, dict):
        return value

    # Check if it's a file/json reference (has 'type' key)
    if 'type' not in value:
        # It's a plain dict, recurse into it
        return {k: resolve_frontmatter_value(v, base_path) for k, v in value.items()}

    ref_type = value['type']

    if ref_type == 'file':
        # Read entire file content
        path = base_path / value['path']
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return f.read().strip()
        except FileNotFoundError:
            errors.append(f"File not found: {path}")
            return f"[FILE NOT FOUND: {path}]"
        except Exception as e:
            errors.append(f"Error reading {path}: {e}")
            return f"[ERROR READING: {path}]"

    elif ref_type == 'json':
        # Extract value from JSON file
        path = base_path / value['path']
        try:
            key_path = value['key']
            extracted = extract_json_keys(path, key_path)
            # Return just the value (not the key-value pair)
            return list(extracted.values())[0]
        except FileNotFoundError:
            errors.append(f"File not found: {path}")
            return f"[FILE NOT FOUND: {path}]"
        except KeyError as e:
            errors.append(f"Key not found in {path}: {e}")
            return f"[KEY NOT FOUND: {e}]"
        except Exception as e:
            errors.append(f"Error reading JSON from {path}: {e}")
            return f"[ERROR READING JSON: {path}]"

    else:
        errors.append(f"Unknown frontmatter type: {ref_type}")
        return f"[UNKNOWN TYPE: {ref_type}]"


def resolve_body_item(item: Dict[str, Any], base_path: Path) -> str:
    """
    Resolve a body item (text, file, or JSON extraction).

    Args:
        item: Body item dict with 'header', 'type', and type-specific fields
        base_path: Base path for resolving relative file paths

    Returns:
        Formatted markdown section with header and content
    """
    header = item.get('header', 'Section')
    item_type = item.get('type', 'text')

    # Start with level 2 header
    section = f"## {header}\n\n"

    if item_type == 'text':
        # Direct text content
        content = item.get('content', '')
        section += content

    elif item_type == 'file':
        # Read file content
        path = base_path / item['path']
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                section += content
        except FileNotFoundError:
            errors.append(f"File not found: {path}")
            section += f"[FILE NOT FOUND: {path}]"
        except Exception as e:
            errors.append(f"Error reading {path}: {e}")
            section += f"[ERROR READING: {path}]"

    elif item_type == 'json':
        # Extract and format JSON keys
        path = base_path / item['path']
        try:
            keys = item.get('keys', [])
            extracted = extract_json_keys(path, keys)

            # Format extracted data as YAML-style
            for key, value in extracted.items():
                formatted_value = format_yaml_value(value)
                if '\n' in formatted_value:
                    section += f"{key}:{formatted_value}\n"
                else:
                    section += f"{key}: {formatted_value}\n"
        except FileNotFoundError:
            errors.append(f"File not found: {path}")
            section += f"[FILE NOT FOUND: {path}]"
        except KeyError as e:
            errors.append(f"Key not found in {path}: {e}")
            section += f"[KEY NOT FOUND: {e}]"
        except Exception as e:
            errors.append(f"Error reading JSON from {path}: {e}")
            section += f"[ERROR READING JSON: {path}]"

    else:
        errors.append(f"Unknown body type: {item_type}")
        section += f"[UNKNOWN TYPE: {item_type}]"

    return section


def build_markdown(
    title: str,
    frontmatter: Dict[str, Any],
    body: List[Dict[str, Any]],
    base_path: Path
) -> str:
    """
    Build the complete markdown document.

    Args:
        title: Document title (becomes H1)
        frontmatter: Frontmatter dictionary
        body: List of body section items
        base_path: Base path for resolving relative file paths

    Returns:
        Complete markdown document as string
    """
    parts = []

    # Add frontmatter if present
    if frontmatter:
        resolved_frontmatter = {
            key: resolve_frontmatter_value(value, base_path)
            for key, value in frontmatter.items()
        }
        yaml_content = format_yaml(resolved_frontmatter)
        parts.append(f"---\n{yaml_content}\n---")

    # Add title
    if title:
        parts.append(f"# {title}")

    # Add body sections
    for item in body:
        section = resolve_body_item(item, base_path)
        parts.append(section)

    # Join all parts with double newlines
    return "\n\n".join(parts)


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Build markdown files from multiple sources with structured frontmatter',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Simple text content
  %(prog)s \\
    --title "My Document" \\
    --frontmatter '{"date": "2025-01-26"}' \\
    --body '[{"header": "Intro", "type": "text", "content": "Hello"}]' \\
    --output doc.md

  # Reference files
  %(prog)s \\
    --title "Podcast" \\
    --frontmatter '{"guest": {"type": "file", "path": "guest.txt"}}' \\
    --body '[{"header": "Transcript", "type": "file", "path": "transcript.md"}]' \\
    --output episode.md

  # Extract from JSON
  %(prog)s \\
    --title "Report" \\
    --body '[{"header": "Stats", "type": "json", "path": "data.json", "keys": ["count"]}]' \\
    --output report.md

Frontmatter value types:
  - Plain: "key": "value"
  - File: "key": {"type": "file", "path": "file.txt"}
  - JSON: "key": {"type": "json", "path": "data.json", "key": "nested.path"}

Body item types:
  - Text: {"header": "Title", "type": "text", "content": "..."}
  - File: {"header": "Title", "type": "file", "path": "file.md"}
  - JSON: {"header": "Title", "type": "json", "path": "data.json", "keys": ["key1", "key2"]}
        """
    )

    parser.add_argument(
        '--title', '-t',
        required=True,
        help='Document title (becomes H1)'
    )

    parser.add_argument(
        '--frontmatter', '-f',
        default='{}',
        help='Frontmatter as JSON object (default: {})'
    )

    parser.add_argument(
        '--body', '-b',
        default='[]',
        help='Body sections as JSON array (default: [])'
    )

    parser.add_argument(
        '--output', '-o',
        required=True,
        help='Output markdown file path (absolute or relative, e.g., ./file.md or /full/path/file.md or ~/Documents/file.md)'
    )

    parser.add_argument(
        '--base-path',
        help='Base path for resolving relative file references (default: current directory)'
    )

    args = parser.parse_args()

    # Parse JSON inputs
    try:
        frontmatter = json.loads(args.frontmatter)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in --frontmatter: {e}")
        sys.exit(1)

    try:
        body = json.loads(args.body)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in --body: {e}")
        sys.exit(1)

    # Validate body is a list
    if not isinstance(body, list):
        print("Error: --body must be a JSON array")
        sys.exit(1)

    # Determine base path
    if args.base_path:
        base_path = Path(args.base_path).resolve()
    else:
        base_path = Path.cwd()

    # Build the markdown
    try:
        print(f"Building markdown document...")
        print(f"  Title: {args.title}")
        print(f"  Frontmatter keys: {len(frontmatter)}")
        print(f"  Body sections: {len(body)}")
        print(f"  Base path: {base_path}")

        markdown = build_markdown(args.title, frontmatter, body, base_path)

        # Write output
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(markdown)

        # Report any errors encountered - PRINT ERRORS FIRST!
        if errors:
            print(f"\n{'='*60}")
            print(f"⚠️  ERRORS FOUND - Document created with placeholders:")
            print(f"{'='*60}")
            for error in errors:
                print(f"  ✗ {error}")
            print(f"{'='*60}\n")

            print(f"✓ Created: {output_path} (with placeholders)")
            print(f"  Size: {len(markdown):,} bytes")
            print(f"\n⚠️  Fix the {len(errors)} error(s) above and rebuild.")
            sys.exit(1)
        else:
            print(f"\n✓ Created: {output_path}")
            print(f"  Size: {len(markdown):,} bytes")
            print(f"✓ Success! No errors encountered.")
            sys.exit(0)

    except KeyboardInterrupt:
        print("\n\n⚠️  Process interrupted by user")
        sys.exit(1)

    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
