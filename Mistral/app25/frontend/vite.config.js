import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5629,
    strictPort: true,
    proxy: {
      '/api': {
        target: 'http://localhost:5129',
        changeOrigin: true,
        secure: false,
      }
    }
  }
});
