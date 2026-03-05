#!/usr/bin/env python3
"""
Fast PDF to Markdown Transcriber with Multi-Model Support

This script processes PDF files by converting each page to an image and using various AI models
with vision capabilities to transcribe the content into markdown format. Uses parallel processing
for faster conversion.

Supports:
- OpenRouter models (Gemini, Claude, etc.)
- OpenAI models (GPT-4o, GPT-4o-mini)

Features:
- Multi-model support with easy shortcuts
- Parallel processing for speed
- System temp directory for temporary files (auto-cleanup)
- Output saved next to source PDF by default

Usage:
    python pdf_to_markdown.py <pdf_path> [OPTIONS]

Examples:
    # Default: Gemini 2.5 Flash, output next to PDF
    python pdf_to_markdown.py ~/Documents/report.pdf
    # Output: ~/Documents/report.md

    # Use Gemini Pro for better quality
    python pdf_to_markdown.py ~/Documents/report.pdf --model gemini-pro

    # Use Claude Sonnet with more parallel workers
    python pdf_to_markdown.py ~/Documents/report.pdf --model claude-sonnet --workers 20

    # Use OpenAI GPT-4o
    python pdf_to_markdown.py ~/Documents/report.pdf --model gpt-4o

    # Custom output directory
    python pdf_to_markdown.py ~/Documents/report.pdf --output-dir ~/converted_docs
    # Output: ~/converted_docs/report.md

    # Retry failed pages from an existing markdown file
    python pdf_to_markdown.py ~/Documents/report.pdf --retry
    # Retries pages that contain "[Error transcribing page" in report.md

    # Retry specific pages only
    python pdf_to_markdown.py ~/Documents/report.pdf --retry-pages 27,28,80,81
"""

import os
import base64
import sys
import tempfile
import shutil
import time
from pathlib import Path
from pdf2image import convert_from_path
from openai import OpenAI
import requests
from tqdm import tqdm
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
import argparse
from typing import Tuple, Dict, Any, Optional
from abc import ABC, abstractmethod

# Model shortcuts - maps short names to (provider, model_id)
MODELS = {
    # Gemini models (OpenRouter) - Fast and cost-effective
    'gemini-3-flash': ('openrouter', 'google/gemini-3-flash-preview'),
    'gemini-3-pro': ('openrouter', 'google/gemini-3-pro-preview'),
    'gemini-flash': ('openrouter', 'google/gemini-2.5-flash'),  # Alias
    'gemini-2.5-flash': ('openrouter', 'google/gemini-2.5-pro'),      # Alias
    
    # Claude models (OpenRouter)
    'claude-sonnet-4.5': ('openrouter', 'anthropic/claude-sonnet-4.5'),
    'claude-haiku-4.5': ('openrouter', 'anthropic/claude-haiku-4.5'),
    'claude-sonnet': ('openrouter', 'anthropic/claude-sonnet-4.5'),  # Alias
    'claude-haiku': ('openrouter', 'anthropic/claude-haiku-4.5'),    # Alias
    
    # OpenAI models (OpenAI)
    'gpt-4o': ('openai', 'gpt-4o'),
    'gpt-4o-mini': ('openai', 'gpt-4o-mini'),
}

# Default model
DEFAULT_MODEL = 'gemini-3-flash'


def remove_code_block_markers(text):
    """Remove markdown code block markers from text."""
    text = re.sub(r'```.*\n', '', text)
    text = re.sub(r'```\n', '', text)
    text = re.sub(r'```$', '', text)
    return text


def extract_images_from_pdf(pdf_path, output_folder, dpi=200):
    """
    Extract images from PDF at specified DPI.
    Lower DPI (200) for faster processing while maintaining readability.
    """
    pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
    images_folder = os.path.join(output_folder, pdf_name)
    os.makedirs(images_folder, exist_ok=True)
    
    print(f"Converting PDF to images at {dpi} DPI...")
    images = convert_from_path(pdf_path, dpi=dpi)
    
    for i, image in enumerate(images):
        image_path = os.path.join(images_folder, f"page_{i+1}.jpg")
        image.save(image_path, "JPEG", quality=85)  # Lower quality for faster processing
    
    return images_folder, len(images)


class BaseProvider(ABC):
    """Base class for AI vision providers."""
    
    def __init__(self, model: str, api_key: str):
        self.model = model
        self.api_key = api_key
    
    @abstractmethod
    def transcribe_page(self, image_path: str, page_num: int) -> Tuple[int, str]:
        """
        Transcribe a single page image.
        
        Args:
            image_path: Path to the image file
            page_num: Page number
            
        Returns:
            Tuple of (page_num, transcribed_text)
        """
        pass


