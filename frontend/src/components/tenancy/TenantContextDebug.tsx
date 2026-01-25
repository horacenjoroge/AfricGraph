import { useState, useEffect } from 'react'
import axios from 'axios'

interface TenantContextDebugProps {
  showDetails?: boolean
}

export default function TenantContextDebug({ showDetails = false }: TenantContextDebugProps) {
  const [tenantId, setTenantId] = useState<string | null>(null)
  const [tenantInfo, setTenantInfo] = useState<any>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const checkTenant = async () => {
      const saved = localStorage.getItem('current_tenant_id')
      setTenantId(saved)

      if (saved && showDetails) {
        try {
          const response = await axios.get(`/tenants/${saved}`, {
            headers: {
              'X-Tenant-ID': saved,
            },
          })
          setTenantInfo(response.data)
          setError(null)
        } catch (err: any) {
          setError(err.response?.data?.detail || 'Failed to load tenant')
          setTenantInfo(null)
        }
      }
    }

    checkTenant()
    // Check every 2 seconds
    const interval = setInterval(checkTenant, 2000)
    return () => clearInterval(interval)
  }, [showDetails])

  if (!showDetails) {
    return (
      <div className="text-xs text-gray-500 font-mono">
        {tenantId ? `Tenant: ${tenantId.substring(0, 8)}...` : 'No tenant selected'}
      </div>
    )
  }

  return (
    <div className="glass-panel rounded-lg p-4 border border-slate-700/50">
      <h3 className="text-sm font-mono font-semibold text-cyan-400 mb-3">Tenant Context Debug</h3>
      
      <div className="space-y-2 text-xs font-mono">
        <div className="flex justify-between">
          <span className="text-gray-400">Tenant ID (localStorage):</span>
          <span className={tenantId ? 'text-cyan-400' : 'text-red-400'}>
            {tenantId || 'Not set'}
          </span>
        </div>
        
        <div className="flex justify-between">
          <span className="text-gray-400">Axios Header:</span>
          <span className={axios.defaults.headers.common['X-Tenant-ID'] ? 'text-cyan-400' : 'text-red-400'}>
            {axios.defaults.headers.common['X-Tenant-ID'] || 'Not set'}
          </span>
        </div>

        {tenantInfo && (
          <>
            <div className="flex justify-between">
              <span className="text-gray-400">Tenant Name:</span>
              <span className="text-white">{tenantInfo.name}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Status:</span>
              <span className={tenantInfo.status === 'active' ? 'text-green-400' : 'text-yellow-400'}>
                {tenantInfo.status}
              </span>
            </div>
          </>
        )}

        {error && (
          <div className="text-red-400 mt-2">
            Error: {error}
          </div>
        )}

        {!tenantId && (
          <div className="text-yellow-400 mt-2 p-2 bg-yellow-400/10 rounded">
            ⚠️ No tenant selected. Select a tenant from the dropdown to see data.
          </div>
        )}
      </div>
    </div>
  )
}
