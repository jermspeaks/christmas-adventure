#!/usr/bin/env python3
"""
Filter missing character warnings by storyline to identify false positives.

Characters belong to specific storylines:
- Fantasy: Cheshire, Elara, Keepsake Keeper, Kvothe
- Mystery: Marcus, Velma, Eleanor, Yuzu, Officer Martinez, Alistair

Warnings where source and target are different storylines are likely false positives.
Warnings where source and target are same storyline need review.
"""

import re
from pathlib import Path
from collections import defaultdict

# Fantasy storyline characters
FANTASY_CHARS = {'Cheshire', 'Elara', 'Keepsake Keeper', 'Kvothe'}

# Mystery storyline characters
MYSTERY_CHARS = {'Marcus', 'Velma', 'Eleanor', 'Yuzu', 'Officer Martinez', 'Alistair', 'Alistair Finch'}

# Character to storyline mapping
CHAR_STORYLINE = {}
for char in FANTASY_CHARS:
    CHAR_STORYLINE[char] = 'fantasy'
for char in MYSTERY_CHARS:
    CHAR_STORYLINE[char] = 'mystery'


def identify_storyline(section_file, sections_dir='src/content/sections'):
    """Identify which storyline a section belongs to based on characters and locations."""
    section_path = Path(sections_dir) / section_file
    
    if not section_path.exists():
        return 'unknown'
    
    try:
        with open(section_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract body (skip frontmatter)
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                body = parts[2]
            else:
                body = content
        else:
            body = content
        
        # Check for characters
        fantasy_char_count = sum(1 for char in FANTASY_CHARS if char in body)
        mystery_char_count = sum(1 for char in MYSTERY_CHARS if char in body)
        
        # Determine storyline
        if fantasy_char_count > mystery_char_count and fantasy_char_count > 0:
            return 'fantasy'
        elif mystery_char_count > fantasy_char_count and mystery_char_count > 0:
            return 'mystery'
        elif fantasy_char_count == mystery_char_count and (fantasy_char_count > 0 or mystery_char_count > 0):
            return 'mixed'
        else:
            return 'unknown'
    
    except Exception as e:
        print(f"Error processing {section_file}: {e}")
        return 'unknown'


def parse_continuity_report(report_file='CONTINUITY_REPORT.md'):
    """Parse missing character warnings from CONTINUITY_REPORT.md."""
    report_path = Path(report_file)
    
    if not report_path.exists():
        print(f"Error: {report_file} not found!")
        return []
    
    with open(report_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    missing_char_warnings = []
    
    # Find the Missing Characters section
    if '### Missing Characters' not in content:
        print("No Missing Characters section found in report")
        return []
    
    # Extract the section
    start_idx = content.find('### Missing Characters')
    if start_idx == -1:
        return []
    
    # Find the end of this section (next ## or ---)
    end_markers = ['\n## ', '\n---\n\n---']
    end_idx = len(content)
    for marker in end_markers:
        marker_idx = content.find(marker, start_idx + 1)
        if marker_idx != -1 and marker_idx < end_idx:
            end_idx = marker_idx
    
    section_content = content[start_idx:end_idx]
    
    # Parse each warning entry
    # Pattern: - `section-X.md` → `section-Y.md`\n  - Character: Name\n
    pattern = r'- `(section-\d+\.md)` → `(section-\d+\.md)`\s*\n\s*- Character: (.+?)\s*\n'
    matches = re.finditer(pattern, section_content, re.MULTILINE)
    
    for match in matches:
        source_file = match.group(1)
        target_file = match.group(2)
        character = match.group(3).strip()
        
        missing_char_warnings.append({
            'source': source_file,
            'target': target_file,
            'character': character
        })
    
    return missing_char_warnings


def categorize_warnings(missing_char_warnings, sections_dir='src/content/sections'):
    """Categorize missing character warnings by storyline."""
    needs_review = []
    false_positives = []
    
    print("Identifying storylines for sections...")
    for warning in missing_char_warnings:
        source_storyline = identify_storyline(warning['source'], sections_dir)
        target_storyline = identify_storyline(warning['target'], sections_dir)
        character_storyline = CHAR_STORYLINE.get(warning['character'], 'unknown')
        
        warning['source_storyline'] = source_storyline
        warning['target_storyline'] = target_storyline
        warning['character_storyline'] = character_storyline
        
        # Determine if it's a false positive
        # If source and target are different storylines, it's likely a false positive
        # (characters don't cross storylines)
        if source_storyline != target_storyline and source_storyline != 'unknown' and target_storyline != 'unknown':
            false_positives.append(warning)
        # If character's storyline doesn't match target storyline, it's likely a false positive
        elif character_storyline != 'unknown' and character_storyline != target_storyline:
            false_positives.append(warning)
        # Otherwise, needs review (same storyline, character should probably be present)
        else:
            needs_review.append(warning)
    
    return needs_review, false_positives


def generate_report(needs_review, false_positives, output_file='CHARACTER_WARNINGS_ANALYSIS.md'):
    """Generate a filtered report of missing character warnings."""
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# Missing Character Warnings Analysis\n\n")
        f.write("This report filters missing character warnings by storyline to identify ")
        f.write("false positives (cross-storyline transitions) vs. warnings that need review.\n\n")
        f.write("**Note:** This file is automatically generated. Do not edit manually.\n\n")
        f.write("---\n\n")
        
        # Summary
        total = len(needs_review) + len(false_positives)
        f.write("## Summary\n\n")
        f.write(f"- **Total missing character warnings:** {total}\n")
        f.write(f"- **Needs Review (same storyline):** {len(needs_review)}\n")
        f.write(f"- **False Positives (cross-storyline):** {len(false_positives)}\n\n")
        f.write("---\n\n")
        
        # Needs Review
        if needs_review:
            f.write("## Needs Review (Same Storyline)\n\n")
            f.write("These warnings are within the same storyline. Character should probably be present.\n")
            f.write("Review each to determine if character absence needs explanation or if character should be added.\n\n")
            
            # Group by character
            by_character = defaultdict(list)
            for warning in needs_review:
                by_character[warning['character']].append(warning)
            
            for character in sorted(by_character.keys()):
                warnings = sorted(by_character[character], key=lambda x: (x['source'], x['target']))
                f.write(f"### {character}\n\n")
                for warning in warnings:
                    f.write(f"- `{warning['source']}` → `{warning['target']}`\n")
                    f.write(f"  - Source storyline: {warning['source_storyline']}\n")
                    f.write(f"  - Target storyline: {warning['target_storyline']}\n")
                    f.write(f"  - **Action:** Review - explain character's absence if needed or add character mention\n\n")
            f.write("---\n\n")
        
        # False Positives
        if false_positives:
            f.write("## False Positives (Cross-Storyline)\n\n")
            f.write("These warnings are likely false positives because the transition crosses storylines.\n")
            f.write("Characters belong to specific storylines and don't cross between them.\n\n")
            
            # Group by character
            by_character = defaultdict(list)
            for warning in false_positives:
                by_character[warning['character']].append(warning)
            
            for character in sorted(by_character.keys()):
                warnings = sorted(by_character[character], key=lambda x: (x['source'], x['target']))
                f.write(f"### {character}\n\n")
                f.write(f"Character storyline: {CHAR_STORYLINE.get(character, 'unknown')}\n\n")
                for warning in warnings:
                    f.write(f"- `{warning['source']}` → `{warning['target']}`\n")
                    f.write(f"  - Source storyline: {warning['source_storyline']}\n")
                    f.write(f"  - Target storyline: {warning['target_storyline']}\n")
                    f.write(f"  - **Status:** False positive (cross-storyline transition)\n\n")
            f.write("---\n\n")


if __name__ == '__main__':
    import sys
    
    report_file = sys.argv[1] if len(sys.argv) > 1 else 'CONTINUITY_REPORT.md'
    sections_dir = sys.argv[2] if len(sys.argv) > 2 else 'src/content/sections'
    output_file = sys.argv[3] if len(sys.argv) > 3 else 'CHARACTER_WARNINGS_ANALYSIS.md'
    
    print("Parsing CONTINUITY_REPORT.md...")
    missing_char_warnings = parse_continuity_report(report_file)
    print(f"Found {len(missing_char_warnings)} missing character warnings")
    
    print("\nCategorizing by storyline...")
    needs_review, false_positives = categorize_warnings(missing_char_warnings, sections_dir)
    
    print(f"\nNeeds review: {len(needs_review)}")
    print(f"False positives: {len(false_positives)}")
    
    print(f"\nGenerating report: {output_file}")
    generate_report(needs_review, false_positives, output_file)
    
    print("\n" + "="*60)
    print("Filtering complete!")
    print(f"Report saved to: {output_file}")
    print("="*60)

