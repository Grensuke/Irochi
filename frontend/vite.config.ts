import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

const proxyTarget = process.env.PROXY_TARGET || 'localhost:8000'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: `http://${proxyTarget}`,
        changeOrigin: true,
      },
      '/api/v1/ws': {
        target: `ws://${proxyTarget}`,
        ws: true,
      },
    },
  },
})
