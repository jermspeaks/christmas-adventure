#!/usr/bin/env python3
"""
Generate a filtered continuity report that excludes likely false positives.

Filters out:
- Location mismatches where the "location" is actually a character name or date fragment
- Character warnings where characters are in different storylines
- Character warnings where the character is deceased
- Location mismatches that are actually same location (parsing errors)
"""

import re
import yaml
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Set, Tuple, Optional

# Known character names (to filter false positive locations)
KNOWN_CHARACTERS = {
    'Cheshire', 'Elara', 'Marcus', 'Velma', 'Eleanor', 'Alistair',
    'Kvothe', 'Yuzu', 'Officer Martinez', 'Alistair Finch'
}

# Known locations
KNOWN_LOCATIONS = {
    'Starlight Hollow', 'Frostwood Forest', 'Tombs and Trinkets',
    'the shop', 'the forest', 'the village', 'the café', 'the cafe',
    'the bookshop', 'the office', 'the storage room', 'the mystery section'
}

# Month names (to filter false positive locations)
MONTHS = {
    'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December'
}

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

def read_section_content(section_file: str, sections_dir='src/content/sections') -> Optional[str]:
    """Read the body content of a section file."""
    sections_path = Path(sections_dir)
    file_path = sections_path / section_file
    
    if not file_path.exists():
        return None
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        _, body = parse_frontmatter(content)
        return body
    except Exception:
        return None

def is_false_positive_location(location: str) -> bool:
    """Check if a location is likely a false positive."""
    location = location.strip()
    
    # Check if it's a character name
    if location in KNOWN_CHARACTERS:
        return True
    
    # Check if it's a month name
    if location in MONTHS:
        return True
    
    # Check if it's a sentence fragment (contains lowercase words that suggest it's not a location)
    words = location.split()
    if len(words) > 1:
        # If it starts with lowercase or contains common words, it's likely a fragment
        if words[0][0].islower() or any(w.lower() in ['the', 'a', 'an', 'was', 'were', 'going', 'to', 'leave', 'me'] for w in words):
            return True
    
    # Check if it's too short or looks like a sentence fragment
    if len(location) < 5:
        return True
    
    # Check for patterns like "She was going to leave me the"
    if re.search(r'\b(was|were|going|to|leave|me|the|a|an)\b', location, re.IGNORECASE):
        if not any(loc in location for loc in KNOWN_LOCATIONS):
            return True
    
    return False

def is_same_storyline(source_file: str, target_file: str, sections_dir='src/content/sections') -> bool:
    """Check if two sections are in the same storyline."""
    # Fantasy storyline characters
    fantasy_chars = {'Cheshire', 'Elara', 'Keepsake Keeper', 'Kvothe'}
    # Mystery storyline characters
    mystery_chars = {'Marcus', 'Velma', 'Eleanor', 'Yuzu', 'Officer Martinez', 'Alistair'}
    
    source_content = read_section_content(source_file, sections_dir)
    target_content = read_section_content(target_file, sections_dir)
    
    if not source_content or not target_content:
        return True  # Assume same if we can't check
    
    source_has_fantasy = any(char in source_content for char in fantasy_chars)
    source_has_mystery = any(char in source_content for char in mystery_chars)
    target_has_fantasy = any(char in target_content for char in fantasy_chars)
    target_has_mystery = any(char in target_content for char in mystery_chars)
    
    # If both have fantasy or both have mystery, they're in the same storyline
    if (source_has_fantasy and target_has_fantasy) or (source_has_mystery and target_has_mystery):
        return True
    
    # If one has fantasy and other has mystery, they're different storylines
    if (source_has_fantasy and target_has_mystery) or (source_has_mystery and target_has_fantasy):
        return False
    
    return True  # Default to same if unclear

def is_character_mentioned_indirectly(character: str, target_content: str) -> bool:
    """Check if a character is mentioned indirectly (pronouns, context, etc.)."""
    if not target_content:
        return False
    
    content_lower = target_content.lower()
    
    # For Cheshire (reindeer), check for reindeer references
    if character == 'Cheshire':
        if 'reindeer' in content_lower or 'talking' in content_lower:
            return True
    
    # For Elara, check for bakery references if she's the baker
    if character == 'Elara':
        if 'bakery' in content_lower or 'baker' in content_lower:
            return True
    
    # Check for "we" or "together" which might include the character
    if 'we' in content_lower or 'together' in content_lower or 'us' in content_lower:
        # If the scene is clearly a continuation with multiple people, character might be included
        if any(word in content_lower for word in ['continued', 'still', 'remained', 'stayed']):
            return True
    
    return False

