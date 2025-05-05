// app/frontend/vite.config.js
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5641, // Frontend port as required
    strictPort: true,
    proxy: {
      // Proxy API calls to the backend running on port 6141
      '/register': {
        target: 'http://localhost:6141',
        changeOrigin: true,
      },
      '/login': {
        target: 'http://localhost:6141',
        changeOrigin: true,
      },
      '/dashboard': {
        target: 'http://localhost:6141',
        changeOrigin: true,
      },
      '/logout': {
        target: 'http://localhost:6141',
        changeOrigin: true,
      },
    },
  },
});
