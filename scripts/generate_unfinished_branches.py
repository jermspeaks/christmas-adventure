#!/usr/bin/env python3
"""
Generate UNFINISHED_BRANCHES.md by analyzing section files.
Finds all choices that point to non-existent target files.
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

def analyze_unfinished_branches(sections_dir='sections'):
    """Analyze all section files for choices pointing to non-existent targets."""
    sections_path = Path(sections_dir)
    unfinished_branches = []
    
    # Get all existing section files
    section_files = sorted(sections_path.glob('section-*.md'))
    all_section_files = set(f.name for f in section_files)
    
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
            
            # Find choices pointing to non-existent files
            unfinished = []
            for i, choice in enumerate(choices, 1):
                target = choice.get('target', '')
                if target and target not in all_section_files:
                    unfinished.append({
                        'choice_num': i,
                        'text': choice.get('text', ''),
                        'target': target
                    })
            
            if unfinished:
                unfinished_branches.append({
                    'filename': md_file.name,
                    'id': section_id,
                    'title': title,
                    'unfinished': unfinished
                })
        
        except Exception as e:
            print(f"Error processing {md_file.name}: {e}")
            continue
    
    return unfinished_branches

def generate_unfinished_branches_report(unfinished_branches, output_file='UNFINISHED_BRANCHES.md'):
    """Generate a markdown report of unfinished branches."""
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# Unfinished Branches Analysis\n\n")
        f.write("This file documents all sections where choices lead to non-existent destination files.\n\n")
        f.write("Each section shows:\n")
        f.write("- Section filename and title\n")
        f.write("- All choices with missing destination files marked with ⚠️ **MISSING**\n\n")
        f.write("---\n\n")
        
        if not unfinished_branches:
            f.write("**No unfinished branches found! All choices point to existing sections.**\n")
            return
        
        for section in unfinished_branches:
            f.write(f"## {section['filename']} - \"{section['title']}\"\n\n")
            
            for choice in section['unfinished']:
                f.write(f"- Choice {choice['choice_num']}: \"{choice['text']}\" → `{choice['target']}` ⚠️ **MISSING**\n")
            
            f.write("\n")
            f.write("**Missing Targets:**\n")
            missing_targets = sorted(set(c['target'] for c in section['unfinished']))
            for target in missing_targets:
                f.write(f"- `{target}`\n")
            
            f.write("\n")
            f.write("---\n\n")
        
        # Summary
        total_sections = len(unfinished_branches)
        total_missing = sum(len(s['unfinished']) for s in unfinished_branches)
        unique_missing = len(set(c['target'] for s in unfinished_branches for c in s['unfinished']))
        
        f.write("\n## Summary\n\n")
        f.write(f"Total sections with unfinished branches: **{total_sections}**\n\n")
        f.write(f"Total unfinished choice targets: **{total_missing}**\n\n")
        f.write(f"Unique missing target files: **{unique_missing}**\n")

if __name__ == '__main__':
    import sys
    
    sections_dir = sys.argv[1] if len(sys.argv) > 1 else 'sections'
    output_file = sys.argv[2] if len(sys.argv) > 2 else 'UNFINISHED_BRANCHES.md'
    
    print("Starting analysis...")
    unfinished_branches = analyze_unfinished_branches(sections_dir)
    
    print(f"\nFound {len(unfinished_branches)} sections with unfinished branches")
    total_missing = sum(len(s['unfinished']) for s in unfinished_branches)
    unique_missing = len(set(c['target'] for s in unfinished_branches for c in s['unfinished']))
    print(f"Total {total_missing} choices pointing to missing files")
    print(f"{unique_missing} unique missing target files")
    
    print(f"\nGenerating report: {output_file}")
    generate_unfinished_branches_report(unfinished_branches, output_file)
    
    print("\nAnalysis complete!")

