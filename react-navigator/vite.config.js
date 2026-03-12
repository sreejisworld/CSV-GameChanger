import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig(({ mode }) => ({
  // In production the React build is served by FastAPI at /navigator/
  // In development (npm run dev) it is served from root on port 3000
  base: mode === 'production' ? '/navigator/' : '/',

  plugins: [react()],

  server: {
    port: 3000,
    proxy: {
      // Forward /api calls to FastAPI on port 8000 during dev
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
}))
