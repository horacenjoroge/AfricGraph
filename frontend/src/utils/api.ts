import axios from 'axios'

const api = axios.create({
  baseURL: '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
})

// Add request interceptor for auth tokens and tenant ID
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  
  // Always include X-Tenant-ID from localStorage if available
  const tenantId = localStorage.getItem('current_tenant_id')
  if (tenantId) {
    config.headers['X-Tenant-ID'] = tenantId
  }
  
  return config
})

export default api
