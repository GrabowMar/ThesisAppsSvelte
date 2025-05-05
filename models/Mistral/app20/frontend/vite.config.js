import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5619,
    strictPort: true,
    proxy: {
      '/api': {
        target: 'http://localhost:5119',
        changeOrigin: true,
        secure: false,
      }
    }
  }
});
