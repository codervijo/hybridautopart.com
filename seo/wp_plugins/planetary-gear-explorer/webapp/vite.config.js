import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  build: {
    outDir: '../plugin/dist',
    emptyOutDir: true,
    rollupOptions: {
      output: {
        entryFileNames: 'pgx.js',
        chunkFileNames: 'pgx-[name].js',
        assetFileNames: 'pgx[extname]',
      },
    },
  },
  base: './',
  server: {
    port: 5174,
    host: true,
  },
})