def is_scene_continuation(source_file: str, target_file: str, sections_dir='src/content/sections') -> bool:
    """Check if target section is a direct continuation of source (same scene)."""
    source_content = read_section_content(source_file, sections_dir)
    target_content = read_section_content(target_file, sections_dir)
    
    if not source_content or not target_content:
        return False
    
    # Check for continuation indicators
    continuation_indicators = [
        'continued', 'still', 'remained', 'as you', 'you looked', 'you saw',
        'you heard', 'you felt', 'you realized', 'you thought', 'you said',
        'you asked', 'you decided', 'you focused', 'you turned', 'you stepped'
    ]
    
    # If target starts with continuation language, it's likely the same scene
    target_start = target_content[:200].lower()
    if any(indicator in target_start for indicator in continuation_indicators):
        return True
    
    return False

def is_character_deceased(character: str, target_file: str, sections_dir='src/content/sections') -> bool:
    """Check if a character is deceased in the target section."""
    if character != 'Eleanor':
        return False
    
    target_content = read_section_content(target_file, sections_dir)
    if not target_content:
        return False
    
    # Check for indicators that Eleanor is dead
    death_indicators = [
        'eleanor.*dead', 'eleanor.*killed', 'eleanor.*murdered',
        'eleanor.*death', 'eleanor.*died', 'found eleanor',
        'eleanor shellstrop.*killed', 'eleanor shellstrop.*murdered'
    ]
    
    content_lower = target_content.lower()
    return any(re.search(pattern, content_lower) for pattern in death_indicators)

