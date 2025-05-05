// frontend/vite.config.js

import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5295,
    proxy: {
      '/api': {
        target: 'http://localhost:5795',
        changeOrigin: true,
        secure: false,
      },
    },
  },
});
