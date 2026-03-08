import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Vite configuration for PropPulse frontend
// - Proxies /api/* requests to FastAPI backend on port 8000 during development
//   so we avoid CORS issues and don't need to hardcode the backend URL
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
