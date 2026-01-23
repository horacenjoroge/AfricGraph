import { motion } from 'framer-motion'
import { useState, useEffect } from 'react'
import axios from 'axios'

interface Node {
  id: string
  name: string
  labels: string[]
  riskScore?: number
  degree?: number
  properties?: Record<string, any>
}

interface Owner {
  id: string
  name: string
  labels: string[]
  properties?: Record<string, any>
  ownership_percentage?: number
}

interface Connection {
  id: string
  name: string
  labels: string[]
  properties?: Record<string, any>
  relationship_type: string
  relationship_properties?: Record<string, any>
}

interface NodeDetailsPanelProps {
  node: Node | null
  onClose: () => void
  onLoadNeighbors?: (nodeId: string) => void
}

export default function NodeDetailsPanel({ node, onClose, onLoadNeighbors }: NodeDetailsPanelProps) {
  const [details, setDetails] = useState<{ owners: Owner[]; connections: Connection[] } | null>(null)
  const [loadingDetails, setLoadingDetails] = useState(false)

  useEffect(() => {
    if (node) {
      setLoadingDetails(true)
      axios
        .get(`/api/v1/graph/node/${node.id}/details`)
        .then((response) => {
          setDetails({
            owners: response.data.owners || [],
            connections: response.data.connections || [],
          })
        })
        .catch((error) => {
          console.error('Failed to load node details:', error)
          setDetails({ owners: [], connections: [] })
        })
        .finally(() => {
          setLoadingDetails(false)
        })
    } else {
      setDetails(null)
    }
  }, [node])

  if (!node) return null

  return (
    <motion.div
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: 20 }}
      className="absolute top-4 right-4 glass-panel-strong rounded-lg p-6 w-80 max-h-[80vh] overflow-y-auto"
    >
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-xl font-bold">{node.name}</h3>
        <button
          onClick={onClose}
          className="text-gray-400 hover:text-white transition-colors"
        >
          ✕
        </button>
      </div>

      <div className="space-y-4">
        {/* Basic Info */}
        <div>
          <h4 className="text-sm font-medium text-gray-400 mb-2">Information</h4>
          <div className="space-y-2 text-sm">
            <div>
              <span className="text-gray-400">ID:</span>{' '}
              <span className="font-mono">{node.id}</span>
            </div>
            <div>
              <span className="text-gray-400">Labels:</span>{' '}
              <div className="flex flex-wrap gap-1 mt-1">
                {node.labels.map((label) => (
                  <span
                    key={label}
                    className="px-2 py-1 bg-blue-500/20 text-blue-400 rounded text-xs"
                  >
                    {label}
                  </span>
                ))}
              </div>
            </div>
            {node.degree !== undefined && (
              <div>
                <span className="text-gray-400">Connections:</span>{' '}
                <span className="font-mono">{node.degree}</span>
              </div>
            )}
          </div>
        </div>

        {/* Risk Score */}
        {node.riskScore !== undefined && (
          <div>
            <h4 className="text-sm font-medium text-gray-400 mb-2">Risk Assessment</h4>
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm">Risk Score</span>
                <span
                  className={`font-mono font-bold text-lg ${
                    node.riskScore >= 80
                      ? 'text-red-400 glow-red'
                      : node.riskScore >= 60
                      ? 'text-yellow-400'
                      : 'text-green-400 glow-green'
                  }`}
                >
                  {node.riskScore}
                </span>
              </div>
              <div className="w-full bg-deep-space-50 rounded-full h-2">
                <div
                  className={`h-2 rounded-full ${
                    node.riskScore >= 80
                      ? 'bg-red-400'
                      : node.riskScore >= 60
                      ? 'bg-yellow-400'
                      : 'bg-green-400'
                  }`}
                  style={{ width: `${node.riskScore}%` }}
                />
              </div>
              <div className="text-xs text-gray-400">
                {node.riskScore >= 80
                  ? 'High Risk - Requires immediate attention'
                  : node.riskScore >= 60
                  ? 'Medium Risk - Monitor closely'
                  : 'Low Risk - Normal operations'}
              </div>
            </div>
          </div>
        )}

        {/* Owners */}
        {node.labels.includes('Business') && (
          <div>
            <h4 className="text-sm font-medium text-gray-400 mb-2">
              Owners ({loadingDetails ? '...' : details?.owners.length || 0})
            </h4>
            {loadingDetails ? (
              <div className="text-xs text-gray-500">Loading owners...</div>
            ) : details && details.owners.length > 0 ? (
              <div className="space-y-2 text-sm">
                {details.owners.map((owner) => (
                  <div
                    key={owner.id}
                    className="p-2 bg-blue-500/10 rounded border border-blue-500/20"
                  >
                    <div className="font-medium">{owner.name || owner.id}</div>
                    {owner.ownership_percentage !== null && owner.ownership_percentage !== undefined && (
                      <div className="text-xs text-gray-400">
                        Ownership: {owner.ownership_percentage}%
                      </div>
                    )}
                    <div className="flex flex-wrap gap-1 mt-1">
                      {owner.labels.map((label) => (
                        <span
                          key={label}
                          className="px-1.5 py-0.5 bg-blue-500/20 text-blue-400 rounded text-xs"
                        >
                          {label}
                        </span>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-xs text-gray-500">No owners found</div>
            )}
          </div>
        )}

        {/* Connections */}
        <div>
          <h4 className="text-sm font-medium text-gray-400 mb-2">
            Connections ({loadingDetails ? '...' : details?.connections.length || 0})
          </h4>
          {loadingDetails ? (
            <div className="text-xs text-gray-500">Loading connections...</div>
          ) : details && details.connections.length > 0 ? (
            <div className="space-y-2 text-sm max-h-48 overflow-y-auto">
              {details.connections.slice(0, 10).map((conn) => (
                <div
                  key={conn.id}
                  className="p-2 bg-green-500/10 rounded border border-green-500/20"
                >
                  <div className="font-medium">{conn.name || conn.id}</div>
                  <div className="text-xs text-gray-400 mt-1">
                    <span className="px-1.5 py-0.5 bg-green-500/20 text-green-400 rounded">
                      {conn.relationship_type}
                    </span>
                  </div>
                  <div className="flex flex-wrap gap-1 mt-1">
                    {conn.labels.map((label) => (
                      <span
                        key={label}
                        className="px-1.5 py-0.5 bg-green-500/20 text-green-400 rounded text-xs"
                      >
                        {label}
                      </span>
                    ))}
                  </div>
                </div>
              ))}
              {details.connections.length > 10 && (
                <div className="text-xs text-gray-500 text-center">
                  +{details.connections.length - 10} more connections
                </div>
              )}
            </div>
          ) : (
            <div className="text-xs text-gray-500">No connections found</div>
          )}
        </div>

        {/* Properties */}
        {node.properties && Object.keys(node.properties).length > 0 && (
          <div>
            <h4 className="text-sm font-medium text-gray-400 mb-2">Properties</h4>
            <div className="space-y-1 text-sm">
              {Object.entries(node.properties).map(([key, value]) => (
                <div key={key} className="flex justify-between">
                  <span className="text-gray-400">{key}:</span>
                  <span className="font-mono text-right max-w-[60%] truncate">
                    {String(value)}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Actions */}
        <div className="pt-4 border-t border-glass-border space-y-2">
          {onLoadNeighbors && (
            <button
              onClick={() => onLoadNeighbors(node.id)}
              className="w-full px-4 py-2 bg-blue-500/20 text-blue-400 rounded-lg hover:bg-blue-500/30 transition-colors text-sm"
            >
              Load Neighbors
            </button>
          )}
          <button
            onClick={onClose}
            className="w-full px-4 py-2 bg-red-500/20 text-red-400 rounded-lg hover:bg-red-500/30 transition-colors text-sm"
          >
            Close
          </button>
        </div>
      </div>
    </motion.div>
  )
}
