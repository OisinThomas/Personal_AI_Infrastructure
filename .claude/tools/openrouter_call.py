#!/usr/bin/env python3
"""
OpenRouter API Caller

Call OpenRouter models with flexible prompt composition and conversation threading.

Usage:
    ./openrouter_call.py --model MODEL --user "prompt" --output file.md

Examples:
    # Simple call
    ./openrouter_call.py \
      --model gemini-2.5-flash \
      --user "Explain quantum computing" \
      --output tmp/quantum.md

    # With system message
    ./openrouter_call.py \
      --model claude-sonnet-4.5 \
      --system "You are a helpful coding assistant" \
      --user "Write a Python function to sort a list" \
      --output tmp/code.py

    # Multi-part composition
    ./openrouter_call.py \
      --model gemini-2.5-pro \
      --system '[
        {"type": "file", "path": "prompts/coder.md"},
        {"type": "text", "content": "\n\n## Context:\n"},
        {"type": "files", "paths": ["src/main.py", "src/utils.py"], "separator": "\n----\n"}
      ]' \
      --user "Refactor this code" \
      --output tmp/refactor.md

    # Continue conversation
    ./openrouter_call.py \
      --model claude-sonnet-4.5 \
      --continue-thread 20250129-a3f2 \
      --user "Can you explain that in simpler terms?" \
      --output tmp/response2.md

    # Structured output
    ./openrouter_call.py \
      --model gemini-2.5-pro \
      --user "Extract key points from this text" \
      --schema '{"type": "object", "properties": {"points": {"type": "array", "items": {"type": "string"}}}}' \
      --output tmp/extracted.json

    # List threads
    ./openrouter_call.py --list-threads

    # Show thread history
    ./openrouter_call.py --show-thread 20250129-a3f2
"""

import sys
import json
import os
import argparse
import hashlib
import requests
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, List, Union, Optional

# Model shortcuts - easy to add new models
MODELS = {
    'gemini-2.5-flash': 'google/gemini-2.5-flash',
    'gemini-2.5-pro': 'google/gemini-2.5-pro',
    'gemini-flash': 'google/gemini-2.5-flash',  # Alias
    'gemini-pro': 'google/gemini-2.5-pro',      # Alias
    'claude-sonnet-4.5': 'anthropic/claude-sonnet-4.5',
    'claude-haiku-4.5': 'anthropic/claude-haiku-4.5',
    'claude-sonnet': 'anthropic/claude-sonnet-4.5',  # Alias
    'claude-haiku': 'anthropic/claude-haiku-4.5',    # Alias
}

# Global error tracking
errors = []


def get_api_key() -> str:
    """Get OpenRouter API key from environment."""
    api_key = os.environ.get('OPENROUTER_API_KEY')
    if not api_key:
        print("Error: OPENROUTER_API_KEY environment variable not set")
        print("\nSet it with:")
        print("  export OPENROUTER_API_KEY='your-key-here'")
        sys.exit(1)
    return api_key


def resolve_model(model_name: str) -> str:
    """
    Resolve model shortcut to full OpenRouter model ID.
    
    Args:
        model_name: Short name or full model ID
        
    Returns:
        Full OpenRouter model ID
    """
    # If it's a shortcut, resolve it
    if model_name in MODELS:
        return MODELS[model_name]
    
    # Otherwise assume it's a full model ID
    return model_name


