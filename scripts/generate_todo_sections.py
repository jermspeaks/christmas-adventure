#!/usr/bin/env python3
"""
Generate TODO_SECTIONS.md from DECISIONS.md

This script parses DECISIONS.md to identify:
1. Incomplete terminated sections (Untitled + terminated)
2. Orphaned sections (no incoming links)
3. Missing section files (referenced but don't exist)
"""

import re
from pathlib import Path


def parse_decisions(decisions_file='DECISIONS.md', sections_dir='src/content/sections'):
    """Parse DECISIONS.md and extract section information."""
    
    # Read DECISIONS.md
    with open(decisions_file, 'r') as f:
        content = f.read()
    
    # Get all existing section files
    sections_path = Path(sections_dir)
    existing_sections = set()
    if sections_path.exists():
        for f in sections_path.glob('section-*.md'):
            existing_sections.add(f.stem)
    
    # Parse sections from DECISIONS.md
    sections = {}
    
    # Pattern to match section headers
    section_pattern = re.compile(r'^### (section-\d+\.md)$', re.MULTILINE)
    id_pattern = re.compile(r'\*\*ID:\*\* `(section-\d+)`')
    title_pattern = re.compile(r'\*\*Title:\*\* (.+)')
    # Match "Referenced by:" followed by optional whitespace/newline, then capture until next section or end
    referenced_by_pattern = re.compile(r'\*\*Referenced by:\*\*\s*\n?(.+?)(?=\n\n### |\n\n---|\Z)', re.DOTALL)
    points_to_pattern = re.compile(r'\*\*Points to:\*\*\s*\n?(.+?)(?=\n\n### |\n\n---|\Z)', re.DOTALL)
    
    # Split into incoming and outgoing sections
    incoming_section = content.find('## Incoming Links')
    outgoing_section = content.find('## Outgoing Links')
    incoming_content = content[incoming_section:outgoing_section]
    outgoing_content = content[outgoing_section:]
    
    # Parse incoming links
    for match in section_pattern.finditer(incoming_content):
        section_name = match.group(1)
        section_id = section_name.replace('.md', '')
        
        # Extract section info
        start = match.end()
        next_match = section_pattern.search(incoming_content, start)
        end = next_match.start() if next_match else len(incoming_content)
        section_text = incoming_content[start:end]
        
        id_match = id_pattern.search(section_text)
        title_match = title_pattern.search(section_text)
        ref_match = referenced_by_pattern.search(section_text)
        
        if id_match and title_match:
            sections[section_id] = {
                'id': id_match.group(1),
                'title': title_match.group(1),
                'referenced_by': ref_match.group(1) if ref_match else '',
                'points_to': '',
                'file_exists': section_id in existing_sections
            }
    
    # Parse outgoing links
    for match in section_pattern.finditer(outgoing_content):
        section_name = match.group(1)
        section_id = section_name.replace('.md', '')
        
        start = match.end()
        next_match = section_pattern.search(outgoing_content, start)
        end = next_match.start() if next_match else len(outgoing_content)
        section_text = outgoing_content[start:end]
        
        id_match = id_pattern.search(section_text)
        title_match = title_pattern.search(section_text)
        points_match = points_to_pattern.search(section_text)
        
        if id_match and title_match:
            if section_id not in sections:
                sections[section_id] = {
                    'id': id_match.group(1),
                    'title': title_match.group(1),
                    'referenced_by': '',
                    'points_to': '',
                    'file_exists': section_id in existing_sections
                }
            sections[section_id]['points_to'] = points_match.group(1) if points_match else ''
    
    return sections


def categorize_sections(sections):
    """Categorize sections into incomplete, orphaned, and missing."""
    
    incomplete_terminated = []
    orphaned = []
    missing_files = []
    
    for section_id, info in sections.items():
        # Check if file exists
        if not info['file_exists']:
            missing_files.append((section_id, info))
        
        # Check if orphaned (no incoming links)
        if 'No incoming links' in info['referenced_by']:
            orphaned.append((section_id, info))
        
        # Check if incomplete terminated (Untitled and terminated)
        if info['title'] == 'Untitled' and 'No outgoing links' in info['points_to']:
            incomplete_terminated.append((section_id, info))
    
    return incomplete_terminated, orphaned, missing_files


def extract_references(ref_text):
    """Extract reference lines from text."""
    if not ref_text or 'No incoming links' in ref_text:
        return []
    # Split by lines and filter
    ref_lines = []
    for line in ref_text.split('\n'):
        line = line.strip()
        if line and line.startswith('-') and not line.startswith('*'):
            ref_lines.append(line)
    return ref_lines


def extract_points_to(points_text):
    """Extract points-to lines from text."""
    if not points_text or 'No outgoing links' in points_text:
        return []
    point_lines = [line.strip() for line in points_text.split('\n') 
                   if line.strip() and not line.strip().startswith('*')]
    return [point for point in point_lines if point.startswith('-')]


