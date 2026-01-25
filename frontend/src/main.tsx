import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { NotificationProvider } from './contexts/NotificationContext'
import App from './App.tsx'
import './index.css'
import axios from 'axios'

// Set up axios interceptor to include X-Tenant-ID header from localStorage on all requests
axios.interceptors.request.use((config) => {
  const tenantId = localStorage.getItem('current_tenant_id')
  if (tenantId) {
    config.headers['X-Tenant-ID'] = tenantId
  }
  return config
})

// Also set default header if tenant exists on app load
const savedTenantId = localStorage.getItem('current_tenant_id')
if (savedTenantId) {
  axios.defaults.headers.common['X-Tenant-ID'] = savedTenantId
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <BrowserRouter>
      <NotificationProvider>
        <App />
      </NotificationProvider>
    </BrowserRouter>
  </React.StrictMode>,
)
