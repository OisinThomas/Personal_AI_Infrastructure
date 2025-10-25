#!/usr/bin/env python3
"""
Fast PDF to Markdown Transcriber with Parallel Processing

This script processes PDF files by converting each page to an image and using OpenAI's GPT-4o
with vision capabilities to transcribe the content into markdown format. Uses parallel processing
for faster conversion.

Usage:
    python pdf_to_markdown.py <pdf_path>
    
Example:
    python pdf_to_markdown.py ~/Documents/report.pdf
"""

import os
import base64
import sys
from pathlib import Path
from pdf2image import convert_from_path
from openai import OpenAI
from tqdm import tqdm
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
import argparse

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

def transcribe_page_with_openai(args):
    """
    Transcribe a single page image using OpenAI GPT-4o.
    Designed to be called in parallel.
    """
    image_path, page_num, client = args
    
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
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            max_tokens=4000
        )
        
        transcribed_text = response.choices[0].message.content
        return page_num, remove_code_block_markers(transcribed_text)
        
    except Exception as e:
        error_msg = f"Error transcribing page {page_num}: {str(e)}"
        print(f"\nWarning: {error_msg}")
        return page_num, f"[Error transcribing page {page_num}: {str(e)}]"

def process_pdf_to_markdown_parallel(pdf_path, images_folder, output_folder, client, max_workers=10):
    """
    Process a single PDF file to markdown using parallel processing.
    
    Args:
        pdf_path: Path to the PDF file
        images_folder: Folder containing extracted images
        output_folder: Folder to save markdown output
        client: OpenAI client instance
        max_workers: Number of parallel workers (default: 10)
    """
    pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
    pdf_images_folder = os.path.join(images_folder, pdf_name)
    
    # Extract images from PDF
    _, num_pages = extract_images_from_pdf(pdf_path, images_folder)
    
    print(f"\nProcessing {num_pages} pages with OpenAI GPT-4o using {max_workers} parallel workers...")
    
    # Prepare arguments for parallel processing
    tasks = []
    for page_num in range(1, num_pages + 1):
        image_path = os.path.join(pdf_images_folder, f"page_{page_num}.jpg")
        tasks.append((image_path, page_num, client))
    
    # Process pages in parallel
    results = {}
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(transcribe_page_with_openai, task): task[1] for task in tasks}
        
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
    parser = argparse.ArgumentParser(description='Convert PDF to Markdown using OpenAI GPT-4o with parallel processing')
    parser.add_argument('pdf_path', help='Path to the PDF file to convert')
    parser.add_argument('--workers', type=int, default=10, help='Number of parallel workers (default: 10)')
    parser.add_argument('--output-dir', default='./pdf_output', help='Output directory for markdown files')
    
    args = parser.parse_args()
    
    pdf_path = args.pdf_path
    max_workers = args.workers
    output_folder = args.output_dir
    
    if not os.path.exists(pdf_path):
        print(f"Error: PDF file not found: {pdf_path}")
        sys.exit(1)
    
    # Configuration
    images_folder = "./temp_images"
    
    # Create output directories
    os.makedirs(images_folder, exist_ok=True)
    os.makedirs(output_folder, exist_ok=True)
    
    # Initialize OpenAI client
    openai_api_key = os.getenv("OPENAI_API_KEY_DEFAULT")
    if not openai_api_key:
        print("Error: Please set your OpenAI API key in the environment variable OPENAI_API_KEY_DEFAULT.")
        sys.exit(1)
    
    client = OpenAI(api_key=openai_api_key)
    print("OpenAI client initialized successfully.")
    
    try:
        print(f"\n{'='*60}")
        print(f"Processing: {os.path.basename(pdf_path)}")
        print(f"Using {max_workers} parallel workers")
        print(f"{'='*60}")
        
        markdown_path = process_pdf_to_markdown_parallel(
            pdf_path, 
            images_folder, 
            output_folder, 
            client,
            max_workers=max_workers
        )
        
        file_size = os.path.getsize(markdown_path)
        print(f"\n✓ Successfully created: {os.path.basename(markdown_path)} ({file_size:,} bytes)")
        print(f"Output saved to: {markdown_path}")
        
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        sys.exit(1)
    
    finally:
        # Cleanup temporary images
        print(f"\nCleaning up temporary images in {images_folder}...")
        try:
            import shutil
            shutil.rmtree(images_folder)
            print("✓ Temporary images cleaned up successfully.")
        except Exception as e:
            print(f"Warning: Could not clean up temporary images: {e}")
    
    print("\nProcess completed!")

if __name__ == "__main__":
    main()
