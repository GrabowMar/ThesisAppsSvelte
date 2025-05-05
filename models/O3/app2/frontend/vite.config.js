// app/frontend/vite.config.js
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5643, // Frontend Vite dev server runs on port 5643
    strictPort: true,
    proxy: {
      // Proxy API calls to the Flask backend on port 6143
      '/api': {
        target: 'http://localhost:6143',
        changeOrigin: true,
        secure: false,
      }
    }
  }
});
