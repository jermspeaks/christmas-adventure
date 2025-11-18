#!/usr/bin/env python3
"""
Analyze section files to identify "islands" - sections that have no incoming links.
These sections are unreachable through normal gameplay and need to be either
connected to the story or terminated.
"""

import os
import yaml
from pathlib import Path
from collections import defaultdict

def parse_frontmatter(content):
    """Extract YAML frontmatter from markdown file."""
    if not content.startswith('---'):
        return None, content
    
    parts = content.split('---', 2)
    if len(parts) < 3:
        return None, content
    
    try:
        frontmatter = yaml.safe_load(parts[1])
        return frontmatter, parts[2]
    except yaml.YAMLError:
        return None, content

def find_islands(sections_dir='sections'):
    """Find all sections that have no incoming links (islands)."""
    sections_path = Path(sections_dir)
    
    # Get all section files
    section_files = sorted(sections_path.glob('section-*.md'))
    
    print(f"Analyzing {len(section_files)} section files...")
    
    # Track all sections that exist
    existing_sections = {}
    
    # Track all sections that are referenced as targets (have incoming links)
    referenced_sections = set()
    
    # First pass: collect all existing sections and their choices
    for md_file in section_files:
        try:
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            frontmatter, body = parse_frontmatter(content)
            if not frontmatter:
                continue
            
            section_id = frontmatter.get('id', '')
            title = frontmatter.get('title', 'Untitled')
            choices = frontmatter.get('choices', [])
            
            # Store section info
            existing_sections[md_file.name] = {
                'id': section_id,
                'title': title,
                'choices': choices,
                'filename': md_file.name
            }
            
            # Track all targets referenced by this section's choices
            for choice in choices:
                target = choice.get('target', '')
                if target:
                    referenced_sections.add(target)
        
        except Exception as e:
            print(f"Error processing {md_file.name}: {e}")
            continue
    
    # Find islands: sections that exist but are not referenced
    # Exclude section-1.md as it's the starting point
    islands = []
    for filename, section_info in existing_sections.items():
        if filename == 'section-1.md':
            continue  # Skip the starting section
        
        if filename not in referenced_sections:
            has_choices = len(section_info['choices']) > 0
            islands.append({
                'filename': filename,
                'id': section_info['id'],
                'title': section_info['title'],
                'has_choices': has_choices,
                'choices': section_info['choices']
            })
    
    return islands

def generate_islands_report(islands, output_file='ISLANDS.md'):
    """Generate a markdown report of island sections."""
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# Islands Analysis\n\n")
        f.write("This file documents all sections that are \"islands\" - sections that exist but have no incoming links from other sections. These sections are unreachable through normal gameplay.\n\n")
        f.write("**What this means:**\n")
        f.write("- These sections cannot be reached by following choices from other sections\n")
        f.write("- They need to either be connected to the story (by adding a choice that points to them) or terminated\n")
        f.write("- Sections with choices need partial termination (remove or modify choices)\n")
        f.write("- Sections without choices are already terminated but may need story connection\n\n")
        f.write("---\n\n")
        
        if not islands:
            f.write("**No island sections found! All sections are reachable.**\n")
            return
        
        # Separate islands by type
        islands_with_choices = [i for i in islands if i['has_choices']]
        islands_without_choices = [i for i in islands if not i['has_choices']]
        
        if islands_with_choices:
            f.write("## Islands with Choices (Need Partial Termination)\n\n")
            f.write("These sections have choices but are unreachable. They need to either:\n")
            f.write("- Have their choices removed/modified to terminate the branch, or\n")
            f.write("- Be connected to the story by adding a choice from another section that points to them\n\n")
            
            for island in sorted(islands_with_choices, key=lambda x: x['filename']):
                f.write(f"### {island['filename']} - \"{island['title']}\"\n\n")
                f.write(f"**Section ID:** `{island['id']}`\n\n")
                f.write("**Choices:**\n")
                for i, choice in enumerate(island['choices'], 1):
                    target = choice.get('target', '')
                    text = choice.get('text', '')
                    f.write(f"- Choice {i}: \"{text}\" → `{target}`\n")
                f.write("\n")
            
            f.write("---\n\n")
        
        if islands_without_choices:
            f.write("## Islands without Choices (Already Terminated)\n\n")
            f.write("These sections have no choices (already terminated) but are unreachable. They may need to be connected to the story if they contain important content.\n\n")
            
            for island in sorted(islands_without_choices, key=lambda x: x['filename']):
                f.write(f"### {island['filename']} - \"{island['title']}\"\n\n")
                f.write(f"**Section ID:** `{island['id']}`\n\n")
                f.write("*This section has no choices and is already terminated.*\n\n")
            
            f.write("---\n\n")
        
        f.write(f"## Summary\n\n")
        f.write(f"Total island sections: **{len(islands)}**\n\n")
        f.write(f"- Islands with choices (need partial termination): **{len(islands_with_choices)}**\n")
        f.write(f"- Islands without choices (already terminated): **{len(islands_without_choices)}**\n")

if __name__ == '__main__':
    import sys
    
    sections_dir = sys.argv[1] if len(sys.argv) > 1 else 'sections'
    output_file = sys.argv[2] if len(sys.argv) > 2 else 'ISLANDS.md'
    
    print("Starting islands analysis...")
    islands = find_islands(sections_dir)
    
    print(f"\nFound {len(islands)} island sections")
    
    islands_with_choices = [i for i in islands if i['has_choices']]
    islands_without_choices = [i for i in islands if not i['has_choices']]
    print(f"  - {len(islands_with_choices)} with choices (need partial termination)")
    print(f"  - {len(islands_without_choices)} without choices (already terminated)")
    
    print(f"\nGenerating report: {output_file}")
    generate_islands_report(islands, output_file)
    
    print("\nAnalysis complete!")

