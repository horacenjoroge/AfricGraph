import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        configure: (proxy, _options) => {
          proxy.on('proxyReq', (proxyReq, req, _res) => {
            // Ensure X-Tenant-ID header is forwarded
            const tenantId = req.headers['x-tenant-id'] || req.headers['X-Tenant-ID']
            if (tenantId) {
              proxyReq.setHeader('X-Tenant-ID', tenantId)
              console.log('[Vite Proxy] Forwarding X-Tenant-ID:', tenantId)
            }
          })
        },
      },
      '/auth': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/tenants': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/graphql': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
})
