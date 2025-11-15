#!/usr/bin/env node
/**
 * Compilation script for Choose Your Own Adventure book.
 * Generates HTML, PDF, and EPUB outputs with page numbers and choice references.
 */

const fs = require('fs');
const path = require('path');
const fm = require('front-matter');
const MarkdownIt = require('markdown-it');
const { execSync } = require('child_process');

const md = new MarkdownIt({
    html: true,
    linkify: true,
    typographer: true
});

function loadPageMapping(mappingFile = 'page-mapping.json') {
    if (!fs.existsSync(mappingFile)) {
        return null;
    }
    
    return JSON.parse(fs.readFileSync(mappingFile, 'utf-8'));
}

function ensurePageMapping() {
    const sectionsDir = path.join(__dirname, '..', 'sections');
    const mappingFile = path.join(__dirname, '..', 'page-mapping.json');
    
    // Check if sections directory exists
    if (!fs.existsSync(sectionsDir)) {
        console.error(`Error: ${sectionsDir} directory not found!`);
        return false;
    }
    
    // Check if mapping exists
    if (!fs.existsSync(mappingFile)) {
        console.log('Page mapping not found. Generating...');
        regeneratePageMapping();
        return true;
    }
    
    // Check if all sections are in the mapping
    const mapping = loadPageMapping(mappingFile);
    if (!mapping || !mapping.sections) {
        console.log('Page mapping is invalid. Regenerating...');
        regeneratePageMapping();
        return true;
    }
    
    const files = fs.readdirSync(sectionsDir);
    const mdFiles = files.filter(f => f.endsWith('.md'));
    
    let needsRegeneration = false;
    for (const mdFile of mdFiles) {
        const filePath = path.join(sectionsDir, mdFile);
        try {
            const content = fs.readFileSync(filePath, 'utf-8');
            const parsed = fm(content);
            const frontmatter = parsed.attributes;
            
            if (frontmatter && frontmatter.id) {
                if (!mapping.sections[frontmatter.id]) {
                    needsRegeneration = true;
                    break;
                }
            }
        } catch (error) {
            // Skip files that can't be parsed
            continue;
        }
    }
    
    if (needsRegeneration) {
        console.log('New sections detected. Regenerating page mapping...');
        regeneratePageMapping();
        return true;
    }
    
    return true;
}

function regeneratePageMapping() {
    try {
        execSync('node scripts/randomize.js', { 
            stdio: 'inherit',
            cwd: path.join(__dirname, '..')
        });
        console.log('Page mapping regenerated successfully.');
    } catch (error) {
        console.error('Error regenerating page mapping:', error.message);
        throw error;
    }
}

function resolveChoiceTarget(targetFile, pageMapping) {
    const targetId = targetFile.replace('.md', '');
    if (pageMapping.sections[targetId]) {
        return pageMapping.sections[targetId].page;
    }
    return null;
}

function processSection(mdFile, pageMapping) {
    const content = fs.readFileSync(mdFile, 'utf-8');
    const parsed = fm(content);
    const frontmatter = parsed.attributes;
    
    if (!frontmatter || !frontmatter.id) {
        return null;
    }
    
    const sectionId = frontmatter.id;
    const pageInfo = pageMapping.sections[sectionId];
    
    if (!pageInfo) {
        return null;
    }
    
    const pageNum = pageInfo.page;
    const title = frontmatter.title || 'Untitled';
    const body = parsed.body.trim();
    
    // Process choices and extract target section IDs
    const choices = [];
    if (frontmatter.choices && Array.isArray(frontmatter.choices)) {
        for (const choice of frontmatter.choices) {
            const choiceText = choice.text || '';
            const targetFile = choice.target || '';
            // Extract section ID from filename (e.g., "section-2.md" -> "section-2")
            const targetSectionId = targetFile.replace('.md', '');
            choices.push({
                text: choiceText,
                target: targetSectionId
            });
        }
    }
    
    // For PDF/EPUB: Process choices and replace targets with page numbers
    let choicesMarkdown = '';
    if (choices.length > 0) {
        choicesMarkdown = '\n\n## Your Choices:\n\n';
        for (const choice of choices) {
            const targetPage = resolveChoiceTarget(choice.target + '.md', pageMapping);
            if (targetPage) {
                choicesMarkdown += `- **${choice.text}** → Turn to page ${targetPage}\n`;
            } else {
                choicesMarkdown += `- **${choice.text}** → (Invalid target: ${choice.target})\n`;
            }
        }
    }
    
    // Combine title, page number, body, and choices
    const fullContent = `# ${title}\n\n**Page ${pageNum}**\n\n${body}${choicesMarkdown}`;
    
    return {
        id: sectionId,
        page: pageNum,
        title: title,
        body: body,
        choices: choices,
        content: fullContent,
        html: md.render(fullContent)
    };
}

