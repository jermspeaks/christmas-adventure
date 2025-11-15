import { defineConfig } from 'vite';
import preact from '@preact/preset-vite';
import fs from 'fs';
import path from 'path';

export default defineConfig({
  plugins: [
    preact(),
    {
      name: 'copy-game-data',
      buildStart() {
        // Copy game-data.json from output to public during build
        const source = path.join(process.cwd(), 'output', 'game-data.json');
        const dest = path.join(process.cwd(), 'public', 'game-data.json');
        if (fs.existsSync(source)) {
          if (!fs.existsSync(path.join(process.cwd(), 'public'))) {
            fs.mkdirSync(path.join(process.cwd(), 'public'), { recursive: true });
          }
          fs.copyFileSync(source, dest);
        }
      }
    }
  ],
  server: {
    host: true, // Allow access from local network
    port: 4100,
    open: true,
    fs: {
      // Allow serving files from output directory
      allow: ['..']
    }
  },
  publicDir: 'public',
  build: {
    outDir: 'output',
    emptyOutDir: false, // Don't delete existing PDF/EPUB files
    rollupOptions: {
      input: {
        main: './index.html'
      }
    }
  }
});

