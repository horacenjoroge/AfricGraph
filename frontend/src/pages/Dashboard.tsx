import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import axios from 'axios'

interface KPI {
  label: string
  value: string | number
  change?: string
  icon: string
  color: 'blue' | 'green' | 'red' | 'purple'
}

export default function DashboardPage() {
  const [kpis, setKpis] = useState<KPI[]>([])
  const [recentAlerts, setRecentAlerts] = useState<any[]>([])

  useEffect(() => {
    // Fetch KPIs
    const fetchKPIs = async () => {
      try {
        // Mock data for now - replace with actual API calls
        setKpis([
          { label: 'Total Businesses', value: '1,234', change: '+12%', icon: '🏢', color: 'blue' },
          { label: 'High Risk', value: '89', change: '-5%', icon: '⚠️', color: 'red' },
          { label: 'Fraud Alerts', value: '23', change: '+3', icon: '🚨', color: 'purple' },
          { label: 'Pending Workflows', value: '15', change: '+2', icon: '📋', color: 'green' },
        ])
      } catch (error) {
        console.error('Failed to fetch KPIs:', error)
      }
    }

    fetchKPIs()
  }, [])

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold font-mono mb-2">Dashboard</h1>
        <p className="text-gray-400">Real-time intelligence overview</p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {kpis.map((kpi, index) => (
          <motion.div
            key={kpi.label}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
            className={`glass-panel rounded-lg p-6 ${`glow-${kpi.color}`}`}
          >
            <div className="flex items-center justify-between mb-4">
              <span className="text-3xl">{kpi.icon}</span>
              {kpi.change && (
                <span className={`text-sm ${kpi.change.startsWith('+') ? 'text-green-400' : 'text-red-400'}`}>
                  {kpi.change}
                </span>
              )}
            </div>
            <div className="text-2xl font-mono font-bold mb-1">{kpi.value}</div>
            <div className="text-sm text-gray-400">{kpi.label}</div>
          </motion.div>
        ))}
      </div>

      {/* Charts and Recent Alerts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="glass-panel rounded-lg p-6">
          <h2 className="text-xl font-bold mb-4">Risk Distribution</h2>
          <div className="h-64 flex items-center justify-center text-gray-400">
            Risk chart placeholder (Recharts)
          </div>
        </div>

        <div className="glass-panel rounded-lg p-6">
          <h2 className="text-xl font-bold mb-4">Recent Alerts</h2>
          <div className="space-y-3">
            {recentAlerts.length === 0 ? (
              <p className="text-gray-400 text-sm">No recent alerts</p>
            ) : (
              recentAlerts.map((alert) => (
                <div key={alert.id} className="border-b border-glass-border pb-3">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">{alert.title}</span>
                    <span className="text-xs text-gray-400">{alert.time}</span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
