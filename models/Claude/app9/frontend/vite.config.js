import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5837,
    strictPort: true,
    proxy: {
      '/api': {
        target: 'http://localhost:5337',
        changeOrigin: true,
        secure: false,
      }
    }
  }
})