def resolve_content_part(part: Union[str, Dict[str, Any]], base_path: Path) -> str:
    """
    Resolve a content part (text, file, json, or files).
    
    Args:
        part: Content part (string or dict with type)
        base_path: Base path for resolving relative files
        
    Returns:
        Resolved content as string
    """
    # If it's a plain string, return it
    if isinstance(part, str):
        return part
    
    # Must be a dict with 'type'
    if not isinstance(part, dict) or 'type' not in part:
        errors.append(f"Invalid content part: {part}")
        return f"[INVALID PART: {part}]"
    
    part_type = part['type']
    
    if part_type == 'text':
        return part.get('content', '')
    
    elif part_type == 'file':
        path = base_path / part['path']
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            errors.append(f"File not found: {path}")
            return f"[FILE NOT FOUND: {path}]"
        except Exception as e:
            errors.append(f"Error reading {path}: {e}")
            return f"[ERROR READING: {path}]"
    
    elif part_type == 'json':
        path = base_path / part['path']
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Navigate to the key using dot notation
            key_path = part['key']
            value = data
            for key in key_path.split('.'):
                value = value[key]
            
            # Return as string (JSON if complex type)
            if isinstance(value, (dict, list)):
                return json.dumps(value, indent=2)
            return str(value)
            
        except FileNotFoundError:
            errors.append(f"File not found: {path}")
            return f"[FILE NOT FOUND: {path}]"
        except KeyError as e:
            errors.append(f"Key not found in {path}: {e}")
            return f"[KEY NOT FOUND: {e}]"
        except Exception as e:
            errors.append(f"Error reading JSON from {path}: {e}")
            return f"[ERROR READING JSON: {path}]"
    
    elif part_type == 'files':
        paths = part.get('paths', [])
        separator = part.get('separator', '\n')
        
        contents = []
        for file_path in paths:
            path = base_path / file_path
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    contents.append(f.read())
            except FileNotFoundError:
                errors.append(f"File not found: {path}")
                contents.append(f"[FILE NOT FOUND: {path}]")
            except Exception as e:
                errors.append(f"Error reading {path}: {e}")
                contents.append(f"[ERROR READING: {path}]")
        
        return separator.join(contents)
    
    else:
        errors.append(f"Unknown content type: {part_type}")
        return f"[UNKNOWN TYPE: {part_type}]"


def compose_message(content: Union[str, List], base_path: Path) -> str:
    """
    Compose a message from parts.
    
    Args:
        content: String, dict, or list of content parts
        base_path: Base path for resolving files
        
    Returns:
        Composed message string
    """
    # If it's a string, return as-is
    if isinstance(content, str):
        return content
    
    # If it's a single dict, resolve it
    if isinstance(content, dict):
        return resolve_content_part(content, base_path)
    
    # If it's a list, resolve and concatenate all parts
    if isinstance(content, list):
        parts = [resolve_content_part(part, base_path) for part in content]
        return ''.join(parts)
    
    errors.append(f"Invalid message content type: {type(content)}")
    return f"[INVALID CONTENT: {content}]"


def generate_thread_id() -> str:
    """Generate a unique thread ID."""
    timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    random_hash = hashlib.md5(os.urandom(8)).hexdigest()[:4]
    return f"{timestamp}-{random_hash}"


