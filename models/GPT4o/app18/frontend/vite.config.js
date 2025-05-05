import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5775,
    proxy: {
      '/api': {
        target: 'http://localhost:5275',
        changeOrigin: true,
        secure: false,
      },
    },
  },
});
