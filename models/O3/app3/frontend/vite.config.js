// app/frontend/vite.config.js

import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5645, // Frontend Vite server running on port 5645
    strictPort: true,
    proxy: {
      '/api': {
        target: 'http://localhost:6145', // Proxy API requests to Flask backend on port 6145
        changeOrigin: true,
        secure: false,
      },
    },
  },
});
