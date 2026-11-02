import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';

function localApiTarget(): string {
  const configuredTarget = process.env.VIRMS_API_TARGET || 'http://127.0.0.1:8001';
  const target = new URL(configuredTarget);
  const loopbackHosts = new Set(['127.0.0.1', 'localhost', '[::1]', '::1']);
  if (
    target.protocol !== 'http:' ||
    !loopbackHosts.has(target.hostname) ||
    target.pathname !== '/' ||
    target.search ||
    target.hash ||
    target.username ||
    target.password
  ) {
    throw new Error('VIRMS_API_TARGET must be an http loopback origin without credentials or a path.');
  }
  return target.origin;
}

const apiProxy = {
  '/api/v1': {
    target: localApiTarget(),
    changeOrigin: false,
  },
  '/admin': {
    target: localApiTarget(),
    changeOrigin: false,
  },
  '/static': {
    target: localApiTarget(),
    changeOrigin: false,
  },
};

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    host: '127.0.0.1',
    port: 5173,
    proxy: apiProxy,
  },
  preview: {
    host: '127.0.0.1',
    port: 5173,
    proxy: apiProxy,
  },
  test: {
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    clearMocks: true,
    restoreMocks: true,
  },
});
