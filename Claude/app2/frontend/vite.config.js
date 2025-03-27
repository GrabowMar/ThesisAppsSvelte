import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5823,
    strictPort: true,
    proxy: {
      '/api': {
        target: 'http://localhost:5323',
        changeOrigin: true,
        secure: false,
      },
      '/socket.io': {
        target: 'http://localhost:5323',
        changeOrigin: true,
        ws: true,
      }
    }
  }
})
