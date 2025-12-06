#!/usr/bin/env python3
"""
Check story continuity across all sections.
Validates structural integrity (links, choice text) and basic narrative continuity.
"""

import yaml
import re
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Set, Tuple, Optional

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

def extract_locations(text: str) -> Set[str]:
    """Extract location references from text."""
    locations = set()
    
    # Common location patterns
    location_patterns = [
        r'\b(?:in|at|to|from|toward|towards)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
        r'\bthe\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:forest|village|shop|store|café|cafe|hollow|hollows)',
        r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:Forest|Village|Shop|Store|Café|Cafe|Hollow)',
    ]
    
    for pattern in location_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            if isinstance(match, tuple):
                match = match[0] if match else ''
            if match and len(match) > 2:
                locations.add(match.strip())
    
    # Specific known locations
    known_locations = [
        'Starlight Hollow', 'Frostwood Forest', 'Tombs and Trinkets',
        'the shop', 'the forest', 'the village', 'the café', 'the cafe',
        'the bookshop', 'the office', 'the storage room'
    ]
    
    for loc in known_locations:
        if loc.lower() in text.lower():
            locations.add(loc)
    
    return locations

def extract_characters(text: str) -> Set[str]:
    """Extract character names from text."""
    characters = set()
    
    # Known character names (from the story)
    known_characters = [
        'Cheshire', 'Elara', 'Marcus', 'Velma', 'Eleanor', 'Alistair',
        'Kvothe', 'Yuzu', 'Officer Martinez', 'Alistair Finch'
    ]
    
    for char in known_characters:
        # Look for character name with context (is, was, said, etc.)
        pattern = rf'\b{re.escape(char)}\b'
        if re.search(pattern, text, re.IGNORECASE):
            characters.add(char)
    
    # Look for pronoun patterns that might indicate characters
    pronoun_patterns = [
        r'\b(?:he|she|they|him|her|them)\s+(?:is|was|said|told|asked|looked|walked)',
    ]
    
    # Also look for "with [name]" patterns
    with_pattern = r'\bwith\s+([A-Z][a-z]+)'
    matches = re.findall(with_pattern, text)
    for match in matches:
        if match not in ['You', 'The', 'This', 'That']:
            characters.add(match)
    
    return characters

def extract_objects(text: str) -> Set[str]:
    """Extract important objects/items from text."""
    objects = set()
    
    # Known important objects
    known_objects = [
        'Keepsake Keeper', 'silver button', 'the book', 'the ornament',
        'the cocoa', 'the letter opener', 'the torn note', 'the button',
        'Memory Vault', 'the vault'
    ]
    
    for obj in known_objects:
        if obj.lower() in text.lower():
            objects.add(obj)
    
    # Look for "you have" or "you're holding" patterns
    possession_patterns = [
        r'\b(?:you|you\'re)\s+(?:have|had|holding|holding|carrying|holding)\s+(?:a|an|the)?\s*([a-z]+(?:\s+[a-z]+)*)',
        r'\b(?:in|with)\s+(?:your|the)\s+([a-z]+(?:\s+[a-z]+)*)',
    ]
    
    for pattern in possession_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            if len(match) > 2 and match not in ['the', 'a', 'an']:
                objects.add(match.strip())
    
    return objects

def extract_time_references(text: str) -> Set[str]:
    """Extract time references from text."""
    time_refs = set()
    
    time_patterns = [
        r'\b(morning|afternoon|evening|night|midnight|dawn|dusk)\b',
        r'\b(it\'s|it is)\s+(morning|afternoon|evening|night)',
        r'\b(?:three|two|one|four|five)\s+(?:weeks?|days?|hours?|minutes?)\s+(?:ago|earlier)',
        r'\b(?:December|January|February|March|April|May|June|July|August|September|October|November)\s+\d+',
    ]
    
    for pattern in time_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            if isinstance(match, tuple):
                match = ' '.join(match)
            if match:
                time_refs.add(match.strip())
    
    return time_refs

