#!/usr/bin/env python3
"""
Compilation script for Choose Your Own Adventure book.
Generates HTML, PDF, and EPUB outputs with page numbers and choice references.
"""

import os
import json
import yaml
import markdown
from pathlib import Path
from datetime import datetime

def parse_frontmatter(content):
    """Extract YAML frontmatter from markdown file."""
    if not content.startswith('---'):
        return None, content
    
    parts = content.split('---', 2)
    if len(parts) < 3:
        return None, content
    
    try:
        frontmatter = yaml.safe_load(parts[1])
        body = parts[2].strip()
        return frontmatter, body
    except yaml.YAMLError:
        return None, content

def load_page_mapping(mapping_file='page-mapping.json'):
    """Load the page mapping from JSON file."""
    if not os.path.exists(mapping_file):
        raise FileNotFoundError(f"Page mapping file not found: {mapping_file}. Run randomize.py first!")
    
    with open(mapping_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def resolve_choice_target(target_file, page_mapping):
    """Resolve a target filename to a page number."""
    target_id = target_file.replace('.md', '')
    if target_id in page_mapping['sections']:
        return page_mapping['sections'][target_id]['page']
    return None

def process_section(md_file, page_mapping):
    """Process a single section file and return formatted content."""
    with open(md_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    frontmatter, body = parse_frontmatter(content)
    if not frontmatter or 'id' not in frontmatter:
        return None
    
    section_id = frontmatter['id']
    page_info = page_mapping['sections'].get(section_id)
    
    if not page_info:
        return None
    
    page_num = page_info['page']
    title = frontmatter.get('title', 'Untitled')
    
    # Process choices and replace targets with page numbers
    choices_html = ""
    if 'choices' in frontmatter and frontmatter['choices']:
        choices_html = "\n\n## Your Choices:\n\n"
        for choice in frontmatter['choices']:
            choice_text = choice.get('text', '')
            target_file = choice.get('target', '')
            target_page = resolve_choice_target(target_file, page_mapping)
            
            if target_page:
                choices_html += f"- **{choice_text}** → Turn to page {target_page}\n"
            else:
                choices_html += f"- **{choice_text}** → (Invalid target: {target_file})\n"
    
    # Combine title, page number, body, and choices
    full_content = f"# {title}\n\n**Page {page_num}**\n\n{body}{choices_html}"
    
    return {
        'id': section_id,
        'page': page_num,
        'title': title,
        'content': full_content,
        'html': markdown.markdown(full_content, extensions=['extra', 'codehilite'])
    }

def generate_html(sections_data, output_file='output/adventure.html'):
    """Generate HTML output."""
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # Sort sections by page number
    sorted_sections = sorted(sections_data, key=lambda x: x['page'])
    
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Choose Your Own Christmas Adventure</title>
    <style>
        body {
            font-family: Georgia, serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            line-height: 1.6;
            background-color: #fafafa;
        }
        .section {
            page-break-after: always;
            background: white;
            padding: 40px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        h1 {
            color: #c41e3a;
            border-bottom: 3px solid #c41e3a;
            padding-bottom: 10px;
        }
        h2 {
            color: #2d5016;
            margin-top: 30px;
        }
        ul {
            list-style-type: none;
            padding-left: 0;
        }
        li {
            margin: 10px 0;
            padding: 10px;
            background-color: #f0f0f0;
            border-left: 4px solid #c41e3a;
        }
        @media print {
            .section {
                page-break-after: always;
                box-shadow: none;
                margin: 0;
            }
        }
    </style>
</head>
<body>
"""
    
    for section in sorted_sections:
        html_content += f'<div class="section">\n{section["html"]}\n</div>\n\n'
    
    html_content += """</body>
</html>"""
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"HTML generated: {output_file}")

def generate_pdf_via_pandoc(html_file='output/adventure.html', output_file='output/adventure.pdf'):
    """Generate PDF using pandoc."""
    import subprocess
    
    # First, convert HTML to markdown for pandoc, or use pandoc directly on HTML
    cmd = [
        'pandoc',
        html_file,
        '-o', output_file,
        '--pdf-engine=pdflatex',
        '-V', 'geometry:margin=1in',
        '-V', 'fontsize=11pt',
        '--toc'
    ]
    
    try:
        subprocess.run(cmd, check=True, capture_output=True)
        print(f"PDF generated: {output_file}")
    except subprocess.CalledProcessError as e:
        print(f"Error generating PDF: {e}")
        print("Make sure pandoc and pdflatex are installed")
    except FileNotFoundError:
        print("pandoc not found. Install it with: brew install pandoc")

def generate_epub(sections_data, output_file='output/adventure.epub'):
    """Generate EPUB using pandoc."""
    import subprocess
    import tempfile
    
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # Create a temporary markdown file with all sections
    sorted_sections = sorted(sections_data, key=lambda x: x['page'])
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
        temp_md = f.name
        f.write("# Choose Your Own Christmas Adventure\n\n")
        f.write(f"*Generated on {datetime.now().strftime('%Y-%m-%d')}*\n\n")
        
        for section in sorted_sections:
            f.write(f"\n\n---\n\n")
            f.write(section['content'])
            f.write("\n\n")
    
    cmd = [
        'pandoc',
        temp_md,
        '-o', output_file,
        '--epub-cover-image=cover.jpg' if os.path.exists('cover.jpg') else '',
        '--toc',
        '--epub-metadata=metadata.xml' if os.path.exists('metadata.xml') else ''
    ]
    cmd = [c for c in cmd if c]  # Remove empty strings
    
    try:
        subprocess.run(cmd, check=True, capture_output=True)
        print(f"EPUB generated: {output_file}")
        os.unlink(temp_md)
    except subprocess.CalledProcessError as e:
        print(f"Error generating EPUB: {e}")
        print("Make sure pandoc is installed")
    except FileNotFoundError:
        print("pandoc not found. Install it with: brew install pandoc")

def compile_book(sections_dir='sections', mapping_file='page-mapping.json', 
                 output_dir='output'):
    """Main compilation function."""
    print("Loading page mapping...")
    page_mapping = load_page_mapping(mapping_file)
    
    print("Processing sections...")
    sections_path = Path(sections_dir)
    sections_data = []
    
    for md_file in sections_path.glob('*.md'):
        section_data = process_section(md_file, page_mapping)
        if section_data:
            sections_data.append(section_data)
            print(f"  Processed: {section_data['id']} (Page {section_data['page']})")
    
    if not sections_data:
        print("No sections found to compile!")
        return
    
    print(f"\nCompiling {len(sections_data)} sections...")
    
    # Generate HTML
    html_file = os.path.join(output_dir, 'adventure.html')
    generate_html(sections_data, html_file)
    
    # Generate PDF
    pdf_file = os.path.join(output_dir, 'adventure.pdf')
    generate_pdf_via_pandoc(html_file, pdf_file)
    
    # Generate EPUB
    epub_file = os.path.join(output_dir, 'adventure.epub')
    generate_epub(sections_data, epub_file)
    
    print("\nCompilation complete!")

if __name__ == '__main__':
    import sys
    
    sections_dir = sys.argv[1] if len(sys.argv) > 1 else 'sections'
    mapping_file = sys.argv[2] if len(sys.argv) > 2 else 'page-mapping.json'
    output_dir = sys.argv[3] if len(sys.argv) > 3 else 'output'
    
    compile_book(sections_dir, mapping_file, output_dir)

