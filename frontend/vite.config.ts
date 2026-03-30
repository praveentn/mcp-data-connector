import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 7791,
    host: true,
    proxy: {
      '/api': {
        target: 'http://localhost:7790',
        changeOrigin: true,
      },
      '/ws': {
        target: 'ws://localhost:7790',
        ws: true,
        changeOrigin: true,
      },
    },
  },
})
