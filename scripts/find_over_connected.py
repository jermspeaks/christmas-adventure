#!/usr/bin/env python3
"""
Analyze section files to identify sections with too many incoming connections.
According to the "choose your own adventure" rule, sections should have at most
3 incoming connections. Any more than that, and the adventure no longer feels
like a choice.

This script identifies over-connected sections and analyzes which connections
might be redundant or unnecessary.
"""

import yaml
from pathlib import Path
from collections import defaultdict
from difflib import SequenceMatcher

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

def similarity(text1, text2):
    """Calculate similarity ratio between two texts."""
    return SequenceMatcher(None, text1.lower(), text2.lower()).ratio()

def analyze_redundancy(incoming_links):
    """
    Analyze incoming links for redundancy patterns.
    Returns a dictionary with redundancy analysis.
    """
    analysis = {
        'similar_choices': [],
        'island_sources': [],
        'exact_duplicates': []
    }
    
    # Group by choice text similarity
    choice_texts = [(link['text'], link) for link in incoming_links]
    
    # Find exact duplicate choice texts
    text_to_links = defaultdict(list)
    for text, link in choice_texts:
        text_to_links[text].append(link)
    
    for text, links in text_to_links.items():
        if len(links) > 1:
            analysis['exact_duplicates'].append({
                'text': text,
                'count': len(links),
                'sources': [link['source'] for link in links]
            })
    
    # Find similar choice texts (similarity > 0.7)
    processed = set()
    for i, (text1, link1) in enumerate(choice_texts):
        if i in processed:
            continue
        
        similar_group = [link1]
        for j, (text2, link2) in enumerate(choice_texts[i+1:], start=i+1):
            if j in processed:
                continue
            
            if similarity(text1, text2) > 0.7:
                similar_group.append(link2)
                processed.add(j)
        
        if len(similar_group) > 1:
            analysis['similar_choices'].append({
                'representative_text': text1,
                'count': len(similar_group),
                'sources': [link['source'] for link in similar_group]
            })
        
        processed.add(i)
    
    # Identify island sources (sections that might be unreachable)
    # We'll mark them but can't determine reachability without full graph analysis
    # For now, we'll note sections that appear to be in similar number ranges
    # (which might indicate they're from the same branch)
    return analysis

def find_over_connected(sections_dir='sections', max_connections=3):
    """
    Find all sections that have more than max_connections incoming links.
    Returns a list of over-connected sections with their incoming link details.
    """
    sections_path = Path(sections_dir)
    
    # Get all section files
    section_files = sorted(sections_path.glob('section-*.md'))
    
    print(f"Analyzing {len(section_files)} section files...")
    
    # Track all sections that exist
    existing_sections = {}
    
    # Build reverse index: for each target, which sections point to it
    incoming_links = defaultdict(list)
    
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
                    incoming_links[target].append({
                        'source': md_file.name,
                        'source_id': section_id,
                        'source_title': title,
                        'text': choice.get('text', ''),
                        'target': target
                    })
        
        except Exception as e:
            print(f"Error processing {md_file.name}: {e}")
            continue
    
    # Find over-connected sections (more than max_connections incoming links)
    over_connected = []
    
    for target, links in incoming_links.items():
        if len(links) > max_connections:
            # Get target section info
            target_info = existing_sections.get(target, {})
            
            # Analyze redundancy
            redundancy = analyze_redundancy(links)
            
            over_connected.append({
                'filename': target,
                'id': target_info.get('id', ''),
                'title': target_info.get('title', 'Untitled'),
                'incoming_count': len(links),
                'incoming_links': links,
                'redundancy': redundancy
            })
    
    # Sort by incoming count (descending)
    over_connected.sort(key=lambda x: x['incoming_count'], reverse=True)
    
    return over_connected

