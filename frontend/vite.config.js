import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vite.dev/config/
export default defineConfig({
  base: '/static/frontend/',
  plugins: [vue()],
  build: {
    outDir: '../static/frontend',
    emptyOutDir: true,
  },
})
