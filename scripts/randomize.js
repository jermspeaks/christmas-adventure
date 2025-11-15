#!/usr/bin/env node
/**
 * Randomizer script for Choose Your Own Adventure book.
 * Assigns random page numbers to each section to prevent sequential backtracking.
 */

const fs = require('fs');
const path = require('path');
const fm = require('front-matter');

function scanSections(sectionsDir) {
    const sections = {};
    
    if (!fs.existsSync(sectionsDir)) {
        console.error(`Error: ${sectionsDir} directory not found!`);
        return sections;
    }
    
    const files = fs.readdirSync(sectionsDir);
    const mdFiles = files.filter(f => f.endsWith('.md'));
    
    for (const mdFile of mdFiles) {
        const filePath = path.join(sectionsDir, mdFile);
        const content = fs.readFileSync(filePath, 'utf-8');
        
        try {
            const parsed = fm(content);
            const frontmatter = parsed.attributes;
            
            if (frontmatter && frontmatter.id) {
                sections[frontmatter.id] = {
                    filename: mdFile,
                    frontmatter: frontmatter,
                    targets: []
                };
                
                // Extract all targets from choices
                if (frontmatter.choices && Array.isArray(frontmatter.choices)) {
                    for (const choice of frontmatter.choices) {
                        if (choice.target) {
                            // Extract section ID from target filename
                            const targetId = choice.target.replace('.md', '');
                            sections[frontmatter.id].targets.push(targetId);
                        }
                    }
                }
            }
        } catch (error) {
            console.warn(`Warning: Could not parse ${mdFile}: ${error.message}`);
        }
    }
    
    return sections;
}

function assignRandomPages(sections, startPage = 1) {
    const sectionIds = Object.keys(sections);
    
    // Shuffle array using Fisher-Yates algorithm
    for (let i = sectionIds.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [sectionIds[i], sectionIds[j]] = [sectionIds[j], sectionIds[i]];
    }
    
    const pageMapping = {};
    sectionIds.forEach((sectionId, index) => {
        const page = startPage + index;
        pageMapping[sectionId] = {
            page: page,
            filename: sections[sectionId].filename,
            title: sections[sectionId].frontmatter.title || 'Untitled',
            targets: sections[sectionId].targets
        };
    });
    
    return pageMapping;
}

function createPageMapping(sectionsDir = 'sections', outputFile = 'page-mapping.json', startPage = 1) {
    console.log('Scanning sections...');
    const sections = scanSections(sectionsDir);
    
    if (Object.keys(sections).length === 0) {
        console.log('No sections found!');
        return;
    }
    
    console.log(`Found ${Object.keys(sections).length} sections`);
    
    console.log('Assigning random page numbers...');
    const pageMapping = assignRandomPages(sections, startPage);
    
    // Add reverse mapping (page number -> section ID) for easier lookup
    const reverseMapping = {};
    for (const [sectionId, info] of Object.entries(pageMapping)) {
        reverseMapping[info.page] = sectionId;
    }
    
    const outputData = {
        sections: pageMapping,
        page_to_section: reverseMapping,
        total_pages: Object.keys(pageMapping).length
    };
    
    fs.writeFileSync(outputFile, JSON.stringify(outputData, null, 2), 'utf-8');
    
    console.log(`Page mapping created: ${outputFile}`);
    console.log(`Total pages: ${Object.keys(pageMapping).length}`);
    console.log('\nPage assignments:');
    
    const sortedEntries = Object.entries(pageMapping)
        .sort((a, b) => a[1].page - b[1].page);
    
    for (const [sectionId, info] of sortedEntries) {
        console.log(`  Page ${String(info.page).padStart(3)}: ${sectionId} - ${info.title}`);
    }
}

// Main execution
const sectionsDir = process.argv[2] || 'sections';
const outputFile = process.argv[3] || 'page-mapping.json';
const startPage = parseInt(process.argv[4]) || 1;

createPageMapping(sectionsDir, outputFile, startPage);