def scan_sections(sections_dir='src/content/sections'):
    """Scan all section files and extract full information."""
    sections_path = Path(sections_dir)
    
    if not sections_path.exists():
        print(f"Error: {sections_dir} directory not found!")
        return {}, {}, {}, {}
    
    section_files = sorted(sections_path.glob('section-*.md'))
    print(f"Scanning {len(section_files)} section files...")
    
    sections_info = {}
    outgoing_map = defaultdict(list)
    incoming_map = defaultdict(list)
    section_content = {}
    
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
            
            sections_info[md_file.name] = {
                'id': section_id,
                'title': title,
                'filename': md_file.name,
                'choices': choices
            }
            
            # Store full content for narrative checking
            section_content[md_file.name] = {
                'body': body,
                'title': title,
                'locations': extract_locations(body),
                'characters': extract_characters(body),
                'objects': extract_objects(body),
                'time_refs': extract_time_references(body)
            }
            
            # Build connection maps
            for choice in choices:
                target = choice.get('target', '')
                choice_text = choice.get('text', '')
                
                if target:
                    outgoing_map[md_file.name].append({
                        'target': target,
                        'text': choice_text
                    })
                    
                    incoming_map[target].append({
                        'source': md_file.name,
                        'text': choice_text
                    })
        
        except Exception as e:
            print(f"Error processing {md_file.name}: {e}")
            continue
    
    return sections_info, outgoing_map, incoming_map, section_content

def validate_structural_integrity(sections_info, outgoing_map, incoming_map):
    """Validate structural integrity of all connections."""
    issues = {
        'broken_links': [],
        'missing_files': [],
        'choice_mismatches': [],
        'bidirectional_inconsistencies': []
    }
    
    all_sections = set(sections_info.keys())
    all_targets = set()
    
    # Collect all targets
    for source, links in outgoing_map.items():
        for link in links:
            all_targets.add(link['target'])
    
    # Check for broken links (targets that don't exist)
    for source, links in outgoing_map.items():
        for link in links:
            target = link['target']
            if target not in all_sections:
                issues['broken_links'].append({
                    'source': source,
                    'target': target,
                    'choice': link['text']
                })
                if target not in [m['target'] for m in issues['missing_files']]:
                    issues['missing_files'].append({
                        'target': target,
                        'referenced_by': [source]
                    })
            else:
                # Update missing_files if we found the file
                for mf in issues['missing_files']:
                    if mf['target'] == target and source not in mf['referenced_by']:
                        mf['referenced_by'].append(source)
    
    # Check choice text matches between outgoing and what's in the file
    for source, links in outgoing_map.items():
        section = sections_info.get(source, {})
        file_choices = section.get('choices', [])
        
        for link in links:
            target = link['target']
            expected_text = link['text']
            
            # Find matching choice in file
            found = False
            for file_choice in file_choices:
                if file_choice.get('target') == target:
                    actual_text = file_choice.get('text', '')
                    if actual_text != expected_text:
                        issues['choice_mismatches'].append({
                            'source': source,
                            'target': target,
                            'expected': expected_text,
                            'actual': actual_text
                        })
                    found = True
                    break
            
            if not found:
                issues['choice_mismatches'].append({
                    'source': source,
                    'target': target,
                    'expected': expected_text,
                    'actual': 'CHOICE NOT FOUND IN FILE'
                })
    
    # Check bidirectional consistency
    for target, incoming_links in incoming_map.items():
        if target not in all_sections:
            continue
        
        # For each incoming link, verify it exists in outgoing map
        for incoming in incoming_links:
            source = incoming['source']
            expected_text = incoming['text']
            
            if source in outgoing_map:
                found = False
                for outgoing_link in outgoing_map[source]:
                    if outgoing_link['target'] == target and outgoing_link['text'] == expected_text:
                        found = True
                        break
                
                if not found:
                    issues['bidirectional_inconsistencies'].append({
                        'source': source,
                        'target': target,
                        'incoming_text': expected_text,
                        'outgoing_links': [l['text'] for l in outgoing_map[source] if l['target'] == target]
                    })
    
    return issues