def generate_report(over_connected, output_file='UNNECESSARY_CONNECTIONS.md'):
    """Generate a markdown report of over-connected sections."""
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# Unnecessary Connections Analysis\n\n")
        f.write("This file documents all sections that have more than 3 incoming connections, ")
        f.write("violating the \"at most 3 loops back\" rule for choose-your-own-adventure stories.\n\n")
        f.write("**The Rule:** At most, we can loop back 3 times. Any more, and the \"choose your own adventure\" ")
        f.write("no longer feels like a choice. This rule can be broken only if it makes sense for the story.\n\n")
        f.write("**What this means:**\n")
        f.write("- Sections with more than 3 incoming connections may need some connections terminated or redirected\n")
        f.write("- Redundant connections (similar choice text, duplicate paths) are prime candidates for removal\n")
        f.write("- Connections from unreachable/island sections should be considered for termination\n\n")
        f.write("---\n\n")
        
        if not over_connected:
            f.write("**No over-connected sections found! All sections have 3 or fewer incoming connections.**\n")
            return
        
        for section in over_connected:
            f.write(f"## {section['filename']} - \"{section['title']}\"\n\n")
            f.write(f"**Section ID:** `{section['id']}`\n\n")
            f.write(f"**Total Incoming Connections:** **{section['incoming_count']}** (exceeds limit of 3)\n\n")
            
            # List all incoming links
            f.write("### All Incoming Connections\n\n")
            for i, link in enumerate(section['incoming_links'], 1):
                f.write(f"{i}. From `{link['source']}` - \"{link['source_title']}\"\n")
                f.write(f"   - Choice text: \"{link['text']}\"\n")
            
            f.write("\n")
            
            # Redundancy analysis
            redundancy = section['redundancy']
            has_redundancy = (redundancy['exact_duplicates'] or 
                            redundancy['similar_choices'] or 
                            redundancy['island_sources'])
            
            if has_redundancy:
                f.write("### Redundancy Analysis\n\n")
                
                if redundancy['exact_duplicates']:
                    f.write("**Exact Duplicate Choice Texts:**\n\n")
                    for dup in redundancy['exact_duplicates']:
                        f.write(f"- Choice text \"{dup['text']}\" appears {dup['count']} times from:\n")
                        for source in dup['sources']:
                            f.write(f"  - `{source}`\n")
                        f.write("\n")
                
                if redundancy['similar_choices']:
                    f.write("**Similar Choice Texts (potential redundancy):**\n\n")
                    for similar in redundancy['similar_choices']:
                        f.write(f"- Similar choices (representative: \"{similar['representative_text']}\") appear {similar['count']} times from:\n")
                        for source in similar['sources']:
                            f.write(f"  - `{source}`\n")
                        f.write("\n")
                
                if not redundancy['exact_duplicates'] and not redundancy['similar_choices']:
                    f.write("*No obvious redundancy patterns detected in choice texts.*\n\n")
            else:
                f.write("### Redundancy Analysis\n\n")
                f.write("*No obvious redundancy patterns detected.*\n\n")
            
            f.write("---\n\n")
        
        f.write("## Summary\n\n")
        f.write(f"Total over-connected sections: **{len(over_connected)}**\n\n")
        
        # Count sections by connection count
        count_distribution = defaultdict(int)
        for section in over_connected:
            count_distribution[section['incoming_count']] += 1
        
        f.write("**Distribution by connection count:**\n")
        for count in sorted(count_distribution.keys(), reverse=True):
            f.write(f"- {count} connections: **{count_distribution[count]}** sections\n")
        
        f.write("\n")
        
        # Count total redundant connections
        total_exact_duplicates = sum(
            len(dup['sources']) - 1  # -1 because we keep one
            for section in over_connected
            for dup in section['redundancy']['exact_duplicates']
        )
        
        total_similar_choices = sum(
            len(similar['sources']) - 1  # -1 because we keep one
            for section in over_connected
            for similar in section['redundancy']['similar_choices']
        )
        
        if total_exact_duplicates > 0 or total_similar_choices > 0:
            f.write("**Potential redundant connections:**\n")
            if total_exact_duplicates > 0:
                f.write(f"- Exact duplicate choice texts: **{total_exact_duplicates}** connections could be removed\n")
            if total_similar_choices > 0:
                f.write(f"- Similar choice texts: **{total_similar_choices}** connections might be redundant\n")

if __name__ == '__main__':
    import sys
    
    sections_dir = sys.argv[1] if len(sys.argv) > 1 else 'sections'
    output_file = sys.argv[2] if len(sys.argv) > 2 else 'UNNECESSARY_CONNECTIONS.md'
    max_connections = int(sys.argv[3]) if len(sys.argv) > 3 else 3
    
    print("Starting over-connected sections analysis...")
    over_connected = find_over_connected(sections_dir, max_connections)
    
    print(f"\nFound {len(over_connected)} over-connected sections")
    
    if over_connected:
        print("\nOver-connected sections:")
        for section in over_connected:
            print(f"  - {section['filename']}: {section['incoming_count']} incoming connections")
    
    print(f"\nGenerating report: {output_file}")
    generate_report(over_connected, output_file)
    
    print("\nAnalysis complete!")

