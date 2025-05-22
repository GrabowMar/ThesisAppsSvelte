import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5501, // Replace with XXXX when needed
    strictPort: true,
    proxy: {
      '/api': {
        target: 'http://localhost:5001', // Replace with YYYY when needed
        changeOrigin: true,
        secure: false,
      }
    }
  }
});
