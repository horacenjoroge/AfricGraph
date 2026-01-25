import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import axios from 'axios'

interface KPI {
  label: string
  value: string | number
  change?: string
  color: 'cyan' | 'blue' | 'green' | 'red' | 'purple'
}

interface Alert {
  id: string
  title: string
  time: string
  severity?: string
  business_id?: string
}

export default function DashboardPage() {
  const [kpis, setKpis] = useState<KPI[]>([])
  const [recentAlerts, setRecentAlerts] = useState<Alert[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchDashboardData()
    
    // Auto-refresh every 30 seconds
    const interval = setInterval(() => {
      fetchDashboardData()
    }, 30000)
    
    return () => clearInterval(interval)
  }, [])

  const formatNumber = (num: number): string => {
    if (num >= 1000) {
      return (num / 1000).toFixed(1) + 'K'
    }
    return num.toString()
  }

  const fetchDashboardData = async () => {
    setLoading(true)
    
    // Check if tenant is selected
    const tenantId = localStorage.getItem('current_tenant_id')
    if (!tenantId) {
      console.warn('No tenant selected - data may not be visible')
      setKpis([
        { 
          label: 'Total Businesses', 
          value: '0', 
          change: undefined,
          color: 'cyan' 
        },
        { 
          label: 'High Risk', 
          value: '0', 
          change: undefined,
          color: 'red' 
        },
        { 
          label: 'Total Transactions', 
          value: '0', 
          change: undefined,
          color: 'blue' 
        },
        { 
          label: 'Active Alerts', 
          value: '0', 
          change: undefined,
          color: 'purple' 
        },
      ])
      setRecentAlerts([])
      setLoading(false)
      return
    }
    
    try {
      // Fetch all data in parallel with tenant header
      const [businessesRes, alertsRes, fraudAlertsRes, transactionsRes] = await Promise.allSettled([
        axios.get('/api/v1/businesses/search', { 
          params: { limit: 1 },
          headers: { 'X-Tenant-ID': tenantId }
        }),
        axios.get('/alerts', { 
          params: { limit: 10, status: 'active' },
          headers: { 'X-Tenant-ID': tenantId }
        }),
        axios.get('/api/v1/fraud/alerts', { 
          params: { limit: 10, status: 'pending' },
          headers: { 'X-Tenant-ID': tenantId }
        }),
        axios.get('/api/v1/graph/transactions', { 
          params: { limit: 1 },
          headers: { 'X-Tenant-ID': tenantId }
        }),
      ])

      // Extract data from responses
      const totalBusinesses = businessesRes.status === 'fulfilled' 
        ? businessesRes.value.data.total || 0 
        : 0

      const alertsData = alertsRes.status === 'fulfilled' 
        ? alertsRes.value.data.alerts || [] 
        : []

      const fraudAlertsData = fraudAlertsRes.status === 'fulfilled' 
        ? fraudAlertsRes.value.data.items || [] 
        : []

      const totalTransactions = transactionsRes.status === 'fulfilled'
        ? transactionsRes.value.data.total || 0
        : 0

      // Count high-risk businesses (businesses with risk score > 70)
      // For now, we'll estimate based on alerts or use a placeholder
      // In a real implementation, you'd query businesses with risk scores
      const highRiskCount = alertsData.filter((a: any) => 
        a.severity === 'critical' || a.severity === 'high'
      ).length

      // Combine all alerts and sort by timestamp
      const allAlerts = [
        ...alertsData.map((a: any) => ({
          id: a.id || a.alert_id || String(Math.random()),
          title: a.title || a.message || a.description || 'Alert',
          time: a.created_at || a.timestamp || new Date().toISOString(),
          severity: a.severity,
          business_id: a.business_id,
        })),
        ...fraudAlertsData.map((a: any) => ({
          id: a.id || a.alert_id || String(Math.random()),
          title: a.title || a.message || `Fraud Alert: ${a.business_id || 'Unknown'}`,
          time: a.created_at || a.timestamp || new Date().toISOString(),
          severity: 'high',
          business_id: a.business_id,
        })),
      ]
        .sort((a, b) => new Date(b.time).getTime() - new Date(a.time).getTime())
        .slice(0, 10)
        .map((alert) => ({
          ...alert,
          time: new Date(alert.time).toLocaleDateString('en-US', {
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
          }),
        }))

      // Calculate changes (placeholder - in production, compare with previous period)
      const totalAlerts = alertsData.length + fraudAlertsData.length

      setKpis([
        { 
          label: 'Total Businesses', 
          value: formatNumber(totalBusinesses), 
          change: undefined, // Could calculate from historical data
          color: 'cyan' 
        },
        { 
          label: 'High Risk', 
          value: highRiskCount || 'N/A', 
          change: undefined,
          color: 'red' 
        },
        { 
          label: 'Fraud Alerts', 
          value: totalAlerts, 
          change: undefined,
          color: 'purple' 
        },
        { 
          label: 'Total Transactions', 
          value: formatNumber(totalTransactions), 
          change: undefined,
          color: 'green' 
        },
      ])

      setRecentAlerts(allAlerts)
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error)
      // Set default values on error
      setKpis([
        { label: 'Total Businesses', value: '0', color: 'cyan' },
        { label: 'High Risk', value: '0', color: 'red' },
        { label: 'Fraud Alerts', value: '0', color: 'purple' },
        { label: 'Total Transactions', value: '0', color: 'green' },
      ])
    } finally {
      setLoading(false)
    }
  }

  const tenantId = localStorage.getItem('current_tenant_id')

  return (
    <div className="space-y-6">
      {!tenantId && (
        <div className="glass-panel border border-yellow-500/30 bg-yellow-500/10 p-4 rounded-lg">
          <div className="flex items-center gap-3">
            <div className="text-yellow-400 text-xl">⚠️</div>
            <div>
              <div className="text-yellow-400 font-mono font-semibold mb-1">No Tenant Selected</div>
              <div className="text-gray-400 text-sm">
                Select a tenant from the dropdown in the top-right corner to view your data.
              </div>
            </div>
          </div>
        </div>
      )}
      
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-4xl font-bold font-mono mb-2 text-glow-cyan tracking-tight">
            DASHBOARD
          </h1>
          <p className="text-gray-500 font-mono text-sm">REAL-TIME INTELLIGENCE OVERVIEW</p>
        </div>
        <button
          onClick={fetchDashboardData}
          disabled={loading}
          className="px-4 py-2 glass-panel border border-glow-cyan/20 hover:border-glow-cyan/40 transition-all text-sm font-mono uppercase tracking-wider disabled:opacity-50"
        >
          {loading ? 'LOADING...' : 'REFRESH'}
        </button>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {loading && kpis.length === 0 ? (
          // Loading skeleton
          Array.from({ length: 4 }).map((_, index) => (
            <div
              key={index}
              className="glass-panel p-6 border border-glass-border animate-pulse"
            >
              <div className="h-8 bg-gray-700/20 rounded mb-4" />
              <div className="h-10 bg-gray-700/20 rounded mb-2" />
              <div className="h-4 bg-gray-700/20 rounded w-2/3" />
            </div>
          ))
        ) : (
          kpis.map((kpi, index) => (
            <motion.div
              key={kpi.label}
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: index * 0.08, type: "spring", stiffness: 200 }}
              className={`glass-panel p-6 border border-glow-${kpi.color}/20 hover:border-glow-${kpi.color}/40 transition-all`}
            >
              <div className="flex items-center justify-between mb-4">
                <div className={`w-1 h-8 bg-glow-${kpi.color} rounded-full`} />
                {kpi.change && (
                  <span className={`text-xs font-mono ${kpi.change.startsWith('+') ? 'text-glow-green' : 'text-glow-red'}`}>
                    {kpi.change}
                  </span>
                )}
              </div>
              <div className={`text-3xl font-mono font-bold mb-2 data-value text-glow-${kpi.color}`}>
                {kpi.value}
              </div>
              <div className="text-xs text-gray-500 font-mono uppercase tracking-wider">{kpi.label}</div>
            </motion.div>
          ))
        )}
      </div>

      {/* Charts and Recent Alerts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mt-6">
        <div className="glass-panel p-6 border border-glass-border">
          <h2 className="text-lg font-bold font-mono mb-6 text-glow-cyan uppercase tracking-wider">
            Risk Distribution
          </h2>
          <div className="h-64 flex items-center justify-center">
            <div className="text-gray-500 font-mono text-sm">
              [RADAR CHART PLACEHOLDER]
            </div>
          </div>
        </div>

        <div className="glass-panel p-6 border border-glass-border">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-lg font-bold font-mono text-glow-cyan uppercase tracking-wider">
              Recent Alerts
            </h2>
            {recentAlerts.length > 0 && (
              <Link
                to="/fraud"
                className="text-xs font-mono text-glow-cyan hover:text-glow-cyan/80 transition-colors"
              >
                VIEW ALL →
              </Link>
            )}
          </div>
          <div className="space-y-2">
            {loading && recentAlerts.length === 0 ? (
              <div className="space-y-2">
                {Array.from({ length: 3 }).map((_, idx) => (
                  <div key={idx} className="border-l-2 border-glass-border pl-3 py-2 animate-pulse">
                    <div className="h-4 bg-gray-700/20 rounded mb-1" />
                    <div className="h-3 bg-gray-700/20 rounded w-1/3" />
                  </div>
                ))}
              </div>
            ) : recentAlerts.length === 0 ? (
              <p className="text-gray-500 text-xs font-mono">NO RECENT ALERTS</p>
            ) : (
              recentAlerts.map((alert, idx) => (
                <motion.div
                  key={alert.id}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: idx * 0.1 }}
                  className={`border-l-2 pl-3 py-2 hover:opacity-80 transition-colors cursor-pointer ${
                    alert.severity === 'critical' || alert.severity === 'high'
                      ? 'border-glow-red/50 hover:border-glow-red'
                      : 'border-glow-yellow/50 hover:border-glow-yellow'
                  }`}
                  onClick={() => alert.business_id && (window.location.href = `/businesses/${alert.business_id}`)}
                >
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-mono data-value">{alert.title}</span>
                    <span className="text-xs text-gray-500 font-mono">{alert.time}</span>
                  </div>
                </motion.div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
