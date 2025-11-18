#!/usr/bin/env python3
"""
Analyze section files to identify duplicate choice targets.
Finds cases where multiple choices in the same section lead to the same destination file.
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

def analyze_sections(sections_dir='sections'):
    """Analyze all section files for duplicate choice targets."""
    sections_path = Path(sections_dir)
    duplicate_sections = []
    
    # Get all section files
    section_files = sorted(sections_path.glob('section-*.md'))
    
    print(f"Analyzing {len(section_files)} section files...")
    
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
            
            if not choices:
                continue
            
            # Group choices by target file
            target_groups = defaultdict(list)
            for i, choice in enumerate(choices, 1):
                target = choice.get('target', '')
                if target:
                    target_groups[target].append({
                        'index': i,
                        'text': choice.get('text', '')
                    })
            
            # Find duplicates (targets with multiple choices)
            duplicates = {target: choices_list for target, choices_list in target_groups.items() 
                         if len(choices_list) > 1}
            
            if duplicates:
                duplicate_sections.append({
                    'filename': md_file.name,
                    'id': section_id,
                    'title': title,
                    'all_choices': choices,
                    'duplicates': duplicates
                })
        
        except Exception as e:
            print(f"Error processing {md_file.name}: {e}")
            continue
    
    return duplicate_sections

def generate_choices_report(duplicate_sections, output_file='CHOICES.md'):
    """Generate a markdown report of duplicate choice targets."""
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# Duplicate Choice Targets Analysis\n\n")
        f.write("This file documents all sections where multiple choices lead to the same destination file.\n\n")
        f.write("Each section shows:\n")
        f.write("- Section filename and title\n")
        f.write("- All choices with their destination files\n")
        f.write("- Duplicate targets marked with ⚠️ DUPLICATE\n\n")
        f.write("---\n\n")
        
        if not duplicate_sections:
            f.write("**No duplicate choice targets found!**\n")
            return
        
        for section in duplicate_sections:
            f.write(f"## {section['filename']} - \"{section['title']}\"\n\n")
            
            # Show all choices
            for i, choice in enumerate(section['all_choices'], 1):
                target = choice.get('target', '')
                text = choice.get('text', '')
                
                # Check if this target is a duplicate
                is_duplicate = target in section['duplicates'] and len(section['duplicates'][target]) > 1
                
                if is_duplicate:
                    # Find which choice index this is in the duplicates list
                    dup_info = next((c for c in section['duplicates'][target] if c['index'] == i), None)
                    if dup_info:
                        f.write(f"- Choice {i}: \"{text}\" → `{target}` ⚠️ **DUPLICATE**\n")
                    else:
                        f.write(f"- Choice {i}: \"{text}\" → `{target}`\n")
                else:
                    f.write(f"- Choice {i}: \"{text}\" → `{target}`\n")
            
            f.write("\n")
            
            # Summary of duplicates
            f.write("**Duplicate Targets:**\n")
            for target, choices_list in section['duplicates'].items():
                choice_nums = [c['index'] for c in choices_list]
                f.write(f"- `{target}` appears in choices: {', '.join(map(str, choice_nums))}\n")
            
            f.write("\n---\n\n")
        
        f.write(f"\n## Summary\n\n")
        f.write(f"Total sections with duplicate choice targets: **{len(duplicate_sections)}**\n\n")
        
        # Count total duplicates
        total_duplicates = sum(len(dups) for dups in [s['duplicates'] for s in duplicate_sections])
        f.write(f"Total duplicate target groups: **{total_duplicates}**\n")

if __name__ == '__main__':
    import sys
    
    sections_dir = sys.argv[1] if len(sys.argv) > 1 else 'sections'
    output_file = sys.argv[2] if len(sys.argv) > 2 else 'CHOICES.md'
    
    print("Starting analysis...")
    duplicate_sections = analyze_sections(sections_dir)
    
    print(f"\nFound {len(duplicate_sections)} sections with duplicate choice targets")
    
    print(f"\nGenerating report: {output_file}")
    generate_choices_report(duplicate_sections, output_file)
    
    print("\nAnalysis complete!")

