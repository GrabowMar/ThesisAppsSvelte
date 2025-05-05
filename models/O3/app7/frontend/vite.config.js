import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5653, // Frontend (Vite) will run on port 5653
    strictPort: true,
    proxy: {
      '/api': {
        target: 'http://localhost:6153', // Proxy API calls to backend on port 6153
        changeOrigin: true,
        secure: false,
      }
    }
  }
})
