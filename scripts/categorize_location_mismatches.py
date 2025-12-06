#!/usr/bin/env python3
"""
Categorize location mismatches by storyline to identify false positives vs real issues.

Groups location mismatches into:
- Fantasy → Fantasy (same storyline, may need transitions)
- Mystery → Mystery (same storyline, may need transitions)
- Fantasy → Mystery (cross-storyline, likely intentional)
- Mystery → Fantasy (cross-storyline, likely intentional)
"""

import re
from pathlib import Path
from collections import defaultdict

# Fantasy storyline characters and locations
FANTASY_CHARS = {'Cheshire', 'Elara', 'Keepsake Keeper', 'Kvothe'}
FANTASY_LOCATIONS = {
    'Starlight Hollow', 'Frostwood Forest', 'the forest', 'the village',
    'the café', 'the cafe', 'Elara\'s Enchanted Bakery'
}

# Mystery storyline characters and locations
MYSTERY_CHARS = {'Marcus', 'Velma', 'Eleanor', 'Yuzu', 'Officer Martinez', 'Alistair'}
MYSTERY_LOCATIONS = {
    'Tombs and Trinkets', 'the bookshop', 'the shop', 'the office',
    'the storage room', 'the mystery section'
}


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
        
        # Check for locations
        fantasy_loc_count = sum(1 for loc in FANTASY_LOCATIONS if loc.lower() in body.lower())
        mystery_loc_count = sum(1 for loc in MYSTERY_LOCATIONS if loc.lower() in body.lower())
        
        # Determine storyline
        fantasy_score = fantasy_char_count + fantasy_loc_count
        mystery_score = mystery_char_count + mystery_loc_count
        
        if fantasy_score > mystery_score and fantasy_score > 0:
            return 'fantasy'
        elif mystery_score > fantasy_score and mystery_score > 0:
            return 'mystery'
        elif fantasy_score == mystery_score and fantasy_score > 0:
            return 'mixed'
        else:
            return 'unknown'
    
    except Exception as e:
        print(f"Error processing {section_file}: {e}")
        return 'unknown'


