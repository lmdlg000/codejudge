import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// 开发联调：/api 转发到本机 FastAPI（uvicorn backend.app.main:app --port 8000）
// 部署预留（GitHub Pages 等静态托管）：
//   base: './' —— 资源相对路径，任意子路径可托管
//   VITE_ROUTER_MODE=hash —— 静态托管无 history 回退时用 hash 路由
//   VITE_API_BASE=https://your-api-host —— 前端静态、后端另部时指定 API 源
export default defineConfig({
  plugins: [vue()],
  base: './',
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true
      }
    }
  },
  build: {
    outDir: 'dist',
    emptyOutDir: true
  }
})
