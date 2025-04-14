import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5789,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:5289',
        changeOrigin: true,
        secure: false,
      }
    }
  }
})
