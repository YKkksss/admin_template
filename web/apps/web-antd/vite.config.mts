import { defineConfig } from '@vben/vite-config';

export default defineConfig(async () => {
  return {
    application: {},
    vite: {
      server: {
        proxy: {
          '/api': {
            changeOrigin: true,
            // 将前端的 /api 前缀映射到后端的 /api/v1（便于保持前端代码不改动）
            rewrite: (path) => path.replace(/^\/api/, '/api/v1'),
            // 后端服务地址
            target: 'http://localhost:8000',
            ws: true,
          },
        },
      },
    },
  };
});