function generateHTML(sectionsData, outputFile = 'output/adventure.html') {
    const outputDir = path.dirname(outputFile);
    if (!fs.existsSync(outputDir)) {
        fs.mkdirSync(outputDir, { recursive: true });
    }
    
    // Prepare game data: map section ID to section data
    const gameData = {};
    for (const section of sectionsData) {
        gameData[section.id] = {
            id: section.id,
            title: section.title,
            body: section.body,
            bodyHtml: md.render(section.body),
            choices: section.choices || []
        };
    }
    
    // Find starting section (section-1 or first section)
    const startingSectionId = gameData['section-1'] ? 'section-1' : sectionsData[0].id;
    
    // Embed game data as JSON
    const gameDataJson = JSON.stringify(gameData, null, 2);
    
    let htmlContent = `<!DOCTYPE html>
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
        const gameData = ${gameDataJson};
        const STARTING_SECTION = '${startingSectionId}';
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
</html>`;
    
    fs.writeFileSync(outputFile, htmlContent, 'utf-8');
    console.log(`HTML generated: ${outputFile}`);
}

function generateGameDataJSON(sectionsData, outputFile = 'output/game-data.json') {
    const outputDir = path.dirname(outputFile);
    if (!fs.existsSync(outputDir)) {
        fs.mkdirSync(outputDir, { recursive: true });
    }
    
    // Prepare game data: map section ID to section data
    const gameData = {};
    for (const section of sectionsData) {
        gameData[section.id] = {
            id: section.id,
            title: section.title,
            body: section.body,
            bodyHtml: md.render(section.body),
            choices: section.choices || []
        };
    }
    
    // Find starting section (section-1 or first section)
    const startingSectionId = gameData['section-1'] ? 'section-1' : sectionsData[0].id;
    
    const gameDataOutput = {
        gameData: gameData,
        startingSection: startingSectionId
    };
    
    fs.writeFileSync(outputFile, JSON.stringify(gameDataOutput, null, 2), 'utf-8');
    console.log(`Game data JSON generated: ${outputFile}`);
}

function generatePDFViaPandoc(htmlFile = 'output/adventure.html', outputFile = 'output/adventure.pdf') {
    try {
        const cmd = [
            'pandoc',
            htmlFile,
            '-o', outputFile,
            '--pdf-engine=pdflatex',
            '-V', 'geometry:margin=1in',
            '-V', 'fontsize=11pt',
            '--toc'
        ].join(' ');
        
        execSync(cmd, { stdio: 'inherit' });
        console.log(`PDF generated: ${outputFile}`);
    } catch (error) {
        console.error('Error generating PDF:', error.message);
        console.log('Make sure pandoc and pdflatex are installed');
    }
}

