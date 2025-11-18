# Choose Your Own Christmas Adventure

A choose-your-own-adventure book system that compiles markdown story sections into HTML, PDF, and EPUB formats with randomized page numbering to prevent backtracking.

## Structure

- `sections/` - Individual markdown files for each story section/page
- `sources/` - Source EPUB files for reference and inspiration
- `scripts/` - Compilation and utility scripts
- `src/` - Preact application source code
  - `src/components/` - React components (Header, Section, ChoiceButton)
  - `src/App.jsx` - Main application component
  - `src/main.jsx` - Application entry point
  - `src/styles.css` - Application styles
- `public/` - Static assets (generated game data JSON)
- `output/` - Generated HTML, PDF, EPUB, and built application files
- `page-mapping.json` - Generated file mapping sections to random page numbers
- `UNFINISHED_BRANCHES.md` - Documentation of choices pointing to non-existent sections
- `DUPLICATE_CHOICES.md` - Documentation of sections with multiple choices leading to the same destination
- `CHARACTERS.md` - Reference guide listing all named characters in the story

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

3. **Start the development server** (recommended for development):
   ```bash
   npm run dev
   ```
   This will:
   - Compile your markdown sections to JSON
   - Start a Vite dev server on http://localhost:4100
   - Watch for changes and automatically recompile
   - Provide hot module replacement for instant updates

4. **Or compile to all formats** (for production):
   ```bash
   npm run compile
   # or
   npm run build  # Compiles and builds the Preact app
   ```

5. **Find your outputs** in the `output/` directory:
   - `adventure.html` - Legacy web-readable version (vanilla JS)
   - `game-data.json` - Game data for the Preact application
   - Built Preact app files (after running `npm run build`)
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
- Generates `game-data.json` for the Preact application

### Frontend Application
The web version uses **Preact** (a lightweight React alternative) with **Vite** for:
- Fast development with hot module replacement
- Component-based architecture for maintainability
- Small bundle size (~3KB for Preact vs ~40KB for React)
- Modern development experience

### UI Features

The web application provides three main views accessible through the header navigation:

#### Game View (Main Play Mode)

- **Story Display**: Shows the current section's title and content with formatted markdown
- **Choice Buttons**: Interactive buttons for each available choice that navigate to the next section
- **Ending Detection**: Automatically displays "The End" for sections with no choices
- **Auto-scroll**: Automatically scrolls to the top when navigating to a new section
- **Start Over Button**: Resets the adventure to the beginning (section-1)

#### Visualization/Map View

- **Interactive Graph**: Visual representation of all story sections as nodes in a graph
- **Connection Lines**: Shows arrows connecting sections based on choices, making it easy to see story paths
- **Section Details**: Each node displays the section title and lists all available choices with their targets
- **Automatic Layout**: Uses dagre graph layout algorithm to automatically arrange sections in a readable hierarchy
- **Terminal Endings**: Clearly marked sections that have no outgoing choices
- **Navigation**: Click "View Map" from the game view to see the complete story structure

#### Branches View

- **Complete Paths**: Lists all possible story paths from the starting section to terminal endings
- **Expandable Branches**: Each complete branch can be expanded or collapsed
- **Section Details**: Within each branch, individual sections can be expanded to view:
  - Section title and content
  - The choice that led to this section (if not the starting section)
  - All available choices from this section
  - Section file reference
- **Bulk Actions**: "Expand All" / "Collapse All" button for each branch to quickly view or hide all sections
- **Path Statistics**: Shows the number of sections in each branch and where it ends
- **Continuity Review**: Perfect for reviewing story continuity and ensuring all paths make narrative sense

#### Navigation

- **Hash-based Routing**: Uses URL hash fragments (`#/`, `#/visualization`, `#/branches`) for navigation
- **Header Navigation**: Consistent header with navigation buttons available in all views
- **View Switching**: Easy switching between game, map, and branches views without losing your place

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

## Tracking Story Progress

### Unfinished Branches

The `UNFINISHED_BRANCHES.md` file helps you identify where your story needs more content. It automatically documents all choices from existing sections that point to non-existent target files.

**How to use it:**

1. **Check for unfinished branches**: Open `UNFINISHED_BRANCHES.md` to see which sections have choices pointing to missing files
2. **Create missing sections**: Use the file to identify which section files need to be created next
3. **Track your progress**: As you create new sections, the unfinished branches will decrease
4. **Regenerate the file**: After creating new sections, you can regenerate `UNFINISHED_BRANCHES.md` by running a Python script that scans all section files and identifies missing targets. The script parses YAML frontmatter from each section file and checks which choice targets don't exist yet.

