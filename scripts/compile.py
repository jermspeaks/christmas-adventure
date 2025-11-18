#!/usr/bin/env python3
"""
Compilation script for Choose Your Own Adventure book.
Generates HTML, PDF, and EPUB outputs with page numbers and choice references.
"""

import os
import json
import re
import yaml
import markdown
from pathlib import Path
from datetime import datetime

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

def load_page_mapping(mapping_file='page-mapping.json'):
    """Load the page mapping from JSON file."""
    if not os.path.exists(mapping_file):
        raise FileNotFoundError(f"Page mapping file not found: {mapping_file}. Run randomize.py first!")
    
    with open(mapping_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def resolve_choice_target(target_file, page_mapping):
    """Resolve a target filename to a page number."""
    target_id = target_file.replace('.md', '')
    if target_id in page_mapping['sections']:
        return page_mapping['sections'][target_id]['page']
    return None

def process_section(md_file, page_mapping):
    """Process a single section file and return formatted content."""
    with open(md_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    frontmatter, body = parse_frontmatter(content)
    if not frontmatter or 'id' not in frontmatter:
        return None
    
    section_id = frontmatter['id']
    page_info = page_mapping['sections'].get(section_id)
    
    if not page_info:
        return None
    
    page_num = page_info['page']
    title = frontmatter.get('title', 'Untitled')
    body = body.strip()
    
    # Remove the first heading from body if it matches the title (to avoid duplicate titles)
    # Match heading with any number of #, optional quotes around title, and any trailing whitespace/newlines
    title_heading_pattern = re.compile(r'^#+\s+["\']?' + re.escape(title) + r'["\']?\s*\n+', re.IGNORECASE)
    if title_heading_pattern.match(body):
        body = title_heading_pattern.sub('', body).strip()
    
    # Process choices and extract target section IDs
    choices = []
    if 'choices' in frontmatter and frontmatter['choices']:
        for choice in frontmatter['choices']:
            choice_text = choice.get('text', '')
            target_file = choice.get('target', '')
            # Extract section ID from filename (e.g., "section-2.md" -> "section-2")
            target_section_id = target_file.replace('.md', '')
            choices.append({
                'text': choice_text,
                'target': target_section_id
            })
    
    # For PDF/EPUB: Process choices and replace targets with page numbers
    choices_html = ""
    if choices:
        choices_html = "\n\n## Your Choices:\n\n"
        for choice in choices:
            target_page = resolve_choice_target(choice['target'] + '.md', page_mapping)
            if target_page:
                choices_html += f"- **{choice['text']}** → Turn to page {target_page}\n"
            else:
                choices_html += f"- **{choice['text']}** → (Invalid target: {choice['target']})\n"
    
    # Combine title, body, and choices (no page number displayed)
    full_content = f"# {title}\n\n{body}{choices_html}"
    
    return {
        'id': section_id,
        'page': page_num,
        'title': title,
        'body': body,
        'choices': choices,
        'content': full_content,
        'html': markdown.markdown(full_content, extensions=['extra', 'codehilite'])
    }

def generate_html(sections_data, output_file='output/adventure.html'):
    """Generate HTML output."""
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # Prepare game data: map section ID to section data
    game_data = {}
    for section in sections_data:
        # Render body HTML separately
        body_html = markdown.markdown(section['body'], extensions=['extra', 'codehilite'])
        game_data[section['id']] = {
            'id': section['id'],
            'title': section['title'],
            'body': section['body'],
            'bodyHtml': body_html,
            'choices': section.get('choices', [])
        }
    
    # Find starting section (section-1 or first section)
    starting_section_id = 'section-1' if 'section-1' in game_data else sections_data[0]['id']
    
    # Embed game data as JSON
    game_data_json = json.dumps(game_data, indent=2, ensure_ascii=False)
    
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Choose Your Own Christmas Adventure</title>
    <style>
        body {
            font-family: Georgia, serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            line-height: 1.6;
            background-color: #fafafa;
            min-height: 100vh;
        }
        .header {
            background: white;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .header h1 {
            margin: 0;
            color: #c41e3a;
            font-size: 1.5em;
        }
        #reset-btn {
            background-color: #c41e3a;
            color: white;
            border: none;
            padding: 10px 20px;
            font-size: 1em;
            cursor: pointer;
            border-radius: 4px;
            font-family: Georgia, serif;
            transition: background-color 0.3s;
        }
        #reset-btn:hover {
            background-color: #a0172e;
        }
        #reset-btn:active {
            background-color: #7d1123;
        }
        .section-container {
            background: white;
            padding: 40px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            min-height: 400px;
        }
        .section-container h1 {
            color: #c41e3a;
            border-bottom: 3px solid #c41e3a;
            padding-bottom: 10px;
            margin-top: 0;
        }
        .section-container h2 {
            color: #2d5016;
            margin-top: 30px;
        }
        .choices-container {
            margin-top: 30px;
        }
        .choice-btn {
            display: block;
            width: 100%;
            margin: 15px 0;
            padding: 15px 20px;
            background-color: #f0f0f0;
            border: 2px solid #c41e3a;
            border-left: 6px solid #c41e3a;
            color: #333;
            text-align: left;
            font-size: 1em;
            font-family: Georgia, serif;
            cursor: pointer;
            transition: all 0.3s;
            border-radius: 4px;
        }
        .choice-btn:hover {
            background-color: #e0e0e0;
            border-color: #a0172e;
            border-left-color: #a0172e;
            transform: translateX(5px);
        }
        .choice-btn:active {
            background-color: #d0d0d0;
        }
        .section-body {
            margin-bottom: 20px;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>Choose Your Own Christmas Adventure</h1>
        <button id="reset-btn" onclick="resetGame()">Start Over</button>
    </div>
    <div class="section-container" id="section-container">
        <p>Loading...</p>
    </div>

    <script>
        // Game data embedded from compilation
        const gameData = """ + game_data_json + """;
        const STARTING_SECTION = '""" + starting_section_id + """';
        let currentSectionId = STARTING_SECTION;

        function loadGameData() {
            // Game data is already loaded from embedded JSON
            showSection(STARTING_SECTION);
        }

        function showSection(sectionId) {
            const section = gameData[sectionId];
            if (!section) {
                document.getElementById('section-container').innerHTML = 
                    '<h1>Error</h1><p>Section not found: ' + sectionId + '</p>';
                return;
            }

            currentSectionId = sectionId;
            const container = document.getElementById('section-container');
            
            let html = '<h1>' + escapeHtml(section.title) + '</h1>';
            html += '<div class="section-body">' + section.bodyHtml + '</div>';
            
            if (section.choices && section.choices.length > 0) {
                html += '<div class="choices-container"><h2>Your Choices:</h2>';
                for (let i = 0; i < section.choices.length; i++) {
                    const choice = section.choices[i];
                    const targetJson = JSON.stringify(choice.target);
                    html += '<button class="choice-btn" onclick=\'makeChoice(' + 
                            targetJson + ')\'>' + 
                            escapeHtml(choice.text) + '</button>';
                }
                html += '</div>';
            } else {
                html += '<div class="choices-container"><p><em>The End</em></p></div>';
            }
            
            container.innerHTML = html;
            // Scroll to top when showing new section
            window.scrollTo(0, 0);
        }

        function makeChoice(targetSectionId) {
            if (gameData[targetSectionId]) {
                showSection(targetSectionId);
            } else {
                alert('Invalid choice target: ' + targetSectionId);
            }
        }

        function resetGame() {
            showSection(STARTING_SECTION);
        }

        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }

        // Initialize game when page loads
        window.addEventListener('DOMContentLoaded', loadGameData);
    </script>
