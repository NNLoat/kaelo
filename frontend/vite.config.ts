import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    host: true, // listen on 0.0.0.0 so the container port is reachable
    port: 5173,
    watch: {
      // Polling makes file-watching reliable inside Docker on macOS/Windows.
      usePolling: true,
    },
  },
});
