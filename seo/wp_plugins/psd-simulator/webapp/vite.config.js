import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  build: {
    outDir: '../plugin/dist',
    emptyOutDir: true,
    rollupOptions: {
      output: {
        entryFileNames: 'psd-simulator.js',
        chunkFileNames: 'psd-simulator-[name].js',
        assetFileNames: 'psd-simulator[extname]',
      },
    },
  },
  base: './',
  server: {
    port: 5173,
    host: true,
  },
})
