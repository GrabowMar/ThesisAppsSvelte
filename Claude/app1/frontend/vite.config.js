import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5821,
    strictPort: true,
    proxy: {
      '/api': {
        target: 'http://localhost:5321',
        changeOrigin: true,
      }
    }
  }
});