def load_thread(thread_id: str, threads_dir: Path) -> Dict[str, Any]:
    """Load a conversation thread."""
    thread_path = threads_dir / f"{thread_id}.json"
    
    if not thread_path.exists():
        print(f"Error: Thread not found: {thread_id}")
        sys.exit(1)
    
    with open(thread_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_thread(thread_data: Dict[str, Any], threads_dir: Path) -> None:
    """Save a conversation thread."""
    threads_dir.mkdir(parents=True, exist_ok=True)
    thread_path = threads_dir / f"{thread_data['thread_id']}.json"
    
    with open(thread_path, 'w', encoding='utf-8') as f:
        json.dump(thread_data, f, indent=2)


def list_threads(threads_dir: Path) -> None:
    """List all available threads."""
    if not threads_dir.exists():
        print("No threads found.")
        return
    
    thread_files = sorted(threads_dir.glob("*.json"), reverse=True)
    
    if not thread_files:
        print("No threads found.")
        return
    
    print(f"\nAvailable threads ({len(thread_files)}):\n")
    
    for thread_file in thread_files:
        try:
            with open(thread_file, 'r', encoding='utf-8') as f:
                thread_data = json.load(f)
            
            thread_id = thread_data['thread_id']
            model = thread_data.get('model', 'unknown')
            created = thread_data.get('created_at', 'unknown')
            msg_count = len(thread_data.get('messages', []))
            
            # Get first user message preview
            preview = "..."
            for msg in thread_data.get('messages', []):
                if msg['role'] == 'user':
                    preview = msg['content'][:60]
                    if len(msg['content']) > 60:
                        preview += "..."
                    break
            
            print(f"  {thread_id}")
            print(f"    Model: {model}")
            print(f"    Created: {created}")
            print(f"    Messages: {msg_count}")
            print(f"    Preview: {preview}")
            print()
            
        except Exception as e:
            print(f"  {thread_file.stem} (error reading: {e})")
    
    print(f"Continue a thread with: --continue-thread THREAD_ID")


def show_thread(thread_id: str, threads_dir: Path) -> None:
    """Display thread history."""
    thread_data = load_thread(thread_id, threads_dir)
    
    print(f"\nThread: {thread_data['thread_id']}")
    print(f"Model: {thread_data.get('model', 'unknown')}")
    print(f"Created: {thread_data.get('created_at', 'unknown')}")
    print(f"\nMessages ({len(thread_data.get('messages', []))}):\n")
    print("=" * 80)
    
    for i, msg in enumerate(thread_data.get('messages', []), 1):
        role = msg['role'].upper()
        content = msg['content']
        
        print(f"\n[{i}] {role}:")
        print("-" * 80)
        print(content)
    
    print("\n" + "=" * 80)


def delete_thread(thread_id: str, threads_dir: Path) -> None:
    """Delete a thread."""
    thread_path = threads_dir / f"{thread_id}.json"
    
    if not thread_path.exists():
        print(f"Error: Thread not found: {thread_id}")
        sys.exit(1)
    
    thread_path.unlink()
    print(f"✓ Deleted thread: {thread_id}")


def call_openrouter(
    model: str,
    messages: List[Dict[str, str]],
    api_key: str,
    schema: Optional[Dict] = None,
    tools: Optional[List[Dict]] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Call OpenRouter API.
    
    Args:
        model: OpenRouter model ID
        messages: List of message dicts
        api_key: OpenRouter API key
        schema: Optional JSON schema for structured output
        tools: Optional tool definitions
        temperature: Optional temperature parameter
        max_tokens: Optional max tokens parameter
        
    Returns:
        API response dict
    """
    url = "https://openrouter.ai/api/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/yourusername/personal-ai-infrastructure",
        "X-Title": "Personal AI Infrastructure",
    }
    
    payload = {
        "model": model,
        "messages": messages,
    }
    
    # Add optional parameters
    if schema:
        payload["response_format"] = {
            "type": "json_schema",
            "json_schema": {
                "name": "response",
                "strict": True,
                "schema": schema
            }
        }
    
    if tools:
        payload["tools"] = tools
    
    if temperature is not None:
        payload["temperature"] = temperature
    
    if max_tokens is not None:
        payload["max_tokens"] = max_tokens
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()
    
    except requests.exceptions.RequestException as e:
        print(f"Error calling OpenRouter API: {e}")
        if e.response is not None and hasattr(e.response, 'text'):
            print(f"Response: {e.response.text}")
        sys.exit(1)


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Call OpenRouter models with flexible prompt composition',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    # Model selection
    parser.add_argument(
        '--model', '-m',
        help='Model name (shortcut or full ID). Available shortcuts: ' + ', '.join(MODELS.keys())
    )
    
    # Message composition
    parser.add_argument(
        '--system', '-s',
        help='System message (string, JSON object, or JSON array of parts)'
    )
    
    parser.add_argument(
        '--user', '-u',
        help='User message (string, JSON object, or JSON array of parts)'
    )
    
    # Thread management
    parser.add_argument(
        '--continue-thread',
        help='Continue an existing conversation thread'
    )
    
    parser.add_argument(
        '--list-threads',
        action='store_true',
        help='List all available threads'
    )
    
    parser.add_argument(
        '--show-thread',
        help='Show thread history'
    )
    
    parser.add_argument(
        '--delete-thread',
        help='Delete a thread'
    )
    
    # Advanced options
    parser.add_argument(
        '--schema',
        help='JSON schema for structured output (JSON object)'
    )
    
    parser.add_argument(
        '--tools',
        help='Tool definitions (JSON array or file reference)'
    )
    
    parser.add_argument(
        '--temperature',
        type=float,
        help='Temperature parameter (0.0-2.0)'
    )
    
    parser.add_argument(
        '--max-tokens',
        type=int,
        help='Maximum tokens in response'
    )
    
    # Output
    parser.add_argument(
        '--output', '-o',
        help='Output file path (required for API calls)'
    )
    
    parser.add_argument(
        '--base-path',
        help='Base path for resolving file references (default: current directory)'
    )
    
    args = parser.parse_args()
    
    # Determine base path
    base_path = Path(args.base_path).resolve() if args.base_path else Path.cwd()
    
    # Thread directory
    threads_dir = base_path / 'tmp' / 'threads'
    
    # Handle thread management commands
    if args.list_threads:
        list_threads(threads_dir)
        sys.exit(0)
    
    if args.show_thread:
        show_thread(args.show_thread, threads_dir)
        sys.exit(0)
    
    if args.delete_thread:
        delete_thread(args.delete_thread, threads_dir)
        sys.exit(0)
    
    # Validate required arguments for API calls
    if not args.model:
        print("Error: --model is required for API calls")
        sys.exit(1)
    
    if not args.output:
        print("Error: --output is required for API calls")
        sys.exit(1)
    
    # Get API key
    api_key = get_api_key()
    
    # Resolve model
    model = resolve_model(args.model)
    
    print(f"Calling OpenRouter API...")
    print(f"  Model: {model}")
    
    # Build messages
    messages = []
    
    # Load existing thread if continuing
    thread_id = None
    if args.continue_thread:
        thread_data = load_thread(args.continue_thread, threads_dir)
        messages = thread_data['messages']
        thread_id = thread_data['thread_id']
        print(f"  Continuing thread: {thread_id}")
        print(f"  Previous messages: {len(messages)}")
    else:
        # New thread
        thread_id = generate_thread_id()
        
        # Add system message if provided
        if args.system:
            try:
                system_content = json.loads(args.system)
            except json.JSONDecodeError:
                system_content = args.system
            
            system_message = compose_message(system_content, base_path)
            messages.append({
                "role": "system",
                "content": system_message
            })
            print(f"  System message: {len(system_message)} chars")
    
    # Add user message
    if not args.user:
        print("Error: --user message is required")
        sys.exit(1)
    
    try:
        user_content = json.loads(args.user)
    except json.JSONDecodeError:
        user_content = args.user
    
    user_message = compose_message(user_content, base_path)
    messages.append({
        "role": "user",
        "content": user_message
    })
    print(f"  User message: {len(user_message)} chars")
    
    # Parse optional parameters
    schema = None
    if args.schema:
        try:
            schema = json.loads(args.schema)
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON in --schema: {e}")
            sys.exit(1)
    
    tools = None
    if args.tools:
        try:
            tools_content = json.loads(args.tools)
            if isinstance(tools_content, dict) and tools_content.get('type') == 'file':
                # Load from file
                tools_path = base_path / tools_content['path']
                with open(tools_path, 'r', encoding='utf-8') as f:
                    loaded_tools = json.load(f)
                    # Ensure it's a list
                    if isinstance(loaded_tools, list):
                        tools = loaded_tools
                    else:
                        print(f"Error: Tools file must contain a JSON array")
                        sys.exit(1)
            elif isinstance(tools_content, list):
                tools = tools_content
            else:
                print(f"Error: --tools must be a JSON array or file reference")
                sys.exit(1)
        except (json.JSONDecodeError, FileNotFoundError) as e:
            print(f"Error: Invalid tools configuration: {e}")
            sys.exit(1)
    
    # Report any errors from composition
    if errors:
        print(f"\n{'='*60}")
        print(f"⚠️  ERRORS during message composition:")
        print(f"{'='*60}")
        for error in errors:
            print(f"  ✗ {error}")
        print(f"{'='*60}\n")
        print("Proceeding with placeholders...")
    
    # Call API
    try:
        response = call_openrouter(
            model=model,
            messages=messages,
            api_key=api_key,
            schema=schema,
            tools=tools,
            temperature=args.temperature,
            max_tokens=args.max_tokens,
        )
        
        # Extract assistant response
        assistant_message = response['choices'][0]['message']
        assistant_content = assistant_message.get('content', '')
        
        # Add to messages
        messages.append({
            "role": "assistant",
            "content": assistant_content
        })
        
        # Save thread (conversation history only)
        thread_data = {
            "thread_id": thread_id,
            "model": model,
            "created_at": datetime.now().isoformat(),
            "messages": messages
        }
        save_thread(thread_data, threads_dir)
        
        # Save raw API response separately
        response_dir = base_path / 'tmp' / 'responses'
        response_dir.mkdir(parents=True, exist_ok=True)
        response_path = response_dir / f"{thread_id}_response.json"
        
        with open(response_path, 'w', encoding='utf-8') as f:
            json.dump(response, f, indent=2)
        
        # Save output content
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(assistant_content)
        
        # Report success
        print(f"\n✓ Output saved to: {output_path}")
        print(f"  Size: {len(assistant_content):,} chars")
        print(f"✓ Thread ID: {thread_id}")
        print(f"  Thread history: {threads_dir / thread_id}.json")
        print(f"  Raw API response: {response_path}")
        print(f"\nContinue with: --continue-thread {thread_id}")
        
        # Show usage stats if available
        if 'usage' in response:
            usage = response['usage']
            print(f"\nUsage:")
            print(f"  Prompt tokens: {usage.get('prompt_tokens', 0):,}")
            print(f"  Completion tokens: {usage.get('completion_tokens', 0):,}")
            print(f"  Total tokens: {usage.get('total_tokens', 0):,}")
        
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
