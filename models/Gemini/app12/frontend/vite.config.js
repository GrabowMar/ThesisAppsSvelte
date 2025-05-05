import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5923,
    strictPort: true,
    proxy: {
      '/api': {
        target: 'http://localhost:5423',
        changeOrigin: true,
        secure: false,
      }
    }
  }
})
