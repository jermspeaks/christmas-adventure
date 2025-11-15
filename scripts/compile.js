#!/usr/bin/env node
/**
 * Compilation script for Choose Your Own Adventure book.
 * Generates HTML, PDF, and EPUB outputs with page numbers and choice references.
 */

const fs = require('fs');
const path = require('path');
const matter = require('gray-matter');
const MarkdownIt = require('markdown-it');
const { execSync } = require('child_process');

const md = new MarkdownIt({
    html: true,
    linkify: true,
    typographer: true
});

function loadPageMapping(mappingFile = 'page-mapping.json') {
    if (!fs.existsSync(mappingFile)) {
        throw new Error(`Page mapping file not found: ${mappingFile}. Run randomize.js first!`);
    }
    
    return JSON.parse(fs.readFileSync(mappingFile, 'utf-8'));
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
    const parsed = matter(content);
    const frontmatter = parsed.data;
    
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
    const body = parsed.content.trim();
    
    // Process choices and replace targets with page numbers
    let choicesMarkdown = '';
    if (frontmatter.choices && Array.isArray(frontmatter.choices)) {
        choicesMarkdown = '\n\n## Your Choices:\n\n';
        for (const choice of frontmatter.choices) {
            const choiceText = choice.text || '';
            const targetFile = choice.target || '';
            const targetPage = resolveChoiceTarget(targetFile, pageMapping);
            
            if (targetPage) {
                choicesMarkdown += `- **${choiceText}** → Turn to page ${targetPage}\n`;
            } else {
                choicesMarkdown += `- **${choiceText}** → (Invalid target: ${targetFile})\n`;
            }
        }
    }
    
    // Combine title, page number, body, and choices
    const fullContent = `# ${title}\n\n**Page ${pageNum}**\n\n${body}${choicesMarkdown}`;
    
    return {
        id: sectionId,
        page: pageNum,
        title: title,
        content: fullContent,
        html: md.render(fullContent)
    };
}

function generateHTML(sectionsData, outputFile = 'output/adventure.html') {
    const outputDir = path.dirname(outputFile);
    if (!fs.existsSync(outputDir)) {
        fs.mkdirSync(outputDir, { recursive: true });
    }
    
    // Sort sections by page number
    const sortedSections = sectionsData.sort((a, b) => a.page - b.page);
    
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
        }
        .section {
            page-break-after: always;
            background: white;
            padding: 40px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        h1 {
            color: #c41e3a;
            border-bottom: 3px solid #c41e3a;
            padding-bottom: 10px;
        }
        h2 {
            color: #2d5016;
            margin-top: 30px;
        }
        ul {
            list-style-type: none;
            padding-left: 0;
        }
        li {
            margin: 10px 0;
            padding: 10px;
            background-color: #f0f0f0;
            border-left: 4px solid #c41e3a;
        }
        @media print {
            .section {
                page-break-after: always;
                box-shadow: none;
                margin: 0;
            }
        }
    </style>
</head>
<body>
`;
    
    for (const section of sortedSections) {
        htmlContent += `<div class="section">\n${section.html}\n</div>\n\n`;
    }
    
    htmlContent += `</body>
</html>`;
    
    fs.writeFileSync(outputFile, htmlContent, 'utf-8');
    console.log(`HTML generated: ${outputFile}`);
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
    console.log('Loading page mapping...');
    const pageMapping = loadPageMapping(mappingFile);
    
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
    
    // Generate HTML
    const htmlFile = path.join(outputPath, 'adventure.html');
    generateHTML(sectionsData, htmlFile);
    
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

