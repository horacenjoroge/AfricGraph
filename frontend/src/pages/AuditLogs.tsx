import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import axios from 'axios'

interface AuditLog {
  id: number
  created_at: string
  event_type: string
  action: string
  actor_id?: string
  resource_type?: string
  resource_id?: string
  outcome: string
}

export default function AuditLogsPage() {
  const [logs, setLogs] = useState<AuditLog[]>([])
  const [loading, setLoading] = useState(false)
  const [filters, setFilters] = useState({
    event_type: '',
    action: '',
    actor_id: '',
    resource_type: '',
    limit: 100,
    offset: 0,
  })

  useEffect(() => {
    fetchLogs()
  }, [filters])

  const fetchLogs = async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams()
      Object.entries(filters).forEach(([key, value]) => {
        if (value) params.append(key, value.toString())
      })
      
      const response = await axios.get(`/api/v1/audit?${params}`)
      setLogs(response.data.items || [])
    } catch (error) {
      console.error('Failed to fetch audit logs:', error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold font-mono mb-2">Audit Logs</h1>
        <p className="text-gray-400">System activity and access logs</p>
      </div>

      {/* Filters */}
      <div className="glass-panel rounded-lg p-6">
        <h2 className="text-xl font-bold mb-4">Filters</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm font-medium mb-2">Event Type</label>
            <input
              type="text"
              value={filters.event_type}
              onChange={(e) => setFilters({ ...filters, event_type: e.target.value })}
              placeholder="Filter by event type..."
              className="w-full px-4 py-2 bg-deep-space-50 border border-glass-border rounded-lg focus:outline-none focus:ring-2 focus:ring-glow-blue"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-2">Action</label>
            <input
              type="text"
              value={filters.action}
              onChange={(e) => setFilters({ ...filters, action: e.target.value })}
              placeholder="Filter by action..."
              className="w-full px-4 py-2 bg-deep-space-50 border border-glass-border rounded-lg focus:outline-none focus:ring-2 focus:ring-glow-blue"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-2">Actor ID</label>
            <input
              type="text"
              value={filters.actor_id}
              onChange={(e) => setFilters({ ...filters, actor_id: e.target.value })}
              placeholder="Filter by actor..."
              className="w-full px-4 py-2 bg-deep-space-50 border border-glass-border rounded-lg focus:outline-none focus:ring-2 focus:ring-glow-blue"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-2">Resource Type</label>
            <input
              type="text"
              value={filters.resource_type}
              onChange={(e) => setFilters({ ...filters, resource_type: e.target.value })}
              placeholder="Filter by resource..."
              className="w-full px-4 py-2 bg-deep-space-50 border border-glass-border rounded-lg focus:outline-none focus:ring-2 focus:ring-glow-blue"
            />
          </div>
        </div>
      </div>

      {/* Logs Table */}
      <div className="glass-panel rounded-lg overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-deep-space-50">
              <tr>
                <th className="px-6 py-4 text-left text-xs font-medium text-gray-400 uppercase">
                  Timestamp
                </th>
                <th className="px-6 py-4 text-left text-xs font-medium text-gray-400 uppercase">
                  Event Type
                </th>
                <th className="px-6 py-4 text-left text-xs font-medium text-gray-400 uppercase">
                  Action
                </th>
                <th className="px-6 py-4 text-left text-xs font-medium text-gray-400 uppercase">
                  Actor
                </th>
                <th className="px-6 py-4 text-left text-xs font-medium text-gray-400 uppercase">
                  Resource
                </th>
                <th className="px-6 py-4 text-left text-xs font-medium text-gray-400 uppercase">
                  Outcome
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-glass-border">
              {loading ? (
                <tr>
                  <td colSpan={6} className="px-6 py-8 text-center text-gray-400">
                    Loading logs...
                  </td>
                </tr>
              ) : logs.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-6 py-8 text-center text-gray-400">
                    No logs found
                  </td>
                </tr>
              ) : (
                logs.map((log, index) => (
                  <motion.tr
                    key={log.id}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: index * 0.02 }}
                    className="hover:bg-glass transition-colors"
                  >
                    <td className="px-6 py-4 font-mono text-sm text-gray-400">
                      {new Date(log.created_at).toLocaleString()}
                    </td>
                    <td className="px-6 py-4">{log.event_type}</td>
                    <td className="px-6 py-4">{log.action}</td>
                    <td className="px-6 py-4 font-mono text-sm">
                      {log.actor_id || '-'}
                    </td>
                    <td className="px-6 py-4">
                      {log.resource_type && log.resource_id ? (
                        <span className="font-mono text-sm">
                          {log.resource_type}:{log.resource_id}
                        </span>
                      ) : (
                        '-'
                      )}
                    </td>
                    <td className="px-6 py-4">
                      <span className={`px-2 py-1 rounded text-xs ${
                        log.outcome === 'allowed' ? 'bg-green-500/20 text-green-400' :
                        log.outcome === 'denied' ? 'bg-red-500/20 text-red-400' :
                        'bg-gray-500/20 text-gray-400'
                      }`}>
                        {log.outcome}
                      </span>
                    </td>
                  </motion.tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