class OpenAIProvider(BaseProvider):
    """OpenAI vision provider using OpenAI SDK."""
    
    def __init__(self, model: str, api_key: str):
        super().__init__(model, api_key)
        self.client = OpenAI(api_key=api_key)
    
    def transcribe_page(self, image_path: str, page_num: int) -> Tuple[int, str]:
        """Transcribe a single page using OpenAI GPT-4o."""
        if not os.path.exists(image_path):
            return page_num, f"Error: Image for page {page_num} not found."
        
        try:
            with open(image_path, "rb") as image_file:
                img_base64 = base64.b64encode(image_file.read()).decode('utf-8')
            
            content = [
                {
                    "type": "text", 
                    "text": "Transcribe this page image into clean markdown format. Preserve all text content, convert tables to markdown tables, format mathematical expressions appropriately, and maintain the document structure. Do not include code block markers (```) in your response. Be concise but accurate."
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{img_base64}"
                    }
                }
            ]
            
            messages = [{"role": "user", "content": content}]
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=4000
            )
            
            transcribed_text = response.choices[0].message.content
            return page_num, remove_code_block_markers(transcribed_text)
            
        except Exception as e:
            error_msg = f"Error transcribing page {page_num}: {str(e)}"
            print(f"\nWarning: {error_msg}")
            return page_num, f"[Error transcribing page {page_num}: {str(e)}]"


class OpenRouterProvider(BaseProvider):
    """OpenRouter vision provider using requests."""

    def __init__(self, model: str, api_key: str, max_retries: int = 3, retry_delay: float = 2.0):
        super().__init__(model, api_key)
        self.url = "https://openrouter.ai/api/v1/chat/completions"
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    def transcribe_page(self, image_path: str, page_num: int) -> Tuple[int, str]:
        """Transcribe a single page using OpenRouter models with retry logic."""
        if not os.path.exists(image_path):
            return page_num, f"[Error transcribing page {page_num}: Image not found]"

        try:
            with open(image_path, "rb") as image_file:
                img_base64 = base64.b64encode(image_file.read()).decode('utf-8')
        except Exception as e:
            return page_num, f"[Error transcribing page {page_num}: Failed to read image: {str(e)}]"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/yourusername/personal-ai-infrastructure",
            "X-Title": "Personal AI Infrastructure - PDF to Markdown",
        }

        content = [
            {
                "type": "text",
                "text": "Transcribe this page image into clean markdown format. Preserve all text content, convert tables to markdown tables, format mathematical expressions appropriately, and maintain the document structure. Do not include code block markers (```) in your response. Be concise but accurate."
            },
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{img_base64}"
                }
            }
        ]

        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": content}],
            "max_tokens": 4000
        }

        last_error = None
        for attempt in range(self.max_retries):
            try:
                response = requests.post(self.url, headers=headers, json=payload, timeout=120)
                response.raise_for_status()

                result = response.json()
                transcribed_text = result['choices'][0]['message']['content']
                return page_num, remove_code_block_markers(transcribed_text)

            except requests.exceptions.RequestException as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))  # Exponential backoff
                    continue
            except Exception as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
                    continue

        # All retries failed
        error_msg = f"Error transcribing page {page_num}: {str(last_error)}"
        print(f"\nWarning: {error_msg}")
        return page_num, f"[Error transcribing page {page_num}: {str(last_error)}]"


def create_provider(provider_type: str, model: str, api_key: str, max_retries: int = 3) -> BaseProvider:
    """
    Factory function to create the appropriate provider.

    Args:
        provider_type: 'openai' or 'openrouter'
        model: Model identifier
        api_key: API key for the provider
        max_retries: Number of retry attempts for failed requests

    Returns:
        Provider instance
    """
    if provider_type == 'openai':
        return OpenAIProvider(model, api_key)
    elif provider_type == 'openrouter':
        return OpenRouterProvider(model, api_key, max_retries=max_retries)
    else:
        raise ValueError(f"Unknown provider type: {provider_type}")


