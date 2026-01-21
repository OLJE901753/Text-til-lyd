import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react-swc'
import path from 'path'
import fs from 'fs'

// Detect if running in Docker and get appropriate proxy target
const getApiProxyTarget = () => {
  // Check for explicit proxy target env var (highest priority)
  if (process.env.VITE_API_PROXY_TARGET) {
    return process.env.VITE_API_PROXY_TARGET
  }
  // Auto-detect Docker (works even if env vars aren't injected / container wasn't recreated)
  if (process.env.DOCKER_ENV === 'true' || fs.existsSync('/.dockerenv')) {
    return 'http://backend:3001'
  }
  // Default to localhost for local development (outside Docker)
  return 'http://localhost:3001'
}

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    host: '0.0.0.0', // Allow access from outside container
    port: 8081,
    strictPort: true,
    open: false,
    hmr: {
    port: 8081,
    },
    proxy: {
      '/api': {
        target: getApiProxyTarget(),
        changeOrigin: true,
        secure: false,
        ws: true, // Enable WebSocket proxying
      },
    },
  },
  // Optimize build and dev server memory usage
  build: {
    target: 'esnext',
    minify: 'esbuild',
    chunkSizeWarningLimit: 1000,
    rollupOptions: {
      output: {
        manualChunks: {
          'react-vendor': ['react', 'react-dom', 'react-router-dom'],
          'ui-vendor': ['@radix-ui/react-dialog', '@radix-ui/react-label', '@radix-ui/react-progress', '@radix-ui/react-slot', '@radix-ui/react-toast'],
        },
      },
    },
  },
  // Optimize dev server
  optimizeDeps: {
    include: ['react', 'react-dom', 'react-router-dom'],
    exclude: ['@tanstack/react-query'],
  },
})
