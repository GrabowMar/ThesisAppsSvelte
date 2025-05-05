import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 6009,
    strictPort: true,
    proxy: {
      '/api': {
        target: 'http://localhost:5509',
        changeOrigin: true,
        secure: false,
      }
    }
  }
})
