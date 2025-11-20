import { defineConfig } from 'astro/config';
import preact from '@astrojs/preact';

// https://astro.build/config
export default defineConfig({
  integrations: [preact()],
  output: 'static',
  build: {
    outDir: 'dist'
  },
  server: {
    port: 4100,
    host: true
  },
  publicDir: 'public'
});

