import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5659,          // Frontend port per requirements.
    strictPort: true,
    proxy: {
      '/api': {
        target: 'http://localhost:6159',  // Proxy calls to backend running on port 6159.
        changeOrigin: true,
        secure: false,
      }
    }
  },
})
