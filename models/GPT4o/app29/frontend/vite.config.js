import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5797,
    strictPort: true,
    proxy: {
      "/api": {
        target: "http://localhost:5297",
        changeOrigin: true,
        secure: false,
      },
    },
  },
});
