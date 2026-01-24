import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import TenantManagement from '../components/admin/TenantManagement'
import IngestionManagement from '../components/admin/IngestionManagement'
import axios from 'axios'
import { useNotifications } from '../contexts/NotificationContext'
import { useNavigate } from 'react-router-dom'

type TabType = 'tenants' | 'ingestion'

export default function AdminPage() {
  const [activeTab, setActiveTab] = useState<TabType>('tenants')
  const [isAdmin, setIsAdmin] = useState(false)
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()
  const { showError } = useNotifications()

  useEffect(() => {
    checkAdminAccess()
  }, [])

  const checkAdminAccess = async () => {
    try {
      setLoading(true)
      const token = localStorage.getItem('auth_token')
      if (!token) {
        showError('Authentication required to access admin page')
        navigate('/login')
        return
      }

      const response = await axios.get('/auth/me', {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      })

      console.log('Admin check - User data:', response.data)
      console.log('Admin check - User role:', response.data.role)
      console.log('Admin check - Is admin?', response.data.role === 'admin')

      if (response.data.role === 'admin') {
        setIsAdmin(true)
      } else {
        showError(`Admin role required. Your current role is: ${response.data.role || 'unknown'}`)
        // Don't navigate immediately, show the error first
        setTimeout(() => navigate('/'), 2000)
      }
    } catch (error: any) {
      console.error('Failed to check admin access:', error)
      console.error('Error response:', error.response)
      showError(`Failed to verify admin access: ${error.response?.data?.detail || error.message}`)
      // Don't navigate immediately, show the error first
      setTimeout(() => navigate('/'), 2000)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-gray-400">Verifying admin access...</div>
      </div>
    )
  }

  if (!isAdmin) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="glass-panel rounded-lg p-8 max-w-md text-center">
          <h2 className="text-2xl font-bold mb-4 text-red-400">Access Denied</h2>
          <p className="text-gray-400 mb-4">
            You need admin privileges to access this page.
          </p>
          <p className="text-sm text-gray-500 mb-6">
            Check the browser console for details about your current role.
          </p>
          <button
            onClick={() => navigate('/')}
            className="px-6 py-2 bg-blue-500/20 text-blue-400 rounded-lg hover:bg-blue-500/30 transition-colors"
          >
            Go to Dashboard
          </button>
        </div>
      </div>
    )
  }

  const tabs: { id: TabType; label: string }[] = [
    { id: 'tenants', label: 'Tenant Management' },
    { id: 'ingestion', label: 'Ingestion Management' },
  ]

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold font-mono mb-2">Admin Panel</h1>
        <p className="text-gray-400">Manage tenants and ingestion jobs</p>
      </div>

      {/* Tabs */}
      <div className="glass-panel rounded-lg p-6">
        <div className="flex gap-4 border-b border-glass-border mb-6">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`pb-4 px-4 font-medium transition-colors ${
                activeTab === tab.id
                  ? 'text-blue-400 border-b-2 border-blue-400'
                  : 'text-gray-400 hover:text-white'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        <motion.div
          key={activeTab}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.2 }}
        >
          {activeTab === 'tenants' && <TenantManagement />}
          {activeTab === 'ingestion' && <IngestionManagement />}
        </motion.div>
      </div>
    </div>
  )
}
