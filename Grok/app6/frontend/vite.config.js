import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5491,
    strictPort: true,
    proxy: {
      '/api': {
        target: 'http://localhost:5991',
        changeOrigin: true,
        secure: false,
      }
    }
  }
})
