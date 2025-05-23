import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5953,  // Changed to match your frontend port
    strictPort: true,
    proxy: {
      '/api': {
        target: 'http://localhost:port: 5453',
        changeOrigin: true,
        secure: false,
      }
    }
  }
});