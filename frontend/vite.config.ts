import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// En GitHub Pages el repo se sirve desde /pisubit/
// En Vercel/Railway la base es /
const isGHPages = process.env.DEPLOY_TARGET === 'ghpages'

export default defineConfig({
  plugins: [react()],
  base: isGHPages ? '/comm-track/' : '/',
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
    },
  },
})
