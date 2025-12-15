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
try:
    import PyPDF2
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

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

def regenerate_page_mapping(sections_dir='src/content/sections', mapping_file='page-mapping.json'):
    """Regenerate the page mapping by calling randomize.py."""
    import subprocess
    import sys
    
    script_path = Path(__file__).parent / 'randomize.py'
    cmd = [sys.executable, str(script_path), sections_dir, mapping_file]
    
    try:
        subprocess.run(cmd, check=True)
        print(f"Page mapping regenerated: {mapping_file}")
    except subprocess.CalledProcessError as e:
        print(f"Error regenerating page mapping: {e}")
        raise

def ensure_page_mapping(sections_dir='src/content/sections', mapping_file='page-mapping.json'):
    """Ensure page mapping exists and includes all sections. Regenerate if needed."""
    sections_path = Path(sections_dir)
    if not sections_path.exists():
        print(f"Error: {sections_dir} directory not found!")
        return False
    
    # Check if mapping exists
    if not os.path.exists(mapping_file):
        print("Page mapping not found. Generating...")
        regenerate_page_mapping(sections_dir, mapping_file)
        return True
    
    # Check if mapping is valid
    try:
        page_mapping = load_page_mapping(mapping_file)
        if not page_mapping or 'sections' not in page_mapping:
            print("Page mapping is invalid. Regenerating...")
            regenerate_page_mapping(sections_dir, mapping_file)
            return True
    except Exception as e:
        print(f"Error loading page mapping: {e}. Regenerating...")
        regenerate_page_mapping(sections_dir, mapping_file)
        return True
    
    # Check if all sections are in the mapping
    needs_regeneration = False
    for md_file in sections_path.glob('*.md'):
        try:
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            frontmatter, _ = parse_frontmatter(content)
            if frontmatter and 'id' in frontmatter:
                section_id = frontmatter['id']
                if section_id not in page_mapping['sections']:
                    needs_regeneration = True
                    break
        except Exception:
            # Skip files that can't be parsed
            continue
    
    if needs_regeneration:
        print("New sections detected. Regenerating page mapping...")
        regenerate_page_mapping(sections_dir, mapping_file)
        return True
    
    return True

