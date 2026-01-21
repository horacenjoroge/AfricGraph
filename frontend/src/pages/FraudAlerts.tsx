import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import axios from 'axios'
import { io, Socket } from 'socket.io-client'

interface FraudAlert {
  id: string
  business_id: string
  pattern_type: string
  severity: 'low' | 'medium' | 'high' | 'critical'
  score: number
  created_at: string
  status: 'new' | 'acknowledged' | 'resolved'
}

export default function FraudAlertsPage() {
  const [alerts, setAlerts] = useState<FraudAlert[]>([])
  const [socket, setSocket] = useState<Socket | null>(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    fetchAlerts()
    
    // Setup WebSocket connection for real-time updates
    const newSocket = io('http://localhost:8000', {
      path: '/ws',
      transports: ['websocket'],
    })
    
    newSocket.on('fraud_alert', (alert: FraudAlert) => {
      setAlerts((prev) => [alert, ...prev])
    })
    
    setSocket(newSocket)
    
    return () => {
      newSocket.close()
    }
  }, [])

  const fetchAlerts = async () => {
    setLoading(true)
    try {
      const response = await axios.get('/api/v1/fraud/alerts')
      setAlerts(response.data.alerts || [])
    } catch (error) {
      console.error('Failed to fetch alerts:', error)
    } finally {
      setLoading(false)
    }
  }

  const acknowledgeAlert = async (alertId: string) => {
    try {
      await axios.post(`/api/v1/fraud/alerts/${alertId}/acknowledge`)
      setAlerts((prev) =>
        prev.map((alert) =>
          alert.id === alertId ? { ...alert, status: 'acknowledged' } : alert
        )
      )
    } catch (error) {
      console.error('Failed to acknowledge alert:', error)
    }
  }

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical':
        return 'text-red-400 glow-red'
      case 'high':
        return 'text-orange-400'
      case 'medium':
        return 'text-yellow-400'
      case 'low':
        return 'text-green-400'
      default:
        return 'text-gray-400'
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold font-mono mb-2">Fraud Alerts</h1>
        <p className="text-gray-400">Real-time fraud pattern detection</p>
      </div>

      <div className="glass-panel rounded-lg overflow-hidden">
        <div className="p-6 border-b border-glass-border">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-bold">Active Alerts</h2>
            <button
              onClick={fetchAlerts}
              className="px-4 py-2 bg-blue-500/20 text-blue-400 rounded-lg hover:bg-blue-500/30 transition-colors"
            >
              Refresh
            </button>
          </div>
        </div>

        <div className="overflow-x-auto">
          <AnimatePresence>
            {loading ? (
              <div className="p-8 text-center text-gray-400">Loading alerts...</div>
            ) : alerts.length === 0 ? (
              <div className="p-8 text-center text-gray-400">No alerts</div>
            ) : (
              <table className="w-full">
                <thead className="bg-deep-space-50">
                  <tr>
                    <th className="px-6 py-4 text-left text-xs font-medium text-gray-400 uppercase">
                      Pattern
                    </th>
                    <th className="px-6 py-4 text-left text-xs font-medium text-gray-400 uppercase">
                      Severity
                    </th>
                    <th className="px-6 py-4 text-left text-xs font-medium text-gray-400 uppercase">
                      Score
                    </th>
                    <th className="px-6 py-4 text-left text-xs font-medium text-gray-400 uppercase">
                      Business ID
                    </th>
                    <th className="px-6 py-4 text-left text-xs font-medium text-gray-400 uppercase">
                      Status
                    </th>
                    <th className="px-6 py-4 text-left text-xs font-medium text-gray-400 uppercase">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-glass-border">
                  {alerts.map((alert, index) => (
                    <motion.tr
                      key={alert.id}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: index * 0.05 }}
                      className={`hover:bg-glass transition-colors ${
                        alert.status === 'new' ? 'glitch' : ''
                      }`}
                    >
                      <td className="px-6 py-4 font-medium">{alert.pattern_type}</td>
                      <td className={`px-6 py-4 font-bold uppercase ${getSeverityColor(alert.severity)}`}>
                        {alert.severity}
                      </td>
                      <td className="px-6 py-4 font-mono">{alert.score}</td>
                      <td className="px-6 py-4 font-mono text-sm text-gray-400">
                        {alert.business_id}
                      </td>
                      <td className="px-6 py-4">
                        <span className={`px-2 py-1 rounded text-xs ${
                          alert.status === 'new' ? 'bg-blue-500/20 text-blue-400' :
                          alert.status === 'acknowledged' ? 'bg-yellow-500/20 text-yellow-400' :
                          'bg-green-500/20 text-green-400'
                        }`}>
                          {alert.status}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        {alert.status === 'new' && (
                          <button
                            onClick={() => acknowledgeAlert(alert.id)}
                            className="px-3 py-1 bg-yellow-500/20 text-yellow-400 rounded hover:bg-yellow-500/30 transition-colors text-sm"
                          >
                            Acknowledge
                          </button>
                        )}
                      </td>
                    </motion.tr>
                  ))}
                </tbody>
              </table>
            )}
          </AnimatePresence>
        </div>
      </div>
    </div>
  )
}
