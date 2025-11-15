#!/usr/bin/env node
/**
 * Development server for Choose Your Own Adventure book.
 * Watches for file changes, recompiles HTML, and serves on localhost.
 */

const fs = require('fs');
const path = require('path');
const { spawn, execSync } = require('child_process');
const chokidar = require('chokidar');
const fm = require('front-matter');
const MarkdownIt = require('markdown-it');

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
    let body = parsed.body.trim();
    
    // Remove the first heading from body if it matches the title (to avoid duplicate titles)
    // Check if body starts with a heading that matches the title
    const escapedTitle = title.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    // Match heading with any number of #, optional quotes around title, and any trailing whitespace/newlines
    const titleHeadingRegex = new RegExp(`^#+\\s+["']?${escapedTitle}["']?\\s*\\n+`, 'i');
    if (titleHeadingRegex.test(body)) {
        body = body.replace(titleHeadingRegex, '').trim();
    }
    
    const choices = [];
    if (frontmatter.choices && Array.isArray(frontmatter.choices)) {
        for (const choice of frontmatter.choices) {
            const choiceText = choice.text || '';
            const targetFile = choice.target || '';
            const targetSectionId = targetFile.replace('.md', '');
            choices.push({
                text: choiceText,
                target: targetSectionId
            });
        }
    }
    
    return {
        id: sectionId,
        page: pageNum,
        title: title,
        body: body,
        choices: choices
    };
}

function generateHTML(sectionsData, outputFile = 'output/adventure.html') {
    const outputDir = path.dirname(outputFile);
    if (!fs.existsSync(outputDir)) {
        fs.mkdirSync(outputDir, { recursive: true });
    }
    
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
    
    const startingSectionId = gameData['section-1'] ? 'section-1' : sectionsData[0].id;
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
    console.log(`[${new Date().toLocaleTimeString()}] HTML compiled: ${outputFile}`);
}

function generateGameDataJSON(sectionsData, outputFile = 'output/game-data.json') {
    const outputDir = path.dirname(outputFile);
    if (!fs.existsSync(outputDir)) {
        fs.mkdirSync(outputDir, { recursive: true });
    }
    
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
    
    const startingSectionId = gameData['section-1'] ? 'section-1' : sectionsData[0].id;
    
    const gameDataOutput = {
        gameData: gameData,
        startingSection: startingSectionId
    };
    
    fs.writeFileSync(outputFile, JSON.stringify(gameDataOutput, null, 2), 'utf-8');
    console.log(`[${new Date().toLocaleTimeString()}] Game data JSON compiled: ${outputFile}`);
}

function compileHTMLOnly() {
    try {
        // Ensure page mapping is up to date before compiling
        ensurePageMapping();
        
        const sectionsDir = path.join(__dirname, '..', 'sections');
        const mappingFile = path.join(__dirname, '..', 'page-mapping.json');
        const htmlFile = path.join(__dirname, '..', 'output', 'adventure.html');
        const jsonFile = path.join(__dirname, '..', 'output', 'game-data.json');
        
        if (!fs.existsSync(sectionsDir)) {
            console.error(`Error: ${sectionsDir} directory not found!`);
            return;
        }
        
        const pageMapping = loadPageMapping(mappingFile);
        if (!pageMapping) {
            console.error('Error: Could not load page mapping after regeneration.');
            return;
        }
        const sectionsData = [];
        
        const files = fs.readdirSync(sectionsDir);
        const mdFiles = files.filter(f => f.endsWith('.md'));
        
        for (const mdFile of mdFiles) {
            const filePath = path.join(sectionsDir, mdFile);
            const sectionData = processSection(filePath, pageMapping);
            if (sectionData) {
                sectionsData.push(sectionData);
            }
        }
        
        if (sectionsData.length === 0) {
            console.log('No sections found to compile!');
            return;
        }
        
        // Generate both HTML (for backward compatibility) and JSON (for Preact app)
        generateHTML(sectionsData, htmlFile);
        generateGameDataJSON(sectionsData, jsonFile);
        
        // Also copy JSON to public directory for Vite to serve
        const publicDir = path.join(__dirname, '..', 'public');
        if (!fs.existsSync(publicDir)) {
            fs.mkdirSync(publicDir, { recursive: true });
        }
        const publicJsonFile = path.join(publicDir, 'game-data.json');
        fs.copyFileSync(jsonFile, publicJsonFile);
    } catch (error) {
        console.error('Compilation error:', error.message);
    }
}

// Get port from environment variable or use default
const PORT = process.env.PORT || 4100;

// Compile initially
console.log('Initial compilation...');
compileHTMLOnly();

// Start Vite dev server
const server = spawn('npx', ['vite', '--port', PORT.toString()], {
    stdio: 'inherit',
    shell: true
});

// Watch for changes
const watcher = chokidar.watch([
    path.join(__dirname, '..', 'sections', '**/*.md'),
    path.join(__dirname, '..', 'page-mapping.json')
], {
    ignored: /(^|[\/\\])\../, // ignore dotfiles
    persistent: true
});

let compileTimeout;
watcher.on('change', (filePath) => {
    console.log(`\n[${new Date().toLocaleTimeString()}] File changed: ${path.relative(process.cwd(), filePath)}`);
    
    // Debounce compilation
    clearTimeout(compileTimeout);
    compileTimeout = setTimeout(() => {
        compileHTMLOnly();
    }, 300);
});

watcher.on('error', error => {
    console.error('Watcher error:', error);
});

// Handle cleanup
process.on('SIGINT', () => {
    console.log('\nShutting down dev server...');
    watcher.close();
    server.kill();
    process.exit(0);
});

console.log(`\nDev server running at http://localhost:${PORT}`);
console.log('Watching for changes in sections/ and page-mapping.json...');
console.log('Press Ctrl+C to stop\n');