def parse_continuity_report(report_file='CONTINUITY_REPORT.md'):
    """Parse the continuity report and extract issues."""
    report_path = Path(report_file)
    
    if not report_path.exists():
        print(f"Error: {report_file} not found!")
        return {}, {}
    
    with open(report_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    location_mismatches = []
    missing_characters = []
    
    # Parse location mismatches
    if '### Location Mismatches' in content:
        start_idx = content.find('### Location Mismatches')
        end_markers = ['\n## ', '\n---\n\n---']
        end_idx = len(content)
        for marker in end_markers:
            marker_idx = content.find(marker, start_idx + 1)
            if marker_idx != -1 and marker_idx < end_idx:
                end_idx = marker_idx
        
        section_content = content[start_idx:end_idx]
        
        pattern = r'- `(section-\d+\.md)` → `(section-\d+\.md)`\s*\n\s*- Source location: (.+?)\s*\n\s*- Target location: (.+?)\s*\n'
        matches = re.finditer(pattern, section_content, re.MULTILINE | re.DOTALL)
        
        for match in matches:
            location_mismatches.append({
                'source': match.group(1),
                'target': match.group(2),
                'source_location': match.group(3).strip(),
                'target_location': match.group(4).strip()
            })
    
    # Parse missing characters
    if '### Missing Characters' in content:
        start_idx = content.find('### Missing Characters')
        end_markers = ['\n## ', '\n---\n\n---']
        end_idx = len(content)
        for marker in end_markers:
            marker_idx = content.find(marker, start_idx + 1)
            if marker_idx != -1 and marker_idx < end_idx:
                end_idx = marker_idx
        
        section_content = content[start_idx:end_idx]
        
        pattern = r'- `(section-\d+\.md)` → `(section-\d+\.md)`\s*\n\s*- Character: (.+?)\s*\n'
        matches = re.finditer(pattern, section_content, re.MULTILINE | re.DOTALL)
        
        for match in matches:
            missing_characters.append({
                'source': match.group(1),
                'target': match.group(2),
                'character': match.group(3).strip()
            })
    
    return location_mismatches, missing_characters

def filter_issues(location_mismatches, missing_characters, sections_dir='src/content/sections'):
    """Filter out false positives from the issues."""
    filtered_locations = []
    filtered_characters = []
    
    # Filter location mismatches
    for issue in location_mismatches:
        source_loc = issue['source_location']
        target_loc = issue['target_location']
        
        # Skip if either location is a false positive
        if is_false_positive_location(source_loc) or is_false_positive_location(target_loc):
            continue
        
        # Check if they're actually the same location (parsing error)
        if source_loc.lower() == target_loc.lower():
            continue
        
        # Check if there's a clear transition in the target section
        target_content = read_section_content(issue['target'], sections_dir)
        if target_content:
            transition_words = ['moved', 'went', 'traveled', 'walked', 'headed', 'arrived', 'reached', 'returned', 'back at', 'found yourself']
            has_transition = any(word in target_content.lower() for word in transition_words)
            if has_transition:
                continue  # Has transition, not a real issue
        
        filtered_locations.append(issue)
    
    # Filter missing characters
    for issue in missing_characters:
        character = issue['character']
        
        # Skip if character is deceased
        if is_character_deceased(character, issue['target'], sections_dir):
            continue
        
        # Skip if sections are in different storylines (cross-storyline transitions are intentional)
        if not is_same_storyline(issue['source'], issue['target'], sections_dir):
            continue
        
        target_content = read_section_content(issue['target'], sections_dir)
        
        # Check if character absence is explained
        if target_content:
            absence_words = ['left', 'gone', 'departed', 'stayed behind', 'remained', 'stayed', 'waited']
            has_explanation = any(word in target_content.lower() for word in absence_words)
            if has_explanation:
                continue  # Absence is explained
            
            # Check if character is mentioned indirectly
            if is_character_mentioned_indirectly(character, target_content):
                continue  # Character is present but not directly named
        
        # Check if this is a scene continuation (character might be present but not mentioned)
        if is_scene_continuation(issue['source'], issue['target'], sections_dir):
            # In scene continuations, characters don't need to be mentioned in every section
            # Only flag if the character was central to the previous scene
            source_content = read_section_content(issue['source'], sections_dir)
            if source_content:
                # If character was mentioned multiple times or in a key role, they should be mentioned
                char_mentions = source_content.lower().count(character.lower())
                if char_mentions < 2:  # Only mentioned once or twice, not central
                    continue  # Character wasn't central, absence is fine
        
        filtered_characters.append(issue)
    
    return filtered_locations, filtered_characters

def generate_filtered_report(filtered_locations, filtered_characters, output_file='CONTINUITY_REPORT_FILTERED.md'):
    """Generate a filtered continuity report."""
    
    total_issues = len(filtered_locations) + len(filtered_characters)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# Filtered Continuity Report\n\n")
        f.write("This report shows only **likely real issues** after filtering out false positives.\n\n")
        f.write("**Note:** This file is automatically generated. Do not edit manually.\n\n")
        f.write("---\n\n")
        
        # Summary
        f.write("## Summary\n\n")
        f.write(f"- **Location mismatches (filtered):** {len(filtered_locations)}\n")
        f.write(f"- **Missing characters (filtered):** {len(filtered_characters)}\n")
        f.write(f"- **Total issues requiring review:** {total_issues}\n\n")
        
        if total_issues == 0:
            f.write("✅ **No real issues found!** All warnings were false positives.\n\n")
            f.write("---\n\n")
            return
        
        # Location Mismatches
        if filtered_locations:
            f.write("## Location Mismatches (Requiring Review)\n\n")
            f.write("These location transitions may need better explanations:\n\n")
            
            for issue in sorted(filtered_locations, key=lambda x: (x['source'], x['target'])):
                f.write(f"- `{issue['source']}` → `{issue['target']}`\n")
                f.write(f"  - Source location: {issue['source_location']}\n")
                f.write(f"  - Target location: {issue['target_location']}\n")
                f.write(f"  - **Action:** Review transition - add explanation if needed\n\n")
        
        # Missing Characters
        if filtered_characters:
            f.write("## Missing Characters (Requiring Review)\n\n")
            f.write("These character absences may need explanation:\n\n")
            
            for issue in sorted(filtered_characters, key=lambda x: (x['source'], x['target'], x['character'])):
                f.write(f"- `{issue['source']}` → `{issue['target']}`\n")
                f.write(f"  - Character: {issue['character']}\n")
                f.write(f"  - **Action:** Review - explain character's absence if needed\n\n")
        
        f.write("---\n\n")
        f.write("## Filtering Criteria\n\n")
        f.write("This report excludes:\n")
        f.write("- Location mismatches where locations are character names or date fragments\n")
        f.write("- Character warnings where characters are in different storylines\n")
        f.write("- Character warnings where the character is deceased\n")
        f.write("- Location mismatches that have clear transition words\n")
        f.write("- Character warnings where absence is explained\n\n")

if __name__ == '__main__':
    import sys
    
    sections_dir = sys.argv[1] if len(sys.argv) > 1 else 'src/content/sections'
    report_file = sys.argv[2] if len(sys.argv) > 2 else 'CONTINUITY_REPORT.md'
    output_file = sys.argv[3] if len(sys.argv) > 3 else 'CONTINUITY_REPORT_FILTERED.md'
    
    print("Parsing continuity report...")
    location_mismatches, missing_characters = parse_continuity_report(report_file)
    print(f"Found {len(location_mismatches)} location mismatches, {len(missing_characters)} missing character warnings")
    
    print("Filtering false positives...")
    filtered_locations, filtered_characters = filter_issues(location_mismatches, missing_characters, sections_dir)
    print(f"After filtering: {len(filtered_locations)} location mismatches, {len(filtered_characters)} missing character warnings")
    
    print(f"Generating filtered report: {output_file}")
    generate_filtered_report(filtered_locations, filtered_characters, output_file)
    
    print(f"\n✅ Filtered report generated: {output_file}")