**How to generate it:**

```bash
# If a script exists for generating UNFINISHED_BRANCHES.md, run it:
# uv run python scripts/generate_unfinished_branches.py
# or check the scripts/ directory for analysis tools
```

**Note:** The specific script name may vary. Look for analysis scripts in the `scripts/` directory that scan section files for missing choice targets.

The file shows:
- Each section with unfinished branches
- The specific choices that point to missing files
- A list of all missing target files
- Summary statistics

This makes it easy to see where to direct your storytelling efforts next and ensures no story branches are left hanging.

### Duplicate Choices

The `DUPLICATE_CHOICES.md` file documents sections where multiple choices lead to the same destination. This can help you identify opportunities to create more branching paths in your story.

**How to generate it:**

```bash
# Generate DUPLICATE_CHOICES.md using the analysis script
uv run python scripts/analyze_choices.py sections DUPLICATE_CHOICES.md
# or
python scripts/analyze_choices.py sections DUPLICATE_CHOICES.md
```

The script analyzes all section files and identifies cases where multiple choices in the same section point to the same destination file.

### Characters

The `CHARACTERS.md` file provides a comprehensive reference of all named characters in the story (excluding the second-person protagonist "you"). It includes:
- Character descriptions and traits
- The section where each character first appears
- A complete list of all sections where each character appears

This file helps maintain character consistency throughout the story and makes it easy to track character appearances and development.

**Note:** This file may be manually maintained or generated by analysis scripts. Check for character analysis scripts in the `scripts/` directory.

## Generating Documentation Files

The following documentation files help track story progress and maintain consistency:

- **`UNFINISHED_BRANCHES.md`** - Lists all choices pointing to non-existent sections (see [Unfinished Branches](#unfinished-branches) above)
- **`DUPLICATE_CHOICES.md`** - Documents sections with multiple choices leading to the same destination (see [Duplicate Choices](#duplicate-choices) above)
- **`CHARACTERS.md`** - Reference guide for all named characters in the story (see [Characters](#characters) above)

These files are typically generated by analysis scripts that scan all section files. Regenerate them periodically as you add new sections to keep them up to date.

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

- **Node.js** 16+ (required for Preact/Vite frontend)
- Python 3.8+ (optional, for Python scripts)
- `uv` (Python package manager) or `pip` (alternative, if using Python)
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

# Node.js dependencies (required)
npm install
```

## Development Workflow

1. **Start the dev server**:
   ```bash
   npm run dev
   ```
   This will:
   - Compile markdown sections to `game-data.json`
   - Start Vite dev server on http://localhost:4100
   - Open your browser automatically
   - Watch for changes in `sections/` and `page-mapping.json`
   - Automatically recompile when files change
   - Provide hot module replacement for instant UI updates

2. **Edit your story sections** in `sections/*.md`

3. **If you add new sections**, re-run the randomizer:
   ```bash
   npm run randomize
   ```
   The dev server will automatically detect the change and recompile.

4. **Build for production**:
   ```bash
   npm run build
   ```
   This creates an optimized production build in the `output/` directory.

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
npm run randomize
# or
node scripts/randomize.js

# Step 2: Development (with hot reload)
npm run dev
# This compiles markdown to JSON and starts Vite dev server on port 4100
# The server watches for changes and automatically recompiles

# Step 3: Build for production
npm run build
# This compiles markdown and builds the optimized Preact application

# Or compile to all formats (HTML, PDF, EPUB)
npm run compile
# or
node scripts/compile.js

# Preview production build
npm run preview
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

- **adventure.html** - Legacy single HTML file with all sections (vanilla JS version)
- **game-data.json** - Game data in JSON format for the Preact application
- **adventure.pdf** - Print-ready PDF with page numbers and table of contents
- **adventure.epub** - E-reader compatible format
- Built Preact application files (after running `npm run build`)

The `public/` directory contains:
- **game-data.json** - Copy of game data served by Vite during development

## Tips

- **Development**: Use `npm run dev` for the best development experience with hot reload
- Run the randomizer each time you add new sections to get fresh page numbers
- The page mapping (`page-mapping.json`) is regenerated each time you run the randomizer
- Sections are sorted by page number in the output, not by filename
- Choice references automatically update to show "Turn to page X" based on the current mapping
- The dev server watches for changes and recompiles automatically - no need to restart
- The Preact app loads game data from `/game-data.json` at runtime
- Both `output/game-data.json` and `public/game-data.json` are generated (public/ is for Vite to serve during dev)

