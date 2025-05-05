import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5787,
    proxy: {
      '/api': {
        target: 'http://localhost:5287',
        changeOrigin: true,
        secure: false,
      },
    },
  },
});