def load_page_spans(spans_file='output/page-spans.json'):
    """Load the page spans from JSON file if it exists."""
    if not os.path.exists(spans_file):
        return None
    
    with open(spans_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def resolve_choice_target(target_file, page_mapping, page_spans=None):
    """Resolve a target filename to a displayed page number.
    
    Uses page-spans.json if available (physical PDF pages), otherwise falls back
    to page-mapping.json (logical page numbers).
    
    Page numbering system:
    - Physical PDF pages: 1 (title, no number), 2 (spacer, no number), 3+ (content)
    - Displayed page numbers: (none), (none), 1, 2, 3... (reset after spacer)
    - Logical page numbers from mapping: 1, 2, 3... (already correct)
    
    So we convert physical pages (from page_spans) by subtracting 2,
    but logical pages (from page_mapping) are already correct.
    """
    target_id = target_file.replace('.md', '')
    
    # First try to use actual PDF page spans if available
    # These are physical page numbers (3, 4, 5...), need to convert to displayed (1, 2, 3...)
    if page_spans and target_id in page_spans:
        physical_page = page_spans[target_id]['start']
        # Subtract 2 to account for title page (1) and spacer page (2)
        return physical_page - 2
    
    # Fall back to logical page number from page-mapping.json
    # These are already correct (1, 2, 3...) and match displayed page numbers
    if target_id in page_mapping['sections']:
        return page_mapping['sections'][target_id]['page']
    
    return None

def process_section(md_file, page_mapping, page_spans=None):
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
            target_page = resolve_choice_target(choice['target'] + '.md', page_mapping, page_spans)
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

def analyze_pdf_page_spans(pdf_file, sections_data):
    """Analyze PDF to determine which physical pages each section spans.
    
    Returns a dictionary mapping section_id to {'start': page_num, 'end': page_num}.
    
    Note: Returns physical PDF page numbers (3, 4, 5...) where content starts on
    physical page 3 (after title page 1 and spacer page 2). These need to be
    converted to displayed page numbers (1, 2, 3...) by subtracting 2 in
    resolve_choice_target().
    """
    if not PDF_AVAILABLE:
        print("  PyPDF2 not available. Install it with: pip install PyPDF2")
        return None
    
    if not os.path.exists(pdf_file):
        print(f"  PDF file not found: {pdf_file}")
        return None
    
    print("  Analyzing PDF to detect page spans...")
    
    try:
        page_spans = {}
        
        # Open PDF and extract text from each page
        with open(pdf_file, 'rb') as f:
            pdf_reader = PyPDF2.PdfReader(f)
            total_pages = len(pdf_reader.pages)
            
            # Extract text from all pages
            page_texts = []
            for page_num in range(total_pages):
                page = pdf_reader.pages[page_num]
                text = page.extract_text()
                page_texts.append(text)
        
        # Sort sections by their logical page order
        sorted_sections = sorted(sections_data, key=lambda x: x['page'])
        
        # Match section titles to PDF pages
        # We'll search sequentially since sections appear in order
        section_page_map = {}  # Maps section_id to PDF page number where it starts
        current_search_start = 3  # Start searching from page 3 (skip title page 1 and spacer page 2)
        
        for section in sorted_sections:
            section_id = section['id']
            title = section['title']
            
            # Normalize title for matching
            normalized_title = re.sub(r'\s+', ' ', title).strip().lower()
            
            # Try to find the title starting from where we expect it
            # Search from current_search_start to end, but prioritize pages near logical page
            logical_page = section['page']
            search_pages = []
            
            # First, try pages near the logical page number
            for offset in range(0, min(20, total_pages)):
                candidate = min(logical_page + offset, total_pages)
                if candidate >= current_search_start and candidate not in section_page_map.values():
                    if candidate not in search_pages:
                        search_pages.append(candidate)
            
            # Then add remaining pages in order
            for page_num in range(current_search_start, total_pages + 1):
                if page_num not in search_pages and page_num not in section_page_map.values():
                    search_pages.append(page_num)
            
            found_page = None
            for page_num in search_pages:
                if page_num > total_pages:
                    continue
                    
                page_text = page_texts[page_num - 1]  # Convert to 0-based index
                # Normalize text for comparison
                normalized_page_text = re.sub(r'\s+', ' ', page_text).strip().lower()
                
                # Check if title appears in this page (prefer near the beginning)
                # Look in first 500 chars for better accuracy
                page_start = normalized_page_text[:500] if len(normalized_page_text) > 500 else normalized_page_text
                
                if normalized_title in page_start or normalized_title in normalized_page_text:
                    found_page = page_num
                    section_page_map[section_id] = page_num
                    current_search_start = page_num + 1  # Next section starts after this one
                    break
            
            if not found_page:
                # Fallback: use logical page if available and not assigned
                if logical_page <= total_pages and logical_page not in section_page_map.values():
                    section_page_map[section_id] = logical_page
                    current_search_start = logical_page + 1
                else:
                    # Find next unassigned page
                    for page_num in range(current_search_start, total_pages + 1):
                        if page_num not in section_page_map.values():
                            section_page_map[section_id] = page_num
                            current_search_start = page_num + 1
                            break
        
        # Now determine page spans (start and end) for each section
        # The end of one section is the start of the next minus 1
        for i, section in enumerate(sorted_sections):
            section_id = section['id']
            start_page = section_page_map.get(section_id)
            
            if start_page:
                # Find the start of the next section to determine end page
                if i + 1 < len(sorted_sections):
                    next_section = sorted_sections[i + 1]
                    next_start = section_page_map.get(next_section['id'])
                    if next_start:
                        end_page = next_start - 1
                    else:
                        # If next section not found, assume this section spans to the end
                        end_page = total_pages
                else:
                    # Last section spans to the end
                    end_page = total_pages
                
                # Account for title page (1) and spacer page (2) in page spans
                # The page spans already reflect actual PDF pages, so no adjustment needed here
                
                # Ensure end_page is at least start_page
                end_page = max(start_page, end_page)
                
                page_spans[section_id] = {
                    'start': start_page,
                    'end': end_page
                }
        
        print(f"  Detected page spans for {len(page_spans)} sections")
        return page_spans
        
    except Exception as e:
        print(f"  Error analyzing PDF: {e}")
        import traceback
        traceback.print_exc()
        return None

def save_page_spans(page_spans, output_file='output/page-spans.json'):
    """Save page spans to JSON file.
    
    The page spans contain physical PDF page numbers (3, 4, 5...) where
    content sections start. These are converted to displayed page numbers
    (1, 2, 3...) when used in resolve_choice_target().
    """
    if page_spans is None:
        return
    
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(page_spans, f, indent=2, ensure_ascii=False)
    
    print(f"  Page spans saved to: {output_file}")

def calculate_gutter_margin(page_count):
    """Calculate gutter margin addition based on total page count.
    
    Lulu printing requirements specify asymmetric margins for binding based on page count.
    The gutter is an increased page margin on the binding side to account for the portion
    of the page inserted and glued into the bookbinding.
    
    Gutter margin requirements (from Lulu Book Creation Guide):
    - <60 pages: 0.5 in total inside margin (no extra gutter)
    - 61-150 pages: Add 0.125 in to inside margin (0.625 in total)
    - 151-400 pages: Add 0.5 in to inside margin (1 in total)
    - 400-600 pages: Add 0.625 in to inside margin (1.125 in total)
    - >600 pages: Add 0.75 in to inside margin (1.25 in total)
    
    Args:
        page_count: Total number of pages in the book (including title/spacer pages)
    
    Returns:
        float: The additional margin (in inches) to add to the base 0.5 in inside margin
    """
    if page_count < 60:
        return 0.0  # No extra gutter, just base 0.5 in margin
    elif page_count <= 150:
        return 0.125  # Total inside margin: 0.625 in
    elif page_count <= 400:
        return 0.5  # Total inside margin: 1.0 in
    elif page_count <= 600:
        return 0.625  # Total inside margin: 1.125 in
    else:
        return 0.75  # Total inside margin: 1.25 in

def generate_pdf_via_pandoc(sections_data, output_file='output/adventure.pdf'):
    """Generate PDF using pandoc from markdown (more reliable than HTML).
    
    Creates a PDF with:
    - Physical page 1: Title page (no page number displayed)
    - Physical page 2: Spacer page (no page number displayed)
    - Physical page 3+: Content sections (displayed as pages 1, 2, 3...)
    - Last two pages: Blank pages (no page numbers displayed)
    
    Page numbering is reset after the spacer page so content displays starting from 1.
    
    Uses 0.75 inch margins on all sides. Page numbers are positioned 0.5 inches higher
    than default to prevent cutoff during printing.
    All fonts embedded automatically by LaTeX/pandoc.
    """
    import subprocess
    import tempfile
    
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # Create a temporary markdown file with all sections (like EPUB generation)
    sorted_sections = sorted(sections_data, key=lambda x: x['page'])
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
        temp_md = f.name
        # Title page (physical page 1) - no page number displayed
        f.write("\\thispagestyle{empty}\n")
        f.write("\\vspace*{\\fill}\n")
        f.write("\\begin{center}\n")
        f.write("\\Huge\\textbf{Choose Your Own Adventure}\n\n")
        f.write("\\vspace{2cm}\n")
        f.write("\\Large Version 1.0\n")
        f.write("\\end{center}\n")
        f.write("\\vspace*{\\fill}\n")
        f.write("\\newpage\n\n")
        
        # Spacer page (physical page 2) - blank page for printing, no page number displayed
        f.write("\\thispagestyle{empty}\n")
        f.write("\\newpage\n\n")
        
        # Reset page counter so content pages display as starting from page 1
        f.write("\\setcounter{page}{1}\n\n")
        
        # Content sections start from physical page 3, but display as page 1, 2, 3...
        for i, section in enumerate(sorted_sections):
            f.write("\\newpage\n\n")
            f.write(section['content'])
            f.write("\n\n")
        
        # Two blank pages at the end (for printing/binding requirements) - no page numbers displayed
        f.write("\\thispagestyle{empty}\n")
        f.write("\\newpage\n\n")
        f.write("\\thispagestyle{empty}\n")
        f.write("\\newpage\n\n")
    
    # Create a LaTeX header file to position page numbers 0.5 inches higher
    with tempfile.NamedTemporaryFile(mode='w', suffix='.tex', delete=False, encoding='utf-8') as header_file:
        header_tex = header_file.name
        header_file.write("\\usepackage{fancyhdr}\n")
        header_file.write("\\pagestyle{fancy}\n")
        # Raise page number by 0.5 inches to move it up from the bottom edge
        # Positive value in raisebox moves content upward
        header_file.write("\\fancyfoot[C]{\\raisebox{0.5in}{\\thepage}}\n")
        header_file.write("\\fancyhead{}\n")
        header_file.write("\\renewcommand{\\headrulewidth}{0pt}\n")
        header_file.write("\\renewcommand{\\footrulewidth}{0pt}\n")
    
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
    
    # Set margins to 0.75 inches on all sides
    margin_settings = [
        '-V', 'geometry:margin=0.75in',
        '-H', header_tex  # Include LaTeX header for page number positioning
    ]
    
    if not pdf_engine:
        # Try without specifying engine - let pandoc choose
        cmd = [
            'pandoc',
            temp_md,
            '-o', output_file,
            '-V', 'fontsize=11pt'
        ] + margin_settings
    else:
        cmd = [
            'pandoc',
            temp_md,
            '-o', output_file,
            f'--pdf-engine={pdf_engine}',
            '-V', 'fontsize=11pt'
        ] + margin_settings
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"PDF generated: {output_file}")
        if pdf_engine:
            print(f"  (using {pdf_engine})")
        os.unlink(temp_md)
        os.unlink(header_tex)
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
        if os.path.exists(header_tex):
            os.unlink(header_tex)
        return False
    except FileNotFoundError:
        print("pandoc not found. Install it with: brew install pandoc")
        os.unlink(temp_md)
        if os.path.exists(header_tex):
            os.unlink(header_tex)
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
        # Title page
        f.write("# Choose Your Own Adventure\n\n")
        f.write("*Version 1.0*\n\n")
        f.write("---\n\n")
        
        # Spacer page (blank for EPUB)
        f.write("\n\n---\n\n")
        
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

