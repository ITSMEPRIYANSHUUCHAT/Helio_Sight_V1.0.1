import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react-swc';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://fastapi:8000',  // Use service name in Docker network (not localhost)
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),  // /api/auth/login → /auth/login
      },
    },
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
});