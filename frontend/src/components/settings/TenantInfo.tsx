import { useState, useEffect } from 'react'
import axios from 'axios'
import { useNotifications } from '../../contexts/NotificationContext'

interface Tenant {
  tenant_id: string
  name: string
  domain?: string
  status: string
  config?: Record<string, any>
  created_at?: string
}

export default function TenantInfo() {
  const [tenant, setTenant] = useState<Tenant | null>(null)
  const [loading, setLoading] = useState(true)
  const { showError } = useNotifications()

  useEffect(() => {
    loadCurrentTenant()
  }, [])

  const loadCurrentTenant = async () => {
    try {
      setLoading(true)
      const tenantId = localStorage.getItem('current_tenant_id')
      if (!tenantId) {
        // Try to get from header or fetch first tenant
        try {
          const response = await axios.get('/tenants')
          const tenants = response.data?.tenants || response.data || []
          if (tenants.length > 0) {
            setTenant(tenants[0])
            localStorage.setItem('current_tenant_id', tenants[0].tenant_id)
          } else {
            setTenant(null)
          }
        } catch (fetchError: any) {
          console.error('Failed to fetch tenants list:', fetchError)
          setTenant(null)
        }
        return
      }

      // Fetch tenant details
      try {
        const response = await axios.get(`/tenants/${tenantId}`)
        setTenant(response.data)
      } catch (fetchError: any) {
        console.error('Failed to fetch tenant details:', fetchError)
        if (fetchError.response?.status === 404) {
          // Tenant not found, clear from localStorage
          localStorage.removeItem('current_tenant_id')
          setTenant(null)
        } else {
          showError('Failed to load tenant information')
          setTenant(null)
        }
      }
    } catch (error: any) {
      console.error('Failed to load tenant info:', error)
      setTenant(null)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-gray-400">Loading tenant information...</div>
      </div>
    )
  }

  if (!tenant) {
    return (
      <div className="text-center py-12">
        <div className="text-gray-400 mb-4">No tenant selected</div>
        <p className="text-sm text-gray-500">
          Use the tenant selector in the top bar to select a tenant
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="glass-panel rounded-lg p-6">
        <h3 className="text-xl font-bold mb-4">Current Tenant</h3>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-2">Tenant Name</label>
            <div className="px-4 py-2 bg-deep-space-50 border border-glass-border rounded-lg text-gray-300">
              {tenant.name}
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-400 mb-2">Tenant ID</label>
            <div className="px-4 py-2 bg-deep-space-50 border border-glass-border rounded-lg font-mono text-gray-300">
              {tenant.tenant_id}
            </div>
          </div>

          {tenant.domain && (
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-2">Domain</label>
              <div className="px-4 py-2 bg-deep-space-50 border border-glass-border rounded-lg text-gray-300">
                {tenant.domain}
              </div>
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-gray-400 mb-2">Status</label>
            <div className="px-4 py-2 bg-deep-space-50 border border-glass-border rounded-lg">
              <span
                className={`px-2 py-1 rounded text-xs font-medium ${
                  tenant.status === 'active'
                    ? 'bg-green-500/20 text-green-400'
                    : tenant.status === 'suspended'
                    ? 'bg-yellow-500/20 text-yellow-400'
                    : 'bg-red-500/20 text-red-400'
                }`}
              >
                {tenant.status.toUpperCase()}
              </span>
            </div>
          </div>

          {tenant.created_at && (
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-2">Created At</label>
              <div className="px-4 py-2 bg-deep-space-50 border border-glass-border rounded-lg text-gray-300">
                {new Date(tenant.created_at).toLocaleDateString('en-US', {
                  year: 'numeric',
                  month: 'long',
                  day: 'numeric',
                })}
              </div>
            </div>
          )}

          {tenant.config && Object.keys(tenant.config).length > 0 && (
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-2">Configuration</label>
              <div className="px-4 py-2 bg-deep-space-50 border border-glass-border rounded-lg">
                <pre className="text-xs text-gray-400 font-mono overflow-auto">
                  {JSON.stringify(tenant.config, null, 2)}
                </pre>
              </div>
            </div>
          )}
        </div>
      </div>

      <div className="glass-panel rounded-lg p-6 border border-blue-500/20">
        <div className="flex items-start gap-3">
          <div className="text-blue-400 text-xl">ℹ️</div>
          <div>
            <h4 className="font-medium text-gray-300 mb-2">About Tenants</h4>
            <p className="text-sm text-gray-400">
              Tenants provide data isolation. All your data (businesses, transactions, relationships) 
              is scoped to your current tenant. Switch tenants using the selector in the top bar.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
