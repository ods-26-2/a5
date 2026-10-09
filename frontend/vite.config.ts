import { defineConfig } from 'vite';

// O front fala com o backend A5 pelo prefixo /api (proxy em dev), entao nao
// precisa de CORS no backend. Para apontar para outro host:
//   A5_API_TARGET=http://meu-host:8000 npm run dev
const target = process.env.A5_API_TARGET ?? 'http://127.0.0.1:8000';

export default defineConfig({
  server: {
    proxy: {
      '/api': { target, changeOrigin: true, rewrite: (p) => p.replace(/^\/api/, '') },
    },
  },
  test: {
    environment: 'jsdom',
    include: ['src/**/*.test.ts', 'vendor/**/*.test.ts'],
  },
});
