// app/frontend/vite.config.js
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 6155,
    strictPort: true,
    proxy: {
      '/api': {
        target: 'http://localhost:5655',
        changeOrigin: true,
        secure: false,
      }
    }
  }
})