function generateEPUB(sectionsData, outputFile = 'output/adventure.epub') {
    const outputDir = path.dirname(outputFile);
    if (!fs.existsSync(outputDir)) {
        fs.mkdirSync(outputDir, { recursive: true });
    }
    
    // Create a temporary markdown file with all sections
    const sortedSections = sectionsData.sort((a, b) => a.page - b.page);
    const tempDir = path.join(__dirname, '..', '.tmp');
    if (!fs.existsSync(tempDir)) {
        fs.mkdirSync(tempDir, { recursive: true });
    }
    
    const tempMd = path.join(tempDir, 'adventure-temp.md');
    let mdContent = '# Choose Your Own Christmas Adventure\n\n';
    mdContent += `*Generated on ${new Date().toISOString().split('T')[0]}*\n\n`;
    
    for (const section of sortedSections) {
        mdContent += `\n\n---\n\n${section.content}\n\n`;
    }
    
    fs.writeFileSync(tempMd, mdContent, 'utf-8');
    
    try {
        const cmd = [
            'pandoc',
            tempMd,
            '-o', outputFile,
            '--toc'
        ];
        
        if (fs.existsSync(path.join(__dirname, '..', 'cover.jpg'))) {
            cmd.push('--epub-cover-image=cover.jpg');
        }
        
        execSync(cmd.join(' '), { stdio: 'inherit', cwd: path.join(__dirname, '..') });
        console.log(`EPUB generated: ${outputFile}`);
        
        // Clean up temp file
        fs.unlinkSync(tempMd);
    } catch (error) {
        console.error('Error generating EPUB:', error.message);
        console.log('Make sure pandoc is installed');
    }
}

function compileBook(sectionsDir = 'sections', mappingFile = 'page-mapping.json', outputDir = 'output') {
    // Ensure page mapping is up to date before compiling
    ensurePageMapping();
    
    console.log('Loading page mapping...');
    const pageMapping = loadPageMapping(mappingFile);
    if (!pageMapping) {
        console.error('Error: Could not load page mapping after regeneration.');
        return;
    }
    
    console.log('Processing sections...');
    const sectionsPath = path.join(__dirname, '..', sectionsDir);
    const sectionsData = [];
    
    if (!fs.existsSync(sectionsPath)) {
        console.error(`Error: ${sectionsPath} directory not found!`);
        return;
    }
    
    const files = fs.readdirSync(sectionsPath);
    const mdFiles = files.filter(f => f.endsWith('.md'));
    
    for (const mdFile of mdFiles) {
        const filePath = path.join(sectionsPath, mdFile);
        const sectionData = processSection(filePath, pageMapping);
        if (sectionData) {
            sectionsData.push(sectionData);
            console.log(`  Processed: ${sectionData.id} (Page ${sectionData.page})`);
        }
    }
    
    if (sectionsData.length === 0) {
        console.log('No sections found to compile!');
        return;
    }
    
    console.log(`\nCompiling ${sectionsData.length} sections...`);
    
    const outputPath = path.join(__dirname, '..', outputDir);
    
    // Generate HTML (for PDF/EPUB generation)
    const htmlFile = path.join(outputPath, 'adventure.html');
    generateHTML(sectionsData, htmlFile);
    
    // Generate game data JSON (for Preact app)
    const gameDataFile = path.join(outputPath, 'game-data.json');
    generateGameDataJSON(sectionsData, gameDataFile);
    
    // Also copy JSON to public directory for Vite to serve
    const publicDir = path.join(__dirname, '..', 'public');
    if (!fs.existsSync(publicDir)) {
        fs.mkdirSync(publicDir, { recursive: true });
    }
    const publicJsonFile = path.join(publicDir, 'game-data.json');
    fs.copyFileSync(gameDataFile, publicJsonFile);
    
    // Generate PDF
    const pdfFile = path.join(outputPath, 'adventure.pdf');
    generatePDFViaPandoc(htmlFile, pdfFile);
    
    // Generate EPUB
    const epubFile = path.join(outputPath, 'adventure.epub');
    generateEPUB(sectionsData, epubFile);
    
    console.log('\nCompilation complete!');
}

// Main execution
const sectionsDir = process.argv[2] || 'sections';
const mappingFile = process.argv[3] || 'page-mapping.json';
const outputDir = process.argv[4] || 'output';

compileBook(sectionsDir, mappingFile, outputDir);

