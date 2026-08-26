import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '');
  const backendPort = env.VITE_BACKEND_PORT || env.BACKEND_PORT || '8090';
  const backendUrl = env.VITE_BACKEND_URL || `http://127.0.0.1:${backendPort}`;
  const backendWsUrl = env.VITE_BACKEND_WS_URL || `ws://127.0.0.1:${backendPort}`;
  const frontendPort = parseInt(env.VITE_PORT || env.PORT || '5180', 10);

  return {
    plugins: [react()],
    server: {
      port: frontendPort,
      strictPort: false, // auto-switch to next free port if 5180 is taken
      proxy: {
        '/api': {
          target: backendUrl,
          changeOrigin: true,
        },
        '/health': {
          target: backendUrl,
          changeOrigin: true,
        },
        '/ws': {
          target: backendWsUrl,
          ws: true,
          changeOrigin: true,
        },
      },
    },
  };
});
