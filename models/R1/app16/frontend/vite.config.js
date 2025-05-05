import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 6091,
    strictPort: true,
    proxy: {
      '/api': {
        target: 'http://localhost:5591',
        changeOrigin: true,
        secure: false,
      }
    }
  }
})
