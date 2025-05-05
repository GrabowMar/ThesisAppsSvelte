import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5759,
    proxy: {
      '/api': {
        target: 'http://localhost:5259',
        changeOrigin: true,
      },
    },
  },
});
