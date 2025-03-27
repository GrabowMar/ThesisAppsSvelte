import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5927,
    strictPort: true,
    proxy: {
      '/api': {
        target: 'http://localhost:5427', // backend address
        changeOrigin: true,
        secure: false,
      }
    }
  }
})
