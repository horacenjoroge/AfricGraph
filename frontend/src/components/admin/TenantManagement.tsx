import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import axios from 'axios'
import { useNotifications } from '../../contexts/NotificationContext'

interface Tenant {
  tenant_id: string
  name: string
  domain?: string
  status: string
  config?: Record<string, any>
  created_at: string
}

export default function TenantManagement() {
  const [tenants, setTenants] = useState<Tenant[]>([])
  const [loading, setLoading] = useState(true)
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [editingTenant, setEditingTenant] = useState<Tenant | null>(null)
  const [formData, setFormData] = useState({
    tenant_id: '',
    name: '',
    domain: '',
    status: 'active',
  })
  const { showSuccess, showError } = useNotifications()

  useEffect(() => {
    fetchTenants()
  }, [])

  const fetchTenants = async () => {
    try {
      setLoading(true)
      const token = localStorage.getItem('auth_token')
      if (!token) {
        console.warn('No auth token found')
        setTenants([])
        return
      }
      
      const response = await axios.get('/tenants', {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      })
      const tenantList = response.data?.tenants || []
      console.log('Fetched tenants in Admin panel:', tenantList)
      setTenants(tenantList)
      
      if (tenantList.length === 0) {
        console.warn('No tenants found. Response:', response.data)
      }
    } catch (error: any) {
      console.error('Failed to fetch tenants:', error)
      console.error('Error response:', error.response?.data)
      setTenants([])
      if (error.response?.status === 401 || error.response?.status === 403) {
        showError('Admin access required to view tenants')
      } else {
        showError(error.response?.data?.detail || 'Failed to load tenants')
      }
    } finally {
      setLoading(false)
    }
  }

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      const token = localStorage.getItem('auth_token')
      if (!token) {
        showError('You must be logged in to create tenants')
        return
      }
      
      console.log('Creating tenant:', formData)
      const response = await axios.post(
        '/tenants',
        {
          tenant_id: formData.tenant_id,
          name: formData.name,
          domain: formData.domain || undefined,
          config: {},
        },
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      )
      console.log('Tenant creation response:', response.data)
      showSuccess(`Tenant "${formData.name}" created successfully`)
      setShowCreateForm(false)
      setFormData({ tenant_id: '', name: '', domain: '', status: 'active' })
      // Wait a bit before fetching to ensure database is updated
      setTimeout(() => {
        fetchTenants()
      }, 500)
    } catch (error: any) {
      console.error('Failed to create tenant:', error)
      console.error('Error response:', error.response?.data)
      const errorMessage = error.response?.data?.detail || error.message || 'Failed to create tenant'
      showError(errorMessage)
      
      // If it's a 403, user might not be admin
      if (error.response?.status === 403) {
        showError('Admin role required to create tenants. Please contact an administrator.')
      } else if (error.response?.status === 401) {
        showError('You must be logged in to create tenants')
      }
    }
  }

  const handleUpdate = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!editingTenant) return

    try {
      const token = localStorage.getItem('auth_token')
      await axios.put(
        `/tenants/${editingTenant.tenant_id}`,
        {
          name: formData.name,
          domain: formData.domain || undefined,
          status: formData.status,
        },
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      )
      showSuccess('Tenant updated successfully')
      setEditingTenant(null)
      setFormData({ tenant_id: '', name: '', domain: '', status: 'active' })
      fetchTenants()
    } catch (error: any) {
      console.error('Failed to update tenant:', error)
      showError(error.response?.data?.detail || 'Failed to update tenant')
    }
  }

  const startEdit = (tenant: Tenant) => {
    setEditingTenant(tenant)
    setFormData({
      tenant_id: tenant.tenant_id,
      name: tenant.name,
      domain: tenant.domain || '',
      status: tenant.status,
    })
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-gray-400">Loading tenants...</div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header with Create Button */}
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold">Tenants</h2>
        <button
          onClick={() => {
            setShowCreateForm(true)
            setEditingTenant(null)
            setFormData({ tenant_id: '', name: '', domain: '', status: 'active' })
          }}
          className="px-4 py-2 bg-blue-500/20 text-blue-400 rounded-lg hover:bg-blue-500/30 transition-colors"
        >
          Create Tenant
        </button>
      </div>

      {/* Create/Edit Form */}
      {(showCreateForm || editingTenant) && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="glass-panel border border-blue-500/30 rounded-lg p-6"
        >
          <h3 className="text-lg font-bold mb-4">
            {editingTenant ? 'Edit Tenant' : 'Create New Tenant'}
          </h3>
          <form onSubmit={editingTenant ? handleUpdate : handleCreate} className="space-y-4">
            {!editingTenant && (
              <div>
                <label className="block text-sm font-medium text-gray-400 mb-2">Tenant ID</label>
                <input
                  type="text"
                  value={formData.tenant_id}
                  onChange={(e) => setFormData({ ...formData, tenant_id: e.target.value })}
                  className="w-full px-4 py-2 bg-deep-space-50 border border-glass-border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-300"
                  placeholder="acme-corp"
                  required
                />
              </div>
            )}
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-2">Name</label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="w-full px-4 py-2 bg-deep-space-50 border border-glass-border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-300"
                placeholder="Acme Corporation"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-2">Domain (Optional)</label>
              <input
                type="text"
                value={formData.domain}
                onChange={(e) => setFormData({ ...formData, domain: e.target.value })}
                className="w-full px-4 py-2 bg-deep-space-50 border border-glass-border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-300"
                placeholder="acme.africgraph.com"
              />
            </div>
            {editingTenant && (
              <div>
                <label className="block text-sm font-medium text-gray-400 mb-2">Status</label>
                <select
                  value={formData.status}
                  onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                  className="w-full px-4 py-2 bg-deep-space-50 border border-glass-border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-300"
                >
                  <option value="active">Active</option>
                  <option value="suspended">Suspended</option>
                  <option value="inactive">Inactive</option>
                </select>
              </div>
            )}
            <div className="flex gap-3">
              <button
                type="submit"
                className="px-6 py-2 bg-blue-500/20 text-blue-400 rounded-lg hover:bg-blue-500/30 transition-colors"
              >
                {editingTenant ? 'Update' : 'Create'}
              </button>
              <button
                type="button"
                onClick={() => {
                  setShowCreateForm(false)
                  setEditingTenant(null)
                  setFormData({ tenant_id: '', name: '', domain: '', status: 'active' })
                }}
                className="px-6 py-2 bg-gray-500/20 text-gray-400 rounded-lg hover:bg-gray-500/30 transition-colors"
              >
                Cancel
              </button>
            </div>
          </form>
        </motion.div>
      )}

      {/* Tenants List */}
      <div className="space-y-4">
        {tenants.length === 0 ? (
          <div className="text-center py-12 text-gray-400">
            No tenants found. Create one to get started.
          </div>
        ) : (
          tenants.map((tenant) => (
            <motion.div
              key={tenant.tenant_id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="glass-panel rounded-lg p-6 border border-glass-border"
            >
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <h3 className="text-lg font-bold font-mono">{tenant.name}</h3>
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
                  <div className="text-sm text-gray-400 space-y-1">
                    <p>
                      <strong>ID:</strong> <span className="font-mono">{tenant.tenant_id}</span>
                    </p>
                    {tenant.domain && (
                      <p>
                        <strong>Domain:</strong> <span className="font-mono">{tenant.domain}</span>
                      </p>
                    )}
                    <p>
                      <strong>Created:</strong>{' '}
                      {new Date(tenant.created_at).toLocaleDateString()}
                    </p>
                  </div>
                </div>
                <button
                  onClick={() => startEdit(tenant)}
                  className="px-4 py-2 bg-blue-500/20 text-blue-400 rounded-lg hover:bg-blue-500/30 transition-colors"
                >
                  Edit
                </button>
              </div>
            </motion.div>
          ))
        )}
      </div>
    </div>
  )
}
