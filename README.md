# Choose Your Own Christmas Adventure

A choose-your-own-adventure book system that compiles markdown story sections into HTML, PDF, and EPUB formats with randomized page numbering to prevent backtracking.

## Structure

- `sections/` - Individual markdown files for each story section/page
- `sources/` - Source EPUB files for reference and inspiration
- `scripts/` - Compilation and utility scripts
- `output/` - Generated HTML, PDF, and EPUB files
- `page-mapping.json` - Generated file mapping sections to random page numbers

## Quick Start

1. **Write your story sections** in `sections/` as markdown files with YAML frontmatter:
   ```yaml
   ---
   id: section-1
   title: "The Beginning"
   choices:
     - text: "Go left"
       target: section-2.md
     - text: "Go right"
       target: section-3.md
   ---
   Your story content here...
   ```

2. **Run the randomizer** to assign random page numbers:
   ```bash
   uv run python scripts/randomize.py
   # or
   node scripts/randomize.js
   ```

3. **Compile to all formats**:
   ```bash
   uv run python scripts/compile.py
   # or
   node scripts/compile.js
   ```

4. **Find your outputs** in the `output/` directory:
   - `adventure.html` - Web-readable version
   - `adventure.pdf` - Print-ready PDF
   - `adventure.epub` - E-reader format

## How It Works

### Randomization
The randomizer assigns random page numbers to each section, ensuring that the adventure isn't sequential and makes backtracking difficult. This mapping is saved in `page-mapping.json`.

### Compilation
The compilation script:
- Parses all markdown files with their frontmatter
- Resolves choice targets using the page mapping
- Replaces file references with "Turn to page X" instructions
- Generates HTML, PDF, and EPUB with proper formatting

### Section Format
Each section file should:
- Have a unique `id` in the frontmatter
- Include a `title` for the section
- List `choices` with `text` (what the reader sees) and `target` (the target markdown file)
- Contain the story content after the frontmatter

## Adding New Sections

1. Create a new markdown file in `sections/` (e.g., `section-5.md`)
2. Add YAML frontmatter with `id`, `title`, and `choices`
3. Write your story content
4. Reference this file in other sections' choices using the filename
5. Re-run the randomizer and compilation scripts

## Converting Source EPUBs to Markdown

If you have EPUB files in the `sources/` directory that you want to convert to Markdown for reference or inspiration, use the EPUB to Markdown converter:

```bash
# Convert all EPUB files in sources/ directory
uv run python scripts/epub_to_markdown.py

# Convert a specific EPUB file
uv run python scripts/epub_to_markdown.py sources/book.epub

# Convert to a specific output directory
uv run python scripts/epub_to_markdown.py -o output/markdown sources/book.epub
```

The converter will:
- Extract metadata (title, author, publisher, etc.) from the EPUB
- Convert all chapters to Markdown format
- Preserve formatting, links, and structure
- Save the output as a Markdown file with YAML frontmatter

The generated Markdown files can be used as reference material when creating your adventure sections.

## Requirements

- Python 3.8+ OR Node.js
- `uv` (Python package manager) or `pip` (alternative)
- `pandoc` (for PDF and EPUB generation)
- `pdflatex` (usually comes with pandoc or TeX distribution)

## Installation

```bash
# Install pandoc (macOS)
brew install pandoc

# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment and install Python dependencies
uv venv
source .venv/bin/activate  # On macOS/Linux
uv pip install -r requirements.txt

# Node.js dependencies
npm install
```

## Usage Examples

### Using Python

```bash
# Activate virtual environment (if not already activated)
source .venv/bin/activate

# Step 1: Randomize page numbers
python scripts/randomize.py

# Step 2: Compile to all formats
python scripts/compile.py
```

Or use `uv run` to automatically use the virtual environment:

```bash
# Step 1: Randomize page numbers
uv run python scripts/randomize.py

# Step 2: Compile to all formats
uv run python scripts/compile.py

# Convert EPUB sources to Markdown (optional)
uv run python scripts/epub_to_markdown.py
```

### Using Node.js

```bash
# Step 1: Randomize page numbers
node scripts/randomize.js
# or
npm run randomize

# Step 2: Compile to all formats
node scripts/compile.js
# or
npm run compile
```

## Example Section File

See `sections/section-1.md` for a complete example. Each section file should:

- Start with YAML frontmatter (between `---` markers)
- Include a unique `id` field
- Include a `title` field
- Optionally include a `choices` array (empty array `[]` for ending sections)
- Contain markdown content after the frontmatter

## Output Files

After compilation, you'll find in the `output/` directory:

- **adventure.html** - Single HTML file with all sections, styled for reading
- **adventure.pdf** - Print-ready PDF with page numbers and table of contents
- **adventure.epub** - E-reader compatible format

## Tips

- Run the randomizer each time you add new sections to get fresh page numbers
- The page mapping (`page-mapping.json`) is regenerated each time you run the randomizer
- Sections are sorted by page number in the output, not by filename
- Choice references automatically update to show "Turn to page X" based on the current mapping

