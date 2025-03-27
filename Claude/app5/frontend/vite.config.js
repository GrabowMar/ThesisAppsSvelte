import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5829,
    strictPort: true,
    proxy: {
      '/api': {
        target: 'http://localhost:5329',
        changeOrigin: true,
        secure: false,
      }
    }
  }
})
