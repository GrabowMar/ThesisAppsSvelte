import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5603,
    strictPort: true,
    proxy: {
      '/api': {
        target: 'http://localhost:5103',
        changeOrigin: true,
        secure: false,
      }
    }
  }
});