def find_failed_pages(markdown_path: str) -> list:
    """
    Find pages that failed to transcribe by looking for error markers.

    Args:
        markdown_path: Path to the markdown file

    Returns:
        List of page numbers that failed
    """
    failed_pages = []

    if not os.path.exists(markdown_path):
        return failed_pages

    with open(markdown_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Find all error markers like "[Error transcribing page X:"
    error_pattern = r'\[Error transcribing page (\d+):'
    matches = re.findall(error_pattern, content)

    failed_pages = sorted(set(int(m) for m in matches))
    return failed_pages


def retry_failed_pages(
    pdf_path: str,
    markdown_path: str,
    failed_pages: list,
    provider: BaseProvider,
    max_workers: int = 5
) -> int:
    """
    Retry transcribing failed pages and update the markdown file.

    Args:
        pdf_path: Path to the original PDF file
        markdown_path: Path to the markdown file to update
        failed_pages: List of page numbers to retry
        provider: AI provider instance
        max_workers: Number of parallel workers

    Returns:
        Number of pages successfully recovered
    """
    if not failed_pages:
        print("No failed pages to retry.")
        return 0

    print(f"\nRetrying {len(failed_pages)} failed pages: {failed_pages}")

    # Create temp directory for images
    temp_dir = tempfile.mkdtemp(prefix='pdf_retry_')

    try:
        # Read existing markdown
        with open(markdown_path, 'r', encoding='utf-8') as f:
            md_content = f.read()

        success_count = 0
        results = {}

        # Convert and transcribe each failed page
        with tqdm(total=len(failed_pages), desc="Retrying pages", unit="page") as pbar:
            for page_num in failed_pages:
                pbar.set_postfix(page=page_num)

                try:
                    # Convert just this page
                    images = convert_from_path(
                        pdf_path,
                        dpi=200,
                        first_page=page_num,
                        last_page=page_num
                    )

                    if not images:
                        pbar.update(1)
                        continue

                    # Save image temporarily
                    image_path = os.path.join(temp_dir, f"page_{page_num}.jpg")
                    images[0].save(image_path, "JPEG", quality=85)

                    # Transcribe
                    _, content = provider.transcribe_page(image_path, page_num)

                    # Check if it succeeded (no error marker)
                    if not content.startswith("[Error transcribing page"):
                        results[page_num] = content
                        success_count += 1

                except Exception as e:
                    print(f"\nFailed to retry page {page_num}: {e}")

                pbar.update(1)

        # Update markdown with successful retries
        for page_num, content in results.items():
            # Pattern to find the page section and replace its content
            pattern = rf"(## Page {page_num}\n\n)(.*?)(\n\n---|\Z)"

            def replacer(match):
                return f"{match.group(1)}{content}{match.group(3)}"

            md_content = re.sub(pattern, replacer, md_content, flags=re.DOTALL)

        # Write updated markdown
        with open(markdown_path, 'w', encoding='utf-8') as f:
            f.write(md_content)

        return success_count

    finally:
        # Cleanup temp directory
        try:
            shutil.rmtree(temp_dir)
        except Exception:
            pass


def resolve_model(model_name: str) -> Tuple[str, str]:
    """
    Resolve model shortcut to (provider, model_id).
    
    Args:
        model_name: Short name or full model ID
        
    Returns:
        Tuple of (provider_type, model_id)
    """
    # If it's a shortcut, resolve it
    if model_name in MODELS:
        return MODELS[model_name]
    
    # Otherwise, try to infer provider from model name
    if model_name.startswith('gpt-'):
        return ('openai', model_name)
    elif '/' in model_name:
        # Assume OpenRouter format (provider/model)
        return ('openrouter', model_name)
    else:
        # Default to OpenRouter
        return ('openrouter', model_name)


def get_api_key(provider_type: str) -> str:
    """
    Get API key for the specified provider.
    
    Args:
        provider_type: 'openai' or 'openrouter'
        
    Returns:
        API key string
    """
    if provider_type == 'openai':
        # Try multiple environment variable names
        api_key = os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY_DEFAULT")
        if not api_key:
            print("Error: OpenAI API key not found.")
            print("Please set one of: OPENAI_API_KEY or OPENAI_API_KEY_DEFAULT")
            sys.exit(1)
        return api_key
    
    elif provider_type == 'openrouter':
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            print("Error: OpenRouter API key not found.")
            print("Please set: OPENROUTER_API_KEY")
            print("\nGet your key at: https://openrouter.ai/keys")
            sys.exit(1)
        return api_key
    
    else:
        raise ValueError(f"Unknown provider type: {provider_type}")


def transcribe_page(args):
    """
    Transcribe a single page image using the provider.
    Designed to be called in parallel.
    """
    image_path, page_num, provider = args
    return provider.transcribe_page(image_path, page_num)


def process_pdf_to_markdown_parallel(
    pdf_path: str,
    images_folder: str,
    output_folder: str,
    provider: BaseProvider,
    max_workers: int = 10
) -> str:
    """
    Process a single PDF file to markdown using parallel processing.
    
    Args:
        pdf_path: Path to the PDF file
        images_folder: Folder containing extracted images
        output_folder: Folder to save markdown output
        provider: AI provider instance
        max_workers: Number of parallel workers (default: 10)
        
    Returns:
        Path to the generated markdown file
    """
    pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
    pdf_images_folder = os.path.join(images_folder, pdf_name)
    
    # Extract images from PDF
    _, num_pages = extract_images_from_pdf(pdf_path, images_folder)
    
    print(f"\nProcessing {num_pages} pages with {provider.model} using {max_workers} parallel workers...")
    
    # Prepare arguments for parallel processing
    tasks = []
    for page_num in range(1, num_pages + 1):
        image_path = os.path.join(pdf_images_folder, f"page_{page_num}.jpg")
        tasks.append((image_path, page_num, provider))
    
    # Process pages in parallel
    results = {}
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(transcribe_page, task): task[1] for task in tasks}
        
        with tqdm(total=num_pages, desc=f"Transcribing {pdf_name}", unit="page") as pbar:
            for future in as_completed(futures):
                page_num, content = future.result()
                results[page_num] = content
                pbar.update(1)
    
    # Assemble markdown in correct page order
    all_markdown = []
    all_markdown.append(f"# {pdf_name}\n\n")
    
    for page_num in range(1, num_pages + 1):
        all_markdown.append(f"## Page {page_num}\n\n")
        all_markdown.append(results[page_num])
        all_markdown.append("\n\n---\n\n")
    
    # Save markdown file
    markdown_filename = f"{pdf_name}.md"
    markdown_path = os.path.join(output_folder, markdown_filename)
    
    with open(markdown_path, "w", encoding="utf-8") as f:
        f.write("".join(all_markdown))
    
    return markdown_path


