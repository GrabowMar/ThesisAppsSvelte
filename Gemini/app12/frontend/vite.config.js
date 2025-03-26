import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5923,  // Changed to match your frontend port
    strictPort: true,
    proxy: {
      '/api': {
        target: 'http://localhost:port: 5423',
        changeOrigin: true,
        secure: false,
      }
    }
  }
});