def check_narrative_continuity(section_content, outgoing_map):
    """Check narrative continuity between connected sections."""
    issues = {
        'location_mismatches': [],
        'missing_characters': [],
        'missing_objects': [],
        'time_inconsistencies': [],
        'unclear_references': []
    }
    
    for source, links in outgoing_map.items():
        if source not in section_content:
            continue
        
        source_content = section_content[source]
        source_locations = source_content['locations']
        source_characters = source_content['characters']
        source_objects = source_content['objects']
        source_time = source_content['time_refs']
        
        for link in links:
            target = link['target']
            if target not in section_content:
                continue
            
            target_content = section_content[target]
            target_locations = target_content['locations']
            target_characters = target_content['characters']
            target_objects = target_content['objects']
            target_time = target_content['time_refs']
            
            # Check location consistency
            if source_locations and target_locations:
                # If source mentions a specific location, target should either:
                # 1. Mention the same location, or
                # 2. Have no location mentioned (transition), or
                # 3. Explicitly mention moving/changing location
                source_specific = {l for l in source_locations if len(l) > 5 and l[0].isupper()}
                target_specific = {l for l in target_locations if len(l) > 5 and l[0].isupper()}
                
                if source_specific and target_specific:
                    # Check for conflicting locations
                    conflicting = source_specific & target_specific
                    if not conflicting and len(source_specific) == 1 and len(target_specific) == 1:
                        # Potential location jump without explanation
                        source_loc = list(source_specific)[0]
                        target_loc = list(target_specific)[0]
                        if source_loc != target_loc:
                            # Check if there's a transition mentioned
                            transition_words = ['moved', 'went', 'traveled', 'walked', 'headed', 'arrived', 'reached']
                            has_transition = any(word in target_content['body'].lower() for word in transition_words)
                            if not has_transition:
                                issues['location_mismatches'].append({
                                    'source': source,
                                    'target': target,
                                    'source_location': source_loc,
                                    'target_location': target_loc
                                })
            
            # Check character continuity
            if source_characters:
                # Characters mentioned in source should either:
                # 1. Be mentioned in target, or
                # 2. Have their absence explained
                for char in source_characters:
                    if char not in target_characters:
                        # Check if character absence is explained
                        absence_words = ['left', 'gone', 'departed', 'stayed behind', 'remained']
                        has_explanation = any(word in target_content['body'].lower() for word in absence_words)
                        
                        # Also check if it's a character that might not always be present
                        if not has_explanation and char in ['Cheshire', 'Elara', 'Marcus', 'Velma']:
                            issues['missing_characters'].append({
                                'source': source,
                                'target': target,
                                'character': char
                            })
            
            # Check object continuity (if object was mentioned as being held/had)
            if source_objects:
                important_objects = {obj for obj in source_objects if any(
                    keyword in obj.lower() for keyword in ['keeper', 'button', 'book', 'ornament', 'vault']
                )}
                
                for obj in important_objects:
                    # If object is mentioned in source, it should either:
                    # 1. Be mentioned in target if still relevant, or
                    # 2. Have its absence explained
                    if obj not in target_objects:
                        # This is just a warning, not necessarily an error
                        # Objects can be put down, lost, etc.
                        pass
            
            # Check time consistency
            if source_time and target_time:
                # Look for conflicting time references
                source_times = {t.lower() for t in source_time}
                target_times = {t.lower() for t in target_time}
                
                # Check for obvious conflicts (morning vs night in same scene)
                time_conflicts = [
                    ('morning', 'night'), ('morning', 'evening'),
                    ('afternoon', 'night'), ('evening', 'morning'),
                    ('night', 'morning'), ('night', 'afternoon')
                ]
                
                for conflict_pair in time_conflicts:
                    if conflict_pair[0] in source_times and conflict_pair[1] in target_times:
                        issues['time_inconsistencies'].append({
                            'source': source,
                            'target': target,
                            'source_time': conflict_pair[0],
                            'target_time': conflict_pair[1]
                        })
    
    return issues

