import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5689,  // Updated frontend port
    proxy: {
      '/': 'http://localhost:5189',  // Updated backend port
    },
  },
});
