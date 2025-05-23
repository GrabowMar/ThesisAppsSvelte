import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5905,
    strictPort: true,
    proxy: {
      '/api': {
        target: 'http://localhost:5405', // Corrected target URL
        changeOrigin: true,
        secure: false,
      }
    }
  },
  build: {
    sourcemap: true, // Enable sourcemaps for debugging
  },
})
