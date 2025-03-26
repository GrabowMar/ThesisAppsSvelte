import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5661,  // Changed to match your frontend port
    strictPort: true,
    proxy: {
      '/api': {
        target: 'http://localhost:port: 5161',
        changeOrigin: true,
        secure: false,
      }
    }
  }
});