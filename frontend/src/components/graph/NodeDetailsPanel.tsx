import { motion } from 'framer-motion'

interface Node {
  id: string
  name: string
  labels: string[]
  riskScore?: number
  degree?: number
  properties?: Record<string, any>
}

interface NodeDetailsPanelProps {
  node: Node | null
  onClose: () => void
  onLoadNeighbors?: (nodeId: string) => void
}

export default function NodeDetailsPanel({ node, onClose, onLoadNeighbors }: NodeDetailsPanelProps) {
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
