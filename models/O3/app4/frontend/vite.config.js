import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5647,  // Frontend port as requested
    strictPort: true,
    proxy: {
      '/api': {
        target: 'http://localhost:6147', // Proxy to Flask backend on port 6147
        changeOrigin: true,
        secure: false
      }
    }
  }
})