def generate_report(sections_info, structural_issues, narrative_issues, output_file='CONTINUITY_REPORT.md'):
    """Generate continuity report."""
    
    total_sections = len(sections_info)
    critical_count = (
        len(structural_issues['broken_links']) +
        len(structural_issues['missing_files'])
    )
    warning_count = (
        len(structural_issues['choice_mismatches']) +
        len(structural_issues['bidirectional_inconsistencies']) +
        len(narrative_issues['location_mismatches']) +
        len(narrative_issues['missing_characters']) +
        len(narrative_issues['time_inconsistencies'])
    )
    info_count = len(narrative_issues['missing_objects']) + len(narrative_issues['unclear_references'])
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# Continuity Report\n\n")
        f.write("This report validates story continuity across all sections.\n")
        f.write("It checks structural integrity (links, choice text) and basic narrative continuity.\n\n")
        f.write("**Note:** This file is automatically generated. Do not edit manually.\n\n")
        f.write("---\n\n")
        
        # Summary
        f.write("## Summary\n\n")
        f.write(f"- **Total sections checked:** {total_sections}\n")
        f.write(f"- **Critical issues:** {critical_count}\n")
        f.write(f"- **Warnings:** {warning_count}\n")
        f.write(f"- **Info:** {info_count}\n\n")
        
        if critical_count == 0 and warning_count == 0 and info_count == 0:
            f.write("✅ **No issues found!** All sections pass continuity checks.\n\n")
            f.write("---\n\n")
            return
        
        # Critical Issues
        if critical_count > 0:
            f.write("## Critical Issues\n\n")
            f.write("These issues must be fixed for the story to work correctly.\n\n")
            
            if structural_issues['broken_links']:
                f.write("### Broken Links\n\n")
                f.write("These links point to sections that don't exist:\n\n")
                for issue in sorted(structural_issues['broken_links'], key=lambda x: (x['source'], x['target'])):
                    f.write(f"- `{issue['source']}` → `{issue['target']}`\n")
                    f.write(f"  - Choice: \"{issue['choice']}\"\n")
                    f.write(f"  - **Action:** Create `{issue['target']}` or fix the choice target\n\n")
            
            if structural_issues['missing_files']:
                f.write("### Missing Section Files\n\n")
                f.write("These sections are referenced but don't exist as files:\n\n")
                for issue in sorted(structural_issues['missing_files'], key=lambda x: x['target']):
                    f.write(f"- `{issue['target']}`\n")
                    f.write(f"  - Referenced by: {', '.join(f'`{ref}`' for ref in sorted(issue['referenced_by']))}\n")
                    f.write(f"  - **Action:** Create this section file\n\n")
            
            f.write("---\n\n")
        
        # Warnings
        if warning_count > 0:
            f.write("## Warnings\n\n")
            f.write("These issues should be reviewed and may need fixes.\n\n")
            
            if structural_issues['choice_mismatches']:
                f.write("### Choice Text Mismatches\n\n")
                f.write("Choice text in section files doesn't match what's recorded:\n\n")
                for issue in sorted(structural_issues['choice_mismatches'], key=lambda x: (x['source'], x['target'])):
                    f.write(f"- `{issue['source']}` → `{issue['target']}`\n")
                    f.write(f"  - DECISIONS.md says: \"{issue['expected']}\"\n")
                    f.write(f"  - Actual choice: \"{issue['actual']}\"\n")
                    f.write(f"  - **Action:** Update choice text to match or regenerate DECISIONS.md\n\n")
            
            if structural_issues['bidirectional_inconsistencies']:
                f.write("### Bidirectional Inconsistencies\n\n")
                f.write("Incoming and outgoing links don't match:\n\n")
                for issue in sorted(structural_issues['bidirectional_inconsistencies'], key=lambda x: (x['source'], x['target'])):
                    f.write(f"- `{issue['source']}` → `{issue['target']}`\n")
                    f.write(f"  - Incoming link text: \"{issue['incoming_text']}\"\n")
                    f.write(f"  - Outgoing link texts: {issue['outgoing_links']}\n")
                    f.write(f"  - **Action:** Fix the choice text or regenerate DECISIONS.md\n\n")
            
            if narrative_issues['location_mismatches']:
                f.write("### Location Mismatches\n\n")
                f.write("Potential location jumps without explanation:\n\n")
                for issue in sorted(narrative_issues['location_mismatches'], key=lambda x: (x['source'], x['target'])):
                    f.write(f"- `{issue['source']}` → `{issue['target']}`\n")
                    f.write(f"  - Source location: {issue['source_location']}\n")
                    f.write(f"  - Target location: {issue['target_location']}\n")
                    f.write(f"  - **Action:** Review transition - add explanation if needed\n\n")
            
            if narrative_issues['missing_characters']:
                f.write("### Missing Characters\n\n")
                f.write("Characters present in source but not mentioned in target:\n\n")
                for issue in sorted(narrative_issues['missing_characters'], key=lambda x: (x['source'], x['target'])):
                    f.write(f"- `{issue['source']}` → `{issue['target']}`\n")
                    f.write(f"  - Character: {issue['character']}\n")
                    f.write(f"  - **Action:** Review - explain character's absence if needed\n\n")
            
            if narrative_issues['time_inconsistencies']:
                f.write("### Time Inconsistencies\n\n")
                f.write("Conflicting time references between sections:\n\n")
                for issue in sorted(narrative_issues['time_inconsistencies'], key=lambda x: (x['source'], x['target'])):
                    f.write(f"- `{issue['source']}` → `{issue['target']}`\n")
                    f.write(f"  - Source time: {issue['source_time']}\n")
                    f.write(f"  - Target time: {issue['target_time']}\n")
                    f.write(f"  - **Action:** Review - add time transition if needed\n\n")
            
            f.write("---\n\n")
        
        # Info
        if info_count > 0:
            f.write("## Info\n\n")
            f.write("Suggestions for improvement (not necessarily errors):\n\n")
            
            if narrative_issues['missing_objects']:
                f.write("### Missing Objects\n\n")
                f.write("Objects mentioned in source but not in target (may be intentional):\n\n")
                for issue in sorted(narrative_issues['missing_objects'], key=lambda x: (x['source'], x['target'])):
                    f.write(f"- `{issue['source']}` → `{issue['target']}`\n")
                    f.write(f"  - Object: {issue['object']}\n")
                    f.write(f"  - **Action:** Review - ensure object continuity if needed\n\n")
            
            if narrative_issues['unclear_references']:
                f.write("### Unclear References\n\n")
                f.write("Potential unclear pronoun or reference usage:\n\n")
                for issue in sorted(narrative_issues['unclear_references'], key=lambda x: (x['source'], x['target'])):
                    f.write(f"- `{issue['source']}` → `{issue['target']}`\n")
                    f.write(f"  - Issue: {issue['description']}\n")
                    f.write(f"  - **Action:** Review for clarity\n\n")
        
        f.write("---\n\n")
        f.write("## How to Fix Issues\n\n")
        f.write("1. **Broken Links / Missing Files**: Create the missing section files or fix choice targets\n")
        f.write("2. **Choice Mismatches**: Update choice text in section files to match, or regenerate DECISIONS.md\n")
        f.write("3. **Narrative Issues**: Review the sections and add transitions/explanations as needed\n")
        f.write("4. **Regenerate Reports**: After fixing issues, regenerate DECISIONS.md and this report\n\n")

