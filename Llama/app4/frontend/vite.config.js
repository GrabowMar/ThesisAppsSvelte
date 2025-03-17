// vite.config.js
import { defineConfig } from 'vite';

export default defineConfig({
    base: 'http://localhost:5507',
    server: {
        proxy: {
            '/api': 'http://localhost:5007',
        },
    },
});
