import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5799,
    proxy: {
      "/api": {
        target: "http://localhost:5299",
        changeOrigin: true,
        secure: false,
      },
    },
  },
});