if __name__ == '__main__':
    import sys
    
    sections_dir = sys.argv[1] if len(sys.argv) > 1 else 'src/content/sections'
    output_file = sys.argv[2] if len(sys.argv) > 2 else 'CONTINUITY_REPORT.md'
    
    print("Starting continuity check...")
    print("=" * 60)
    
    # Phase 1: Load sections
    print("\nPhase 1: Loading sections...")
    sections_info, outgoing_map, incoming_map, section_content = scan_sections(sections_dir)
    print(f"✓ Loaded {len(sections_info)} sections")
    
    # Phase 2: Structural validation
    print("\nPhase 2: Validating structural integrity...")
    structural_issues = validate_structural_integrity(sections_info, outgoing_map, incoming_map)
    
    critical_count = (
        len(structural_issues['broken_links']) +
        len(structural_issues['missing_files'])
    )
    warning_count = (
        len(structural_issues['choice_mismatches']) +
        len(structural_issues['bidirectional_inconsistencies'])
    )
    
    print(f"✓ Found {critical_count} critical issues, {warning_count} structural warnings")
    
    # Phase 3: Narrative continuity
    print("\nPhase 3: Checking narrative continuity...")
    narrative_issues = check_narrative_continuity(section_content, outgoing_map)
    
    narrative_warning_count = (
        len(narrative_issues['location_mismatches']) +
        len(narrative_issues['missing_characters']) +
        len(narrative_issues['time_inconsistencies'])
    )
    narrative_info_count = (
        len(narrative_issues['missing_objects']) +
        len(narrative_issues['unclear_references'])
    )
    
    print(f"✓ Found {narrative_warning_count} narrative warnings, {narrative_info_count} info items")
    
    # Phase 4: Generate report
    print(f"\nPhase 4: Generating report: {output_file}")
    generate_report(sections_info, structural_issues, narrative_issues, output_file)
    
    print("\n" + "=" * 60)
    print("Continuity check complete!")
    print(f"Report saved to: {output_file}")
    
    total_issues = (
        critical_count + warning_count + narrative_warning_count + narrative_info_count
    )
    
    if total_issues == 0:
        print("\n✅ No issues found! All sections pass continuity checks.")
    else:
        print(f"\n⚠️  Found {total_issues} total issues. Please review the report.")

