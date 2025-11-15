#!/usr/bin/env python3
"""
EPUB to Markdown converter for source books.
Extracts text content from EPUB files and converts them to Markdown format.
"""

import os
import sys
import re
from pathlib import Path
from typing import Optional, List, Tuple
import ebooklib
from ebooklib import epub
import html2text


def sanitize_filename(filename: str) -> str:
    """Convert a filename to a safe format for filesystem."""
    # Remove or replace invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Remove leading/trailing spaces and dots
    filename = filename.strip(' .')
    return filename


def extract_epub_metadata(book: epub.EpubBook) -> dict:
    """Extract metadata from EPUB book."""
    metadata = {
        'title': 'Untitled',
        'author': 'Unknown',
        'language': 'en',
        'publisher': '',
        'date': '',
    }
    
    # Extract title
    if book.get_metadata('DC', 'title'):
        metadata['title'] = book.get_metadata('DC', 'title')[0][0]
    
    # Extract author
    if book.get_metadata('DC', 'creator'):
        authors = [item[0] for item in book.get_metadata('DC', 'creator')]
        metadata['author'] = ', '.join(authors)
    
    # Extract language
    if book.get_metadata('DC', 'language'):
        metadata['language'] = book.get_metadata('DC', 'language')[0][0]
    
    # Extract publisher
    if book.get_metadata('DC', 'publisher'):
        metadata['publisher'] = book.get_metadata('DC', 'publisher')[0][0]
    
    # Extract date
    if book.get_metadata('DC', 'date'):
        metadata['date'] = book.get_metadata('DC', 'date')[0][0]
    
    return metadata


def get_chapter_order(book: epub.EpubBook) -> List[Tuple[str, str]]:
    """Get chapters in reading order from spine."""
    chapters = []
    spine_items = book.spine
    
    # Create a mapping of item IDs to items for faster lookup
    items_by_id = {}
    for item in book.items:
        if hasattr(item, 'id') and item.id:
            items_by_id[item.id] = item
    
    for item_id, _ in spine_items:
        if item_id in items_by_id:
            item = items_by_id[item_id]
            if item and item.get_type() == ebooklib.ITEM_DOCUMENT:
                # Get the file name
                file_name = item.get_name()
                chapters.append((item_id, file_name))
    
    return chapters


def html_to_markdown(html_content: bytes) -> str:
    """Convert HTML content to Markdown."""
    # Configure html2text converter
    h = html2text.HTML2Text()
    h.ignore_links = False
    h.ignore_images = False
    h.ignore_emphasis = False
    h.body_width = 0  # Don't wrap lines
    h.unicode_snob = True  # Use unicode characters
    h.mark_code = True  # Mark code blocks
    
    # Convert HTML to Markdown
    try:
        markdown_text = h.handle(html_content.decode('utf-8'))
    except UnicodeDecodeError:
        # Try other encodings
        try:
            markdown_text = h.handle(html_content.decode('latin-1'))
        except:
            markdown_text = h.handle(html_content.decode('utf-8', errors='ignore'))
    
    return markdown_text


def extract_chapter_content(book: epub.EpubBook, item_id: str) -> Optional[str]:
    """Extract and convert a chapter's content to Markdown."""
    # Find item by ID
    item = None
    for book_item in book.items:
        if hasattr(book_item, 'id') and book_item.id == item_id:
            item = book_item
            break
    
    if not item or item.get_type() != ebooklib.ITEM_DOCUMENT:
        return None
    
    content = item.get_content()
    markdown_content = html_to_markdown(content)
    
    # Clean up the markdown
    markdown_content = markdown_content.strip()
    
    # Remove excessive blank lines
    markdown_content = re.sub(r'\n{3,}', '\n\n', markdown_content)
    
    return markdown_content