</body>
</html>"""
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"HTML generated: {output_file}")

def generate_pdf_via_pandoc(sections_data, output_file='output/adventure.pdf'):
    """Generate PDF using pandoc from markdown (more reliable than HTML)."""
    import subprocess
    import tempfile
    
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # Create a temporary markdown file with all sections (like EPUB generation)
    sorted_sections = sorted(sections_data, key=lambda x: x['page'])
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
        temp_md = f.name
        f.write("# Choose Your Own Christmas Adventure\n\n")
        f.write(f"*Generated on {datetime.now().strftime('%Y-%m-%d')}*\n\n")
        
        for i, section in enumerate(sorted_sections):
            if i > 0:
                f.write("\\newpage\n\n")
            f.write(section['content'])
            f.write("\n\n")
    
    # Try multiple PDF engines in order of preference
    pdf_engines = ['pdflatex', 'xelatex', 'lualatex']
    pdf_engine = None
    
    # Check which engine is available
    for engine in pdf_engines:
        try:
            result = subprocess.run(
                ['which', engine],
                capture_output=True,
                check=False
            )
            if result.returncode == 0:
                pdf_engine = engine
                break
        except:
            continue
    
    if not pdf_engine:
        # Try without specifying engine - let pandoc choose
        cmd = [
            'pandoc',
            temp_md,
            '-o', output_file,
            '-V', 'geometry:margin=1in',
            '-V', 'fontsize=11pt'
        ]
    else:
        cmd = [
            'pandoc',
            temp_md,
            '-o', output_file,
            f'--pdf-engine={pdf_engine}',
            '-V', 'geometry:margin=1in',
            '-V', 'fontsize=11pt'
        ]
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"PDF generated: {output_file}")
        if pdf_engine:
            print(f"  (using {pdf_engine})")
        os.unlink(temp_md)
        return True
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr if e.stderr else (e.stdout if e.stdout else str(e))
        print(f"Error generating PDF: {e}")
        if error_msg:
            print(f"Error details: {error_msg}")
        if not pdf_engine:
            print("\nNo LaTeX engine found. Please install one of the following:")
            print("  - BasicTeX: brew install --cask basictex")
            print("  - MacTeX: brew install --cask mactex")
            print("\nAfter installation, you may need to add to PATH:")
            print("  export PATH=\"/Library/TeX/texbin:$PATH\"")
        else:
            print(f"\nMake sure pandoc and {pdf_engine} are properly installed")
        os.unlink(temp_md)
        return False
    except FileNotFoundError:
        print("pandoc not found. Install it with: brew install pandoc")
        os.unlink(temp_md)
        return False

def generate_epub(sections_data, output_file='output/adventure.epub'):
    """Generate EPUB using pandoc."""
    import subprocess
    import tempfile
    
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # Create a temporary markdown file with all sections
    sorted_sections = sorted(sections_data, key=lambda x: x['page'])
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
        temp_md = f.name
        f.write("# Choose Your Own Christmas Adventure\n\n")
        f.write(f"*Generated on {datetime.now().strftime('%Y-%m-%d')}*\n\n")
        
        for section in sorted_sections:
            f.write(f"\n\n---\n\n")
            f.write(section['content'])
            f.write("\n\n")
    
    cmd = [
        'pandoc',
        temp_md,
        '-o', output_file,
        '--epub-cover-image=cover.jpg' if os.path.exists('cover.jpg') else '',
        '--toc',
        '--epub-metadata=metadata.xml' if os.path.exists('metadata.xml') else ''
    ]
    cmd = [c for c in cmd if c]  # Remove empty strings
    
    try:
        subprocess.run(cmd, check=True, capture_output=True)
        print(f"EPUB generated: {output_file}")
        os.unlink(temp_md)
    except subprocess.CalledProcessError as e:
        print(f"Error generating EPUB: {e}")
        print("Make sure pandoc is installed")
    except FileNotFoundError:
        print("pandoc not found. Install it with: brew install pandoc")

def compile_book(sections_dir='sections', mapping_file='page-mapping.json', 
                 output_dir='output'):
    """Main compilation function."""
    print("Loading page mapping...")
    page_mapping = load_page_mapping(mapping_file)
    
    print("Processing sections...")
    sections_path = Path(sections_dir)
    sections_data = []
    
    for md_file in sections_path.glob('*.md'):
        section_data = process_section(md_file, page_mapping)
        if section_data:
            sections_data.append(section_data)
            print(f"  Processed: {section_data['id']} (Page {section_data['page']})")
    
    if not sections_data:
        print("No sections found to compile!")
        return
    
    print(f"\nCompiling {len(sections_data)} sections...")
    
    # Generate HTML
    html_file = os.path.join(output_dir, 'adventure.html')
    generate_html(sections_data, html_file)
    
    # Generate PDF
    pdf_file = os.path.join(output_dir, 'adventure.pdf')
    pdf_success = generate_pdf_via_pandoc(sections_data, pdf_file)
    if not pdf_success:
        print("  (Skipping PDF generation - continuing with other formats)")
    
    # Generate EPUB
    epub_file = os.path.join(output_dir, 'adventure.epub')
    generate_epub(sections_data, epub_file)
    
    print("\nCompilation complete!")

if __name__ == '__main__':
    import sys
    
    sections_dir = sys.argv[1] if len(sys.argv) > 1 else 'sections'
    mapping_file = sys.argv[2] if len(sys.argv) > 2 else 'page-mapping.json'
    output_dir = sys.argv[3] if len(sys.argv) > 3 else 'output'
    
    compile_book(sections_dir, mapping_file, output_dir)

