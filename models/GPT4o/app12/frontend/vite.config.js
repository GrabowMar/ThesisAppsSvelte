import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5763,
    proxy: {
      '/api': {
        target: 'http://localhost:5263',
        changeOrigin: true,
        secure: false,
      },
    },
  },
});
