import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5711,  // Changed to match your frontend port
    strictPort: true,
    proxy: {
      '/api': {
        target: 'http://localhost:port: 5211',
        changeOrigin: true,
        secure: false,
      }
    }
  }
});