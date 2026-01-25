import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import axios from 'axios'
import { useNotifications } from '../../contexts/NotificationContext'

interface TenantHealth {
  tenant_id: string
  status: string
  healthy: boolean
  node_count: number
  relationship_count: number
  created_at: string
  last_updated: string
}

interface TenantUsage {
  tenant_id: string
  period_days: number
  operation_count: number
  active_days: number
  first_activity: string | null
  last_activity: string | null
}

interface TenantQuota {
  quota_type: string
  limit: number
  current_usage: number
  remaining: number
  usage_percentage: number
  is_exceeded: boolean
}

interface TenantMetrics {
  health: TenantHealth
  usage: TenantUsage
  quotas: TenantQuota[]
}

export default function TenantPerformanceDashboard() {
  const [currentTenantId, setCurrentTenantId] = useState<string | null>(null)
  const [metrics, setMetrics] = useState<TenantMetrics | null>(null)
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const { showError } = useNotifications()

  useEffect(() => {
    // Get current tenant from context or localStorage
    const tenantId = localStorage.getItem('current_tenant_id') || 
                     (window as any).__TENANT_ID__ || 
                     null
    setCurrentTenantId(tenantId)
    
    if (tenantId) {
      fetchMetrics(tenantId)
    }
    
    // Auto-refresh every 30 seconds
    const interval = setInterval(() => {
      if (tenantId) {
        refreshMetrics(tenantId)
      }
    }, 30000)
    
    return () => clearInterval(interval)
  }, [])

  const fetchMetrics = async (tenantId: string) => {
    try {
      setLoading(true)
      const token = localStorage.getItem('auth_token')
      
      if (!token) {
        showError('Authentication required')
        return
      }

      const headers = {
        Authorization: `Bearer ${token}`,
        'X-Tenant-ID': tenantId,
      }

      // Fetch all metrics in parallel
      const [healthRes, usageRes, quotasRes] = await Promise.allSettled([
        axios.get(`/tenants/${tenantId}/health`, { headers }),
        axios.get(`/tenants/${tenantId}/usage?days=30`, { headers }),
        // Quotas would come from a quotas endpoint (to be implemented)
        Promise.resolve({ data: [] }),
      ])

      const health = healthRes.status === 'fulfilled' ? healthRes.value.data : null
      const usage = usageRes.status === 'fulfilled' ? usageRes.value.data : null
      const quotas = quotasRes.status === 'fulfilled' ? quotasRes.value.data : []

      if (health && usage) {
        setMetrics({
          health,
          usage,
          quotas: quotas || [],
        })
      }
    } catch (error: any) {
      console.error('Failed to fetch tenant metrics:', error)
      showError(error.response?.data?.detail || 'Failed to load tenant metrics')
    } finally {
      setLoading(false)
    }
  }

  const refreshMetrics = async (tenantId: string) => {
    try {
      setRefreshing(true)
      await fetchMetrics(tenantId)
    } finally {
      setRefreshing(false)
    }
  }

  const formatNumber = (num: number): string => {
    if (num >= 1000000) {
      return (num / 1000000).toFixed(1) + 'M'
    }
    if (num >= 1000) {
      return (num / 1000).toFixed(1) + 'K'
    }
    return num.toString()
  }

  const getHealthColor = (healthy: boolean): string => {
    return healthy ? 'text-cyan-400' : 'text-red-400'
  }

  const getHealthGlow = (healthy: boolean): string => {
    return healthy ? 'shadow-[0_0_20px_rgba(34,211,238,0.3)]' : 'shadow-[0_0_20px_rgba(239,68,68,0.3)]'
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-cyan-400"></div>
      </div>
    )
  }

  if (!currentTenantId) {
    return (
      <div className="text-center py-12 text-gray-400">
        <p>No tenant selected</p>
        <p className="text-sm mt-2">Please select a tenant to view performance metrics</p>
      </div>
    )
  }

  if (!metrics) {
    return (
      <div className="text-center py-12 text-gray-400">
        <p>No metrics available</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-mono font-bold text-cyan-400">Tenant Performance</h2>
          <p className="text-sm text-gray-400 mt-1">Real-time metrics and health monitoring</p>
        </div>
        <button
          onClick={() => refreshMetrics(currentTenantId)}
          disabled={refreshing}
          className="px-4 py-2 bg-cyan-500/10 border border-cyan-500/30 rounded-lg text-cyan-400 hover:bg-cyan-500/20 transition-colors disabled:opacity-50"
        >
          {refreshing ? 'Refreshing...' : 'Refresh'}
        </button>
      </div>

      {/* Health Status Card */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className={`relative backdrop-blur-md bg-slate-900/50 border border-slate-700/50 rounded-xl p-6 ${getHealthGlow(metrics.health.healthy)}`}
      >
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-mono font-semibold text-white">Health Status</h3>
          <div className={`flex items-center gap-2 ${getHealthColor(metrics.health.healthy)}`}>
            <div className={`w-3 h-3 rounded-full ${metrics.health.healthy ? 'bg-cyan-400' : 'bg-red-400'} animate-pulse`}></div>
            <span className="font-mono text-sm">
              {metrics.health.healthy ? 'HEALTHY' : 'UNHEALTHY'}
            </span>
          </div>
        </div>
        
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <p className="text-xs text-gray-400 mb-1">Status</p>
            <p className="font-mono text-cyan-400">{metrics.health.status.toUpperCase()}</p>
          </div>
          <div>
            <p className="text-xs text-gray-400 mb-1">Nodes</p>
            <p className="font-mono text-white">{formatNumber(metrics.health.node_count)}</p>
          </div>
          <div>
            <p className="text-xs text-gray-400 mb-1">Relationships</p>
            <p className="font-mono text-white">{formatNumber(metrics.health.relationship_count)}</p>
          </div>
          <div>
            <p className="text-xs text-gray-400 mb-1">Last Updated</p>
            <p className="font-mono text-xs text-gray-400">
              {new Date(metrics.health.last_updated).toLocaleDateString()}
            </p>
          </div>
        </div>
      </motion.div>

      {/* Usage Metrics */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="backdrop-blur-md bg-slate-900/50 border border-slate-700/50 rounded-xl p-6"
      >
        <h3 className="text-lg font-mono font-semibold text-white mb-4">Usage (Last 30 Days)</h3>
        
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <p className="text-xs text-gray-400 mb-1">Operations</p>
            <p className="font-mono text-2xl text-cyan-400">{formatNumber(metrics.usage.operation_count)}</p>
          </div>
          <div>
            <p className="text-xs text-gray-400 mb-1">Active Days</p>
            <p className="font-mono text-2xl text-white">{metrics.usage.active_days}</p>
          </div>
          <div>
            <p className="text-xs text-gray-400 mb-1">First Activity</p>
            <p className="font-mono text-xs text-gray-400">
              {metrics.usage.first_activity 
                ? new Date(metrics.usage.first_activity).toLocaleDateString()
                : 'N/A'}
            </p>
          </div>
          <div>
            <p className="text-xs text-gray-400 mb-1">Last Activity</p>
            <p className="font-mono text-xs text-gray-400">
              {metrics.usage.last_activity 
                ? new Date(metrics.usage.last_activity).toLocaleDateString()
                : 'N/A'}
            </p>
          </div>
        </div>
      </motion.div>

      {/* Quotas */}
      {metrics.quotas.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="backdrop-blur-md bg-slate-900/50 border border-slate-700/50 rounded-xl p-6"
        >
          <h3 className="text-lg font-mono font-semibold text-white mb-4">Resource Quotas</h3>
          
          <div className="space-y-4">
            {metrics.quotas.map((quota, index) => (
              <div key={index} className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-400 font-mono">{quota.quota_type}</span>
                  <span className={`font-mono ${quota.is_exceeded ? 'text-red-400' : 'text-cyan-400'}`}>
                    {quota.current_usage.toLocaleString()} / {quota.limit.toLocaleString()}
                  </span>
                </div>
                <div className="w-full bg-slate-800 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full transition-all ${
                      quota.is_exceeded 
                        ? 'bg-red-500' 
                        : quota.usage_percentage > 80 
                        ? 'bg-yellow-500' 
                        : 'bg-cyan-500'
                    }`}
                    style={{ width: `${Math.min(100, quota.usage_percentage)}%` }}
                  ></div>
                </div>
                <div className="text-xs text-gray-500 font-mono">
                  {quota.usage_percentage.toFixed(1)}% used • {quota.remaining.toLocaleString()} remaining
                </div>
              </div>
            ))}
          </div>
        </motion.div>
      )}

      {/* Performance Chart Placeholder */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
        className="backdrop-blur-md bg-slate-900/50 border border-slate-700/50 rounded-xl p-6"
      >
        <h3 className="text-lg font-mono font-semibold text-white mb-4">Performance Trends</h3>
        <div className="h-64 flex items-center justify-center text-gray-500">
          <p className="text-sm">Chart visualization coming soon</p>
        </div>
      </motion.div>
    </div>
  )
}