def parse_continuity_report(report_file='CONTINUITY_REPORT.md'):
    """Parse location mismatches from CONTINUITY_REPORT.md."""
    report_path = Path(report_file)
    
    if not report_path.exists():
        print(f"Error: {report_file} not found!")
        return []
    
    with open(report_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    location_mismatches = []
    
    # Find the Location Mismatches section
    if '### Location Mismatches' not in content:
        print("No Location Mismatches section found in report")
        return []
    
    # Extract the section
    start_idx = content.find('### Location Mismatches')
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
    
    # Parse each mismatch entry
    pattern = r'- `(section-\d+\.md)` → `(section-\d+\.md)`\s*\n\s*- Source location: (.+?)\s*\n\s*- Target location: (.+?)\s*\n'
    matches = re.finditer(pattern, section_content, re.MULTILINE | re.DOTALL)
    
    for match in matches:
        source_file = match.group(1)
        target_file = match.group(2)
        source_location = match.group(3).strip()
        target_location = match.group(4).strip()
        
        location_mismatches.append({
            'source': source_file,
            'target': target_file,
            'source_location': source_location,
            'target_location': target_location
        })
    
    return location_mismatches


def categorize_mismatches(location_mismatches, sections_dir='src/content/sections'):
    """Categorize location mismatches by storyline."""
    categorized = {
        'fantasy_to_fantasy': [],
        'mystery_to_mystery': [],
        'fantasy_to_mystery': [],
        'mystery_to_fantasy': [],
        'unknown': []
    }
    
    print("Identifying storylines for sections...")
    for mismatch in location_mismatches:
        source_storyline = identify_storyline(mismatch['source'], sections_dir)
        target_storyline = identify_storyline(mismatch['target'], sections_dir)
        
        mismatch['source_storyline'] = source_storyline
        mismatch['target_storyline'] = target_storyline
        
        # Categorize
        if source_storyline == 'fantasy' and target_storyline == 'fantasy':
            categorized['fantasy_to_fantasy'].append(mismatch)
        elif source_storyline == 'mystery' and target_storyline == 'mystery':
            categorized['mystery_to_mystery'].append(mismatch)
        elif source_storyline == 'fantasy' and target_storyline == 'mystery':
            categorized['fantasy_to_mystery'].append(mismatch)
        elif source_storyline == 'mystery' and target_storyline == 'fantasy':
            categorized['mystery_to_fantasy'].append(mismatch)
        else:
            categorized['unknown'].append(mismatch)
    
    return categorized


def generate_report(categorized, output_file='LOCATION_MISMATCHES_ANALYSIS.md'):
    """Generate a categorized report of location mismatches."""
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# Location Mismatches Analysis\n\n")
        f.write("This report categorizes location mismatches by storyline to help identify ")
        f.write("which transitions need fixes vs. which are intentional cross-storyline transitions.\n\n")
        f.write("**Note:** This file is automatically generated. Do not edit manually.\n\n")
        f.write("---\n\n")
        
        # Summary
        total = sum(len(v) for v in categorized.values())
        f.write("## Summary\n\n")
        f.write(f"- **Total location mismatches:** {total}\n")
        f.write(f"- **Fantasy → Fantasy:** {len(categorized['fantasy_to_fantasy'])} (same storyline, may need transitions)\n")
        f.write(f"- **Mystery → Mystery:** {len(categorized['mystery_to_mystery'])} (same storyline, may need transitions)\n")
        f.write(f"- **Fantasy → Mystery:** {len(categorized['fantasy_to_mystery'])} (cross-storyline, likely intentional)\n")
        f.write(f"- **Mystery → Fantasy:** {len(categorized['mystery_to_fantasy'])} (cross-storyline, likely intentional)\n")
        f.write(f"- **Unknown/Mixed:** {len(categorized['unknown'])} (needs manual review)\n\n")
        f.write("---\n\n")
        
        # Fantasy → Fantasy (needs review)
        if categorized['fantasy_to_fantasy']:
            f.write("## Fantasy → Fantasy (Same Storyline - Needs Review)\n\n")
            f.write("These transitions are within the fantasy storyline and may need location transition text.\n\n")
            for mismatch in sorted(categorized['fantasy_to_fantasy'], key=lambda x: (x['source'], x['target'])):
                f.write(f"- `{mismatch['source']}` → `{mismatch['target']}`\n")
                f.write(f"  - Source location: {mismatch['source_location']}\n")
                f.write(f"  - Target location: {mismatch['target_location']}\n")
                f.write(f"  - **Action:** Review transition - add explanation if needed\n\n")
            f.write("---\n\n")
        
        # Mystery → Mystery (needs review)
        if categorized['mystery_to_mystery']:
            f.write("## Mystery → Mystery (Same Storyline - Needs Review)\n\n")
            f.write("These transitions are within the mystery storyline and may need location transition text.\n\n")
            for mismatch in sorted(categorized['mystery_to_mystery'], key=lambda x: (x['source'], x['target'])):
                f.write(f"- `{mismatch['source']}` → `{mismatch['target']}`\n")
                f.write(f"  - Source location: {mismatch['source_location']}\n")
                f.write(f"  - Target location: {mismatch['target_location']}\n")
                f.write(f"  - **Action:** Review transition - add explanation if needed\n\n")
            f.write("---\n\n")
        
        # Fantasy → Mystery (likely intentional)
        if categorized['fantasy_to_mystery']:
            f.write("## Fantasy → Mystery (Cross-Storyline - Likely Intentional)\n\n")
            f.write("These transitions cross from fantasy to mystery storyline. Likely intentional (flashback, parallel narrative, etc.).\n\n")
            for mismatch in sorted(categorized['fantasy_to_mystery'], key=lambda x: (x['source'], x['target'])):
                f.write(f"- `{mismatch['source']}` → `{mismatch['target']}`\n")
                f.write(f"  - Source location: {mismatch['source_location']}\n")
                f.write(f"  - Target location: {mismatch['target_location']}\n")
                f.write(f"  - **Action:** Verify narrative flow is intentional\n\n")
            f.write("---\n\n")
        
        # Mystery → Fantasy (likely intentional)
        if categorized['mystery_to_fantasy']:
            f.write("## Mystery → Fantasy (Cross-Storyline - Likely Intentional)\n\n")
            f.write("These transitions cross from mystery to fantasy storyline. Likely intentional (flashback, parallel narrative, etc.).\n\n")
            for mismatch in sorted(categorized['mystery_to_fantasy'], key=lambda x: (x['source'], x['target'])):
                f.write(f"- `{mismatch['source']}` → `{mismatch['target']}`\n")
                f.write(f"  - Source location: {mismatch['source_location']}\n")
                f.write(f"  - Target location: {mismatch['target_location']}\n")
                f.write(f"  - **Action:** Verify narrative flow is intentional\n\n")
            f.write("---\n\n")
        
        # Unknown/Mixed (needs manual review)
        if categorized['unknown']:
            f.write("## Unknown/Mixed (Needs Manual Review)\n\n")
            f.write("These transitions couldn't be clearly categorized and need manual review.\n\n")
            for mismatch in sorted(categorized['unknown'], key=lambda x: (x['source'], x['target'])):
                f.write(f"- `{mismatch['source']}` → `{mismatch['target']}`\n")
                f.write(f"  - Source storyline: {mismatch['source_storyline']}\n")
                f.write(f"  - Target storyline: {mismatch['target_storyline']}\n")
                f.write(f"  - Source location: {mismatch['source_location']}\n")
                f.write(f"  - Target location: {mismatch['target_location']}\n")
                f.write(f"  - **Action:** Manual review required\n\n")


if __name__ == '__main__':
    import sys
    
    report_file = sys.argv[1] if len(sys.argv) > 1 else 'CONTINUITY_REPORT.md'
    sections_dir = sys.argv[2] if len(sys.argv) > 2 else 'src/content/sections'
    output_file = sys.argv[3] if len(sys.argv) > 3 else 'LOCATION_MISMATCHES_ANALYSIS.md'
    
    print("Parsing CONTINUITY_REPORT.md...")
    location_mismatches = parse_continuity_report(report_file)
    print(f"Found {len(location_mismatches)} location mismatches")
    
    print("\nCategorizing by storyline...")
    categorized = categorize_mismatches(location_mismatches, sections_dir)
    
    print(f"\nGenerating report: {output_file}")
    generate_report(categorized, output_file)
    
    print("\n" + "="*60)
    print("Categorization complete!")
    print(f"Report saved to: {output_file}")
    print("="*60)

