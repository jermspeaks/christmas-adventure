#!/usr/bin/env python3
"""
Randomizer script for Choose Your Own Adventure book.
Assigns random page numbers to each section to prevent sequential backtracking.
"""

import os
import json
import random
import yaml
from pathlib import Path

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

def scan_sections(sections_dir):
    """Scan all markdown files in sections directory."""
    sections = {}
    sections_path = Path(sections_dir)
    
    if not sections_path.exists():
        print(f"Error: {sections_dir} directory not found!")
        return sections
    
    for md_file in sections_path.glob('*.md'):
        with open(md_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        frontmatter, body = parse_frontmatter(content)
        if frontmatter and 'id' in frontmatter:
            sections[frontmatter['id']] = {
                'filename': md_file.name,
                'frontmatter': frontmatter,
                'targets': []
            }
            
            # Extract all targets from choices
            if 'choices' in frontmatter:
                for choice in frontmatter['choices']:
                    if 'target' in choice:
                        target_file = choice['target']
                        # Extract section ID from target filename
                        target_id = target_file.replace('.md', '')
                        sections[frontmatter['id']]['targets'].append(target_id)
    
    return sections

def assign_random_pages(sections, start_page=1):
    """Assign random page numbers to sections.
    Always assigns section-1 to page 1, then randomly shuffles the rest."""
    section_ids = list(sections.keys())
    
    # Always keep section-1 as the first page
    starting_section = 'section-1'
    other_sections = [sid for sid in section_ids if sid != starting_section]
    random.shuffle(other_sections)
    
    # Build ordered list: section-1 first (if it exists), then shuffled rest
    if starting_section in sections:
        ordered_sections = [starting_section] + other_sections
    else:
        ordered_sections = other_sections
    
    page_mapping = {}
    for idx, section_id in enumerate(ordered_sections, start=start_page):
        page_mapping[section_id] = {
            'page': idx,
            'filename': sections[section_id]['filename'],
            'title': sections[section_id]['frontmatter'].get('title', 'Untitled'),
            'targets': sections[section_id]['targets']
        }
    
    return page_mapping

def create_page_mapping(sections_dir='sections', output_file='page-mapping.json', start_page=1):
    """Main function to create page mapping."""
    print("Scanning sections...")
    sections = scan_sections(sections_dir)
    
    if not sections:
        print("No sections found!")
        return
    
    print(f"Found {len(sections)} sections")
    
    print("Assigning random page numbers...")
    page_mapping = assign_random_pages(sections, start_page)
    
    # Add reverse mapping (page number -> section ID) for easier lookup
    reverse_mapping = {info['page']: section_id for section_id, info in page_mapping.items()}
    
    output_data = {
        'sections': page_mapping,
        'page_to_section': reverse_mapping,
        'total_pages': len(page_mapping)
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f"Page mapping created: {output_file}")
    print(f"Total pages: {len(page_mapping)}")
    print("\nPage assignments:")
    for section_id, info in sorted(page_mapping.items(), key=lambda x: x[1]['page']):
        print(f"  Page {info['page']:3d}: {section_id} - {info['title']}")

if __name__ == '__main__':
    import sys
    
    sections_dir = sys.argv[1] if len(sys.argv) > 1 else 'sections'
    output_file = sys.argv[2] if len(sys.argv) > 2 else 'page-mapping.json'
    start_page = int(sys.argv[3]) if len(sys.argv) > 3 else 1
    
    create_page_mapping(sections_dir, output_file, start_page)

