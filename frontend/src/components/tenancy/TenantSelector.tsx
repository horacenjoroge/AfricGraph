import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import axios from 'axios'
import { useNotifications } from '../../contexts/NotificationContext'

interface Tenant {
  tenant_id: string
  name: string
  domain?: string
  status: string
}

export default function TenantSelector() {
  const [tenants, setTenants] = useState<Tenant[]>([])
  const [currentTenant, setCurrentTenant] = useState<Tenant | null>(null)
  const [isOpen, setIsOpen] = useState(false)
  const [loading, setLoading] = useState(false)
  const { showError, showSuccess } = useNotifications()

  useEffect(() => {
    fetchTenants()
    loadCurrentTenant()
  }, [])

  const fetchTenants = async () => {
    setLoading(true)
    try {
      const response = await axios.get('/tenants')
      // Backend returns {tenants: [...], total: ...}
      const tenantList = response.data?.tenants || response.data || []
      setTenants(Array.isArray(tenantList) ? tenantList : [])
      console.log('Fetched tenants:', tenantList)
    } catch (error: any) {
      console.error('Failed to fetch tenants:', error)
      setTenants([])
      if (error.response?.status !== 404) {
        showError('Failed to load tenants')
      }
    } finally {
      setLoading(false)
    }
  }

  const loadCurrentTenant = () => {
    const saved = localStorage.getItem('current_tenant_id')
    if (saved) {
      // Try to find the tenant in the list
      const tenant = tenants.find((t) => t.tenant_id === saved)
      if (tenant) {
        setCurrentTenant(tenant)
      }
    }
  }

  const switchTenant = async (tenant: Tenant) => {
    setLoading(true)
    try {
      // Save to localStorage
      localStorage.setItem('current_tenant_id', tenant.tenant_id)
      
      // Set header for future requests
      axios.defaults.headers.common['X-Tenant-ID'] = tenant.tenant_id
      
      setCurrentTenant(tenant)
      setIsOpen(false)
      showSuccess(`Switched to tenant: ${tenant.name}`)
      
      // Reload the page to refresh all data
      window.location.reload()
    } catch (error) {
      console.error('Failed to switch tenant:', error)
      showError('Failed to switch tenant')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (currentTenant) {
      axios.defaults.headers.common['X-Tenant-ID'] = currentTenant.tenant_id
    }
  }, [currentTenant])

  useEffect(() => {
    if (tenants.length > 0 && !currentTenant) {
      loadCurrentTenant()
    }
  }, [tenants])

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="glass-panel px-3 py-2 rounded-lg hover:bg-glass/50 transition-all border border-glass-border flex items-center gap-2 text-sm"
        disabled={loading}
      >
        <div className="w-2 h-2 rounded-full bg-glow-cyan"></div>
        <span className="font-mono text-xs">
          {currentTenant ? currentTenant.name : 'Select Tenant'}
        </span>
        <svg
          className={`w-4 h-4 transition-transform ${isOpen ? 'rotate-180' : ''}`}
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
        >
          <polyline points="6 9 12 15 18 9" />
        </svg>
      </button>

      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="absolute top-full mt-2 right-0 z-50 glass-panel-strong border border-glass-border rounded-lg p-2 min-w-[200px] max-h-[300px] overflow-y-auto shadow-lg"
            onClick={(e) => e.stopPropagation()}
          >
            {loading ? (
              <div className="px-4 py-3 text-sm text-gray-400 text-center">
                Loading...
              </div>
            ) : tenants.length === 0 ? (
              <div className="px-4 py-3 text-sm text-gray-400 text-center">
                <div className="mb-2">No tenants available</div>
                <div className="text-xs text-gray-500 mt-2">
                  Create a tenant via API or check backend logs
                </div>
              </div>
            ) : (
              <>
                {tenants.map((tenant) => (
                  <button
                    key={tenant.tenant_id}
                    onClick={() => switchTenant(tenant)}
                    className={`w-full text-left px-4 py-2 rounded-lg transition-colors mb-1 ${
                      currentTenant?.tenant_id === tenant.tenant_id
                        ? 'bg-glow-cyan/20 text-glow-cyan'
                        : 'hover:bg-glass/50 text-gray-300'
                    }`}
                  >
                    <div className="font-medium text-sm">{tenant.name}</div>
                    <div className="text-xs text-gray-500 font-mono mt-1">
                      {tenant.tenant_id.substring(0, 8)}...
                    </div>
                  </button>
                ))}
                <div className="border-t border-glass-border mt-2 pt-2">
                  <button
                    onClick={() => {
                      fetchTenants()
                    }}
                    className="w-full text-left px-4 py-2 rounded-lg hover:bg-glass/50 text-sm text-gray-400"
                  >
                    Refresh List
                  </button>
                </div>
              </>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
