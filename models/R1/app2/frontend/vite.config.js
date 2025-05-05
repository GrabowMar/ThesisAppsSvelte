import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 6063,
    strictPort: true,
    proxy: {
      '/socket.io': {
        target: 'http://localhost:5563',
        ws: true,
        changeOrigin: true
      }
    }
  }
})