def convert_epub_to_markdown(epub_path: str, output_dir: Optional[str] = None) -> str:
    """
    Convert an EPUB file to Markdown.
    
    Args:
        epub_path: Path to the EPUB file
        output_dir: Directory to save the Markdown file (default: same as EPUB)
    
    Returns:
        Path to the generated Markdown file
    """
    epub_path = Path(epub_path)
    if not epub_path.exists():
        raise FileNotFoundError(f"EPUB file not found: {epub_path}")
    
    print(f"Reading EPUB: {epub_path.name}")
    
    # Read the EPUB
    try:
        book = epub.read_epub(str(epub_path))
    except Exception as e:
        raise ValueError(f"Error reading EPUB file: {e}")
    
    # Extract metadata
    metadata = extract_epub_metadata(book)
    print(f"  Title: {metadata['title']}")
    print(f"  Author: {metadata['author']}")
    
    # Get chapters in order
    chapters = get_chapter_order(book)
    print(f"  Found {len(chapters)} chapters")
    
    # Determine output path
    if output_dir:
        output_path = Path(output_dir)
    else:
        output_path = epub_path.parent
    
    # Create output filename
    safe_title = sanitize_filename(metadata['title'])
    output_file = output_path / f"{safe_title}.md"
    
    # Build Markdown content
    markdown_parts = []
    
    # Add frontmatter/metadata
    markdown_parts.append("---")
    markdown_parts.append(f"title: \"{metadata['title']}\"")
    markdown_parts.append(f"author: \"{metadata['author']}\"")
    if metadata['publisher']:
        markdown_parts.append(f"publisher: \"{metadata['publisher']}\"")
    if metadata['date']:
        markdown_parts.append(f"date: \"{metadata['date']}\"")
    markdown_parts.append(f"language: \"{metadata['language']}\"")
    markdown_parts.append(f"source: \"{epub_path.name}\"")
    markdown_parts.append("---")
    markdown_parts.append("")
    
    # Add title
    markdown_parts.append(f"# {metadata['title']}")
    if metadata['author']:
        markdown_parts.append(f"\n*by {metadata['author']}*")
    markdown_parts.append("")
    
    # Extract and add chapters
    for i, (item_id, file_name) in enumerate(chapters, 1):
        print(f"  Processing chapter {i}/{len(chapters)}: {file_name}")
        chapter_content = extract_chapter_content(book, item_id)
        
        if chapter_content:
            # Add chapter separator (except for first chapter)
            if i > 1:
                markdown_parts.append("\n\n---\n\n")
            
            markdown_parts.append(chapter_content)
    
    # Write to file
    output_file.parent.mkdir(parents=True, exist_ok=True)
    full_markdown = "\n".join(markdown_parts)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(full_markdown)
    
    print(f"\nMarkdown saved to: {output_file}")
    return str(output_file)


def convert_all_epubs(sources_dir: str = 'sources', output_dir: Optional[str] = None):
    """Convert all EPUB files in the sources directory to Markdown."""
    sources_path = Path(sources_dir)
    
    if not sources_path.exists():
        print(f"Error: Sources directory not found: {sources_dir}")
        return
    
    # Find all EPUB files
    epub_files = list(sources_path.glob('*.epub'))
    
    if not epub_files:
        print(f"No EPUB files found in {sources_dir}")
        return
    
    print(f"Found {len(epub_files)} EPUB file(s) to convert\n")
    
    # Convert each EPUB
    for epub_file in epub_files:
        try:
            convert_epub_to_markdown(epub_file, output_dir)
            print()
        except Exception as e:
            print(f"Error converting {epub_file.name}: {e}\n")
            continue
    
    print("Conversion complete!")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Convert EPUB files to Markdown format'
    )
    parser.add_argument(
        'epub_file',
        nargs='?',
        help='Path to EPUB file to convert (if not provided, converts all EPUBs in sources/)'
    )
    parser.add_argument(
        '-o', '--output',
        help='Output directory for Markdown files (default: same as source)'
    )
    parser.add_argument(
        '-s', '--sources',
        default='sources',
        help='Sources directory to search for EPUB files (default: sources/)'
    )
    
    args = parser.parse_args()
    
    if args.epub_file:
        # Convert single file
        try:
            convert_epub_to_markdown(args.epub_file, args.output)
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        # Convert all EPUBs in sources directory
        convert_all_epubs(args.sources, args.output)


if __name__ == '__main__':
    main()

