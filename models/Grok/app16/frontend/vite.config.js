import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 6011,
    strictPort: true,
    proxy: {
      '/api': {
        target: 'http://localhost:5511',
        changeOrigin: true,
        secure: false,
      }
    }
  }
})