def compile_book(sections_dir='src/content/sections', mapping_file='page-mapping.json', 
                 output_dir='output'):
    """Main compilation function."""
    # Ensure page mapping is up to date before compiling
    ensure_page_mapping(sections_dir, mapping_file)
    
    print("Loading page mapping...")
    page_mapping = load_page_mapping(mapping_file)
    
    # Try to load existing page spans
    page_spans_file = os.path.join(output_dir, 'page-spans.json')
    page_spans = load_page_spans(page_spans_file)
    
    print("Processing sections...")
    sections_path = Path(sections_dir)
    sections_data = []
    
    for md_file in sections_path.glob('*.md'):
        section_data = process_section(md_file, page_mapping, page_spans)
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
    
    # Generate PDF (first pass - may have incorrect page numbers in choices)
    pdf_file = os.path.join(output_dir, 'adventure.pdf')
    pdf_success = generate_pdf_via_pandoc(sections_data, pdf_file)
    
    # After PDF generation, analyze it to detect actual page spans
    if pdf_success:
        detected_spans = analyze_pdf_page_spans(pdf_file, sections_data)
        if detected_spans:
            save_page_spans(detected_spans, page_spans_file)
            # Re-process sections with updated page spans
            page_spans = detected_spans
            print("  Re-processing sections with detected page spans...")
            sections_data = []
            for md_file in sections_path.glob('*.md'):
                section_data = process_section(md_file, page_mapping, page_spans)
                if section_data:
                    sections_data.append(section_data)
            
            # Regenerate PDF with correct page numbers in choices
            print("  Regenerating PDF with correct page numbers...")
            generate_pdf_via_pandoc(sections_data, pdf_file)
    else:
        print("  (Skipping PDF page span detection - PDF generation failed)")
    
    # Generate EPUB
    epub_file = os.path.join(output_dir, 'adventure.epub')
    generate_epub(sections_data, epub_file)
    
    print("\nCompilation complete!")

if __name__ == '__main__':
    import sys
    
    sections_dir = sys.argv[1] if len(sys.argv) > 1 else 'src/content/sections'
    mapping_file = sys.argv[2] if len(sys.argv) > 2 else 'page-mapping.json'
    output_dir = sys.argv[3] if len(sys.argv) > 3 else 'output'
    
    compile_book(sections_dir, mapping_file, output_dir)

