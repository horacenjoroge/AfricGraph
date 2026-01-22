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

export default function DashboardPage() {
  const [kpis, setKpis] = useState<KPI[]>([])
  const [recentAlerts, setRecentAlerts] = useState<any[]>([])

  useEffect(() => {
    // Fetch KPIs
    const fetchKPIs = async () => {
      try {
        // Mock data for now - replace with actual API calls
        setKpis([
          { label: 'Total Businesses', value: '1,234', change: '+12%', color: 'cyan' },
          { label: 'High Risk', value: '89', change: '-5%', color: 'red' },
          { label: 'Fraud Alerts', value: '23', change: '+3', color: 'purple' },
          { label: 'Pending Workflows', value: '15', change: '+2', color: 'green' },
        ])
      } catch (error) {
        console.error('Failed to fetch KPIs:', error)
      }
    }

    fetchKPIs()
  }, [])

  return (
    <div className="space-y-6">
      <div className="mb-8">
        <h1 className="text-4xl font-bold font-mono mb-2 text-glow-cyan tracking-tight">
          DASHBOARD
        </h1>
        <p className="text-gray-500 font-mono text-sm">REAL-TIME INTELLIGENCE OVERVIEW</p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {kpis.map((kpi, index) => (
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
        ))}
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
          <h2 className="text-lg font-bold font-mono mb-6 text-glow-cyan uppercase tracking-wider">
            Recent Alerts
          </h2>
          <div className="space-y-2">
            {recentAlerts.length === 0 ? (
              <p className="text-gray-500 text-xs font-mono">NO RECENT ALERTS</p>
            ) : (
              recentAlerts.map((alert, idx) => (
                <motion.div
                  key={alert.id}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: idx * 0.1 }}
                  className="border-l-2 border-glow-red/50 pl-3 py-2 hover:border-glow-red transition-colors"
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