def main():
    """Main function to process a single PDF file."""
    parser = argparse.ArgumentParser(
        description='Convert PDF to Markdown using AI vision models with parallel processing',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Available model shortcuts:
  Gemini (OpenRouter):
    gemini-2.5-flash, gemini-flash    - Fast and cost-effective (default)
    gemini-2.5-pro, gemini-pro        - More capable
  
  Claude (OpenRouter):
    claude-sonnet-4.5, claude-sonnet  - High quality
    claude-haiku-4.5, claude-haiku    - Fast and efficient
  
  OpenAI:
    gpt-4o                            - Latest GPT-4 with vision
    gpt-4o-mini                       - Smaller, faster GPT-4

Environment variables required:
  OPENROUTER_API_KEY - For OpenRouter models (Gemini, Claude)
  OPENAI_API_KEY     - For OpenAI models (GPT-4o)

Examples:
  # Default (Gemini 2.5 Flash)
  python pdf_to_markdown.py document.pdf

  # Use Gemini Pro
  python pdf_to_markdown.py document.pdf --model gemini-pro

  # Use Claude Sonnet with more workers
  python pdf_to_markdown.py document.pdf --model claude-sonnet --workers 20

  # Use OpenAI GPT-4o
  python pdf_to_markdown.py document.pdf --model gpt-4o

  # Retry failed pages (auto-detects from error markers)
  python pdf_to_markdown.py document.pdf --retry

  # Retry specific pages only
  python pdf_to_markdown.py document.pdf --retry-pages 27,28,80

  # Increase retry attempts per page
  python pdf_to_markdown.py document.pdf --max-retries 5
"""
    )
    
    parser.add_argument('pdf_path', help='Path to the PDF file to convert')
    parser.add_argument(
        '--model', '-m',
        default=DEFAULT_MODEL,
        help=f'Model to use (default: {DEFAULT_MODEL}). See available models above.'
    )
    parser.add_argument(
        '--workers',
        type=int,
        default=10,
        help='Number of parallel workers (default: 10)'
    )
    parser.add_argument(
        '--output-dir',
        help='Output directory for markdown files (default: same directory as PDF)'
    )
    parser.add_argument(
        '--provider',
        choices=['openai', 'openrouter'],
        help='Override provider auto-detection'
    )
    parser.add_argument(
        '--retry',
        action='store_true',
        help='Retry failed pages from existing markdown file (auto-detects errors)'
    )
    parser.add_argument(
        '--retry-pages',
        type=str,
        help='Retry specific pages (comma-separated, e.g., "27,28,80,81")'
    )
    parser.add_argument(
        '--max-retries',
        type=int,
        default=3,
        help='Maximum retry attempts per page (default: 3)'
    )

    args = parser.parse_args()
    
    pdf_path = args.pdf_path
    max_workers = args.workers
    
    if not os.path.exists(pdf_path):
        print(f"Error: PDF file not found: {pdf_path}")
        sys.exit(1)
    
    # Determine output folder
    if args.output_dir:
        # User specified custom output directory
        output_folder = args.output_dir
    else:
        # Default: same directory as the PDF
        output_folder = os.path.dirname(os.path.abspath(pdf_path))
    
    # Resolve model
    if args.provider:
        # Provider explicitly specified
        provider_type = args.provider
        model_id = args.model
    else:
        # Auto-detect from model name
        provider_type, model_id = resolve_model(args.model)
    
    print(f"Model: {args.model}")
    print(f"Provider: {provider_type}")
    print(f"Model ID: {model_id}")
    
    # Get API key
    api_key = get_api_key(provider_type)

    # Create provider with retry settings
    provider = create_provider(provider_type, model_id, api_key, max_retries=args.max_retries)
    print(f"Provider initialized successfully.")

    # Determine markdown path
    pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
    markdown_path = os.path.join(output_folder, f"{pdf_name}.md")

    # Handle retry modes
    if args.retry or args.retry_pages:
        # Retry mode - update existing markdown file
        if not os.path.exists(markdown_path):
            print(f"Error: Markdown file not found: {markdown_path}")
            print("Run without --retry first to create the initial conversion.")
            sys.exit(1)

        if args.retry_pages:
            # User specified specific pages
            failed_pages = [int(p.strip()) for p in args.retry_pages.split(',')]
        else:
            # Auto-detect failed pages
            failed_pages = find_failed_pages(markdown_path)

        if not failed_pages:
            print("No failed pages found to retry.")
            sys.exit(0)

        print(f"\n{'='*60}")
        print(f"RETRY MODE: {os.path.basename(pdf_path)}")
        print(f"Found {len(failed_pages)} pages to retry: {failed_pages}")
        print(f"{'='*60}")

        success_count = retry_failed_pages(
            pdf_path,
            markdown_path,
            failed_pages,
            provider,
            max_workers=min(max_workers, len(failed_pages))
        )

        file_size = os.path.getsize(markdown_path)
        print(f"\n✓ Retry complete: {success_count}/{len(failed_pages)} pages recovered")
        print(f"Updated: {markdown_path} ({file_size:,} bytes)")

        # Check for remaining failures
        remaining = find_failed_pages(markdown_path)
        if remaining:
            print(f"\n⚠ {len(remaining)} pages still failed: {remaining}")
            print("Run again with --retry to attempt again.")

        print("\nProcess completed!")
        return

    # Normal mode - full conversion
    # Create output directory if it doesn't exist
    os.makedirs(output_folder, exist_ok=True)

    # Create unique temp directory in system temp
    temp_dir = tempfile.mkdtemp(prefix='pdf_to_markdown_')
    images_folder = temp_dir

    print(f"Temp directory: {temp_dir}")
    print(f"Output directory: {output_folder}")

    try:
        print(f"\n{'='*60}")
        print(f"Processing: {os.path.basename(pdf_path)}")
        print(f"Using {max_workers} parallel workers")
        print(f"{'='*60}")

        markdown_path = process_pdf_to_markdown_parallel(
            pdf_path,
            images_folder,
            output_folder,
            provider,
            max_workers=max_workers
        )

        file_size = os.path.getsize(markdown_path)
        print(f"\n✓ Successfully created: {os.path.basename(markdown_path)} ({file_size:,} bytes)")
        print(f"Output saved to: {markdown_path}")

        # Check for failed pages and offer retry
        failed_pages = find_failed_pages(markdown_path)
        if failed_pages:
            print(f"\n⚠ {len(failed_pages)} pages failed: {failed_pages}")
            print(f"Run with --retry to attempt recovery:")
            print(f"  {sys.argv[0]} \"{pdf_path}\" --retry")

    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    finally:
        # Cleanup temporary directory
        print(f"\nCleaning up temporary files in {temp_dir}...")
        try:
            shutil.rmtree(temp_dir)
            print("✓ Temporary files cleaned up successfully.")
        except Exception as e:
            print(f"Warning: Could not clean up temporary files: {e}")

    print("\nProcess completed!")


if __name__ == "__main__":
    main()
