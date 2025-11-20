#!/usr/bin/env node
/**
 * Development server for Choose Your Own Adventure book with Astro.
 * Watches for file changes, recompiles game-data.json, and serves with Astro.
 */

const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');
const chokidar = require('chokidar');

function compileGameData() {
  return new Promise((resolve, reject) => {
    const compileProcess = spawn('node', ['scripts/compile.js'], {
      stdio: 'inherit',
      shell: true,
      cwd: path.join(__dirname, '..')
    });

    compileProcess.on('close', (code) => {
      if (code === 0) {
        // Copy game-data.json to public directory
        const source = path.join(__dirname, '..', 'output', 'game-data.json');
        const dest = path.join(__dirname, '..', 'public', 'game-data.json');
        
        if (fs.existsSync(source)) {
          if (!fs.existsSync(path.dirname(dest))) {
            fs.mkdirSync(path.dirname(dest), { recursive: true });
          }
          fs.copyFileSync(source, dest);
          console.log(`[${new Date().toLocaleTimeString()}] Copied game-data.json to public/`);
        }
        resolve();
      } else {
        reject(new Error(`Compilation failed with code ${code}`));
      }
    });

    compileProcess.on('error', (err) => {
      reject(err);
    });
  });
}

// Get port from environment variable or use default
const PORT = process.env.PORT || 4100;

// Compile initially
console.log('Initial compilation...');
compileGameData()
  .then(() => {
    // Start Astro dev server
    console.log('Starting Astro dev server...');
    const server = spawn('npx', ['astro', 'dev', '--port', PORT.toString(), '--host'], {
      stdio: 'inherit',
      shell: true,
      cwd: path.join(__dirname, '..')
    });

    // Watch for changes in markdown files
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
        compileGameData().catch(err => {
          console.error('Compilation error:', err.message);
        });
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
  })
  .catch(err => {
    console.error('Error starting dev server:', err);
    process.exit(1);
  });

