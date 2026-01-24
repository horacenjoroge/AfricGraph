import { useState } from 'react'
import { motion } from 'framer-motion'
import axios from 'axios'
import { useNotifications } from '../../contexts/NotificationContext'

export default function CacheManagement() {
  const [clearing, setClearing] = useState<string | null>(null)
  const { showSuccess, showError } = useNotifications()

  const clearCache = async (cacheType: 'graph' | 'all', nodeId?: string) => {
    try {
      setClearing(cacheType)
      const token = localStorage.getItem('auth_token')
      
      let endpoint = '/api/v1/cache/invalidate/graph'
      if (cacheType === 'all') {
        endpoint = '/api/v1/cache/clear'
      } else if (nodeId) {
        endpoint = `/api/v1/cache/invalidate/graph?node_id=${nodeId}`
      }

      await axios.delete(endpoint, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      })

      showSuccess(
        cacheType === 'all'
          ? 'All cache cleared successfully'
          : 'Graph cache cleared successfully'
      )
    } catch (error: any) {
      console.error('Failed to clear cache:', error)
      showError(
        error.response?.data?.detail || 'Failed to clear cache'
      )
    } finally {
      setClearing(null)
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-xl font-bold mb-2">Cache Management</h2>
        <p className="text-sm text-gray-400">
          Clear cached data to see the latest information
        </p>
      </div>

      {/* Info Box */}
      <div className="glass-panel border border-blue-500/30 rounded-lg p-4">
        <div className="flex items-start gap-3">
          <div className="text-blue-400 text-xl">ℹ️</div>
          <div>
            <h4 className="font-medium text-gray-300 mb-1">About Cache</h4>
            <p className="text-sm text-gray-400 mb-2">
              The system caches graph queries and other data to improve performance. 
              After ingesting new data, you may need to clear the cache to see updated information.
            </p>
            <ul className="text-sm text-gray-400 space-y-1 list-disc list-inside ml-2">
              <li><strong>Graph Cache:</strong> Clears cached subgraph queries (15 min TTL)</li>
              <li><strong>Clear All:</strong> Clears all cached data (use with caution)</li>
            </ul>
          </div>
        </div>
      </div>

      {/* Cache Actions */}
      <div className="glass-panel rounded-lg p-6 space-y-4">
        <div>
          <h3 className="text-lg font-semibold mb-4">Clear Cache</h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Clear Graph Cache */}
            <motion.div
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              className="border border-glass-border rounded-lg p-4 space-y-3"
            >
              <div>
                <h4 className="font-medium text-gray-300 mb-1">
                  Graph Cache
                </h4>
                <p className="text-sm text-gray-400">
                  Clear cached subgraph queries. Use this after ingesting new data to see updated node properties.
                </p>
              </div>
              <button
                onClick={() => clearCache('graph')}
                disabled={clearing !== null}
                className="w-full px-4 py-2 bg-blue-500/20 text-blue-400 rounded-lg hover:bg-blue-500/30 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {clearing === 'graph' ? 'Clearing...' : 'Clear Graph Cache'}
              </button>
            </motion.div>

            {/* Clear All Cache */}
            <motion.div
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              className="border border-glass-border rounded-lg p-4 space-y-3"
            >
              <div>
                <h4 className="font-medium text-gray-300 mb-1">
                  All Cache
                </h4>
                <p className="text-sm text-gray-400">
                  Clear all cached data including graph, risk scores, business data, and more.
                </p>
              </div>
              <button
                onClick={() => {
                  if (window.confirm('Are you sure you want to clear all cache? This will affect performance temporarily.')) {
                    clearCache('all')
                  }
                }}
                disabled={clearing !== null}
                className="w-full px-4 py-2 bg-red-500/20 text-red-400 rounded-lg hover:bg-red-500/30 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {clearing === 'all' ? 'Clearing...' : 'Clear All Cache'}
              </button>
            </motion.div>
          </div>
        </div>
      </div>

      {/* When to Clear Cache */}
      <div className="glass-panel rounded-lg p-6">
        <h3 className="text-lg font-semibold mb-4">When to Clear Cache</h3>
        <div className="space-y-2 text-sm text-gray-400">
          <div className="flex items-start gap-2">
            <span className="text-green-400">✓</span>
            <span>
              <strong>After data ingestion:</strong> Clear graph cache to see newly ingested transactions and their properties
            </span>
          </div>
          <div className="flex items-start gap-2">
            <span className="text-green-400">✓</span>
            <span>
              <strong>After updating node properties:</strong> If you manually update node data, clear cache to see changes
            </span>
          </div>
          <div className="flex items-start gap-2">
            <span className="text-yellow-400">⚠</span>
            <span>
              <strong>Performance impact:</strong> Clearing cache will cause the next queries to be slower as they rebuild the cache
            </span>
          </div>
        </div>
      </div>
    </div>
  )
}