def generate_todo_file(incomplete_terminated, orphaned, missing_files, output_file='TODO_SECTIONS.md'):
    """Generate the TODO_SECTIONS.md file."""
    
    output = []
    output.append('# TODO Sections')
    output.append('')
    output.append('This file identifies sections that need work to complete the story.')
    output.append('It is generated from DECISIONS.md to help track what needs to be written or connected.')
    output.append('')
    output.append('**Note:** This file should be regenerated after making changes to sections.')
    output.append('')
    output.append('---')
    output.append('')
    output.append('')
    output.append('## Incomplete Terminated Sections')
    output.append('')
    output.append('These sections are marked as "Untitled" and are terminated (no outgoing links).')
    output.append('They need content written to complete the story branches.')
    output.append('')
    output.append(f'**Total:** {len(incomplete_terminated)} sections')
    output.append('')
    
    for section_id, info in sorted(incomplete_terminated, key=lambda x: int(x[0].split('-')[1])):
        output.append(f'### {section_id}.md')
        output.append('')
        output.append(f'**ID:** `{info["id"]}`')
        output.append(f'**Title:** {info["title"]}')
        output.append('')
        refs = extract_references(info['referenced_by'])
        if refs:
            output.append('**Referenced by:**')
            for ref in refs:
                output.append(f'  {ref}')
            output.append('')
        output.append('**Status:** Terminated (no outgoing links)')
        output.append('**Action Needed:** Write content for this section')
        output.append('')
    
    output.append('---')
    output.append('')
    output.append('')
    output.append('## Orphaned Sections')
    output.append('')
    output.append('These sections have no incoming links, meaning they cannot be reached through normal gameplay.')
    output.append('They need connections from other sections to be accessible.')
    output.append('')
    output.append(f'**Total:** {len(orphaned)} sections')
    output.append('')
    
    for section_id, info in sorted(orphaned, key=lambda x: int(x[0].split('-')[1])):
        output.append(f'### {section_id}.md')
        output.append('')
        output.append(f'**ID:** `{info["id"]}`')
        output.append(f'**Title:** {info["title"]}')
        output.append('')
        points = extract_points_to(info['points_to'])
        if points:
            output.append('**Points to:**')
            for point in points:
                output.append(f'  {point}')
            output.append('')
        output.append('**Status:** No incoming links (orphaned)')
        output.append('**Action Needed:** Add a choice from another section that points to this section')
        output.append('')
    
    output.append('---')
    output.append('')
    output.append('')
    output.append('## Missing Section Files')
    output.append('')
    output.append('These sections are referenced in DECISIONS.md but do not exist as files yet.')
    output.append('They need to be created.')
    output.append('')
    output.append(f'**Total:** {len(missing_files)} sections')
    output.append('')
    
    for section_id, info in sorted(missing_files, key=lambda x: int(x[0].split('-')[1])):
        output.append(f'### {section_id}.md')
        output.append('')
        output.append(f'**ID:** `{info["id"]}`')
        output.append(f'**Title:** {info["title"]}')
        output.append('')
        refs = extract_references(info['referenced_by'])
        if refs:
            output.append('**Referenced by:**')
            for ref in refs:
                output.append(f'  {ref}')
            output.append('')
        points = extract_points_to(info['points_to'])
        if points:
            output.append('**Points to:**')
            for point in points:
                output.append(f'  {point}')
            output.append('')
        output.append('**Status:** File does not exist')
        output.append('**Action Needed:** Create the section file')
        output.append('')
    
    output.append('---')
    output.append('')
    output.append('')
    output.append('## Summary')
    output.append('')
    output.append(f'- Incomplete terminated sections: **{len(incomplete_terminated)}**')
    output.append(f'- Orphaned sections: **{len(orphaned)}**')
    output.append(f'- Missing section files: **{len(missing_files)}**')
    output.append(f'- **Total sections needing work: {len(incomplete_terminated) + len(orphaned) + len(missing_files)}**')
    
    # Write to file
    with open(output_file, 'w') as f:
        f.write('\n'.join(output))
    
    print(f'Created {output_file} with:')
    print(f'  - {len(incomplete_terminated)} incomplete terminated sections')
    print(f'  - {len(orphaned)} orphaned sections')
    print(f'  - {len(missing_files)} missing section files')


def main():
    """Main function."""
    import sys
    from pathlib import Path
    
    # Check if DECISIONS.md exists
    decisions_file = Path('DECISIONS.md')
    if not decisions_file.exists():
        print("Error: DECISIONS.md not found.")
        print("Please generate DECISIONS.md first by running:")
        print("  uv run python scripts/generate_decisions.py")
        print("or")
        print("  python scripts/generate_decisions.py")
        sys.exit(1)
    
    sections = parse_decisions()
    incomplete_terminated, orphaned, missing_files = categorize_sections(sections)
    generate_todo_file(incomplete_terminated, orphaned, missing_files)


if __name__ == '__main__':
    main()

