import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5657,
    strictPort: true,
    proxy: {
      '/api': {
        target: 'http://localhost:6157',
        changeOrigin: true,
        secure: false
      }
    }
  }
});
