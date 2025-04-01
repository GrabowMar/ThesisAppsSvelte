import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 6087,
    strictPort: true,
    proxy: {
      '/api': {
        target: 'http://localhost:5587',
        changeOrigin: true,
        secure: false,
      }
    }
  }
})
