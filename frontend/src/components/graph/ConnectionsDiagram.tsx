import { motion } from 'framer-motion'
import { useState } from 'react'

interface Connection {
  id: string
  name: string
  labels: string[]
  properties?: Record<string, any>
  relationship_type: string
  relationship_properties?: Record<string, any>
}

interface Node {
  id: string
  name: string
  labels: string[]
  riskScore?: number
  properties?: Record<string, any>
}

interface ConnectionsDiagramProps {
  node: Node | null
  connections: Connection[]
  onClose: () => void
  onExport?: (format: 'pdf' | 'docx') => void
}

export default function ConnectionsDiagram({
  node,
  connections,
  onClose,
  onExport,
}: ConnectionsDiagramProps) {
  const [viewMode, setViewMode] = useState<'diagram' | 'list'>('diagram')
  const [expandedConnections, setExpandedConnections] = useState<Set<string>>(new Set())

  if (!node) return null

  const toggleConnection = (connId: string) => {
    const newExpanded = new Set(expandedConnections)
    if (newExpanded.has(connId)) {
      newExpanded.delete(connId)
    } else {
      newExpanded.add(connId)
    }
    setExpandedConnections(newExpanded)
  }

  // Group connections by relationship type
  const connectionsByType = connections.reduce((acc, conn) => {
    const type = conn.relationship_type || 'UNKNOWN'
    if (!acc[type]) {
      acc[type] = []
    }
    acc[type].push(conn)
    return acc
  }, {} as Record<string, Connection[]>)

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.95 }}
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm"
      onClick={(e) => {
        if (e.target === e.currentTarget) {
          onClose()
        }
      }}
    >
      <motion.div
        initial={{ y: 20 }}
        animate={{ y: 0 }}
        className="glass-panel-strong rounded-lg p-6 w-[90vw] max-w-6xl max-h-[90vh] overflow-hidden flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between mb-6 pb-4 border-b border-glass-border">
          <div>
            <h2 className="text-2xl font-bold font-mono mb-1">{node.name}</h2>
            <p className="text-sm text-gray-400">
              {connections.length} connection{connections.length !== 1 ? 's' : ''} • {node.labels.join(', ')}
            </p>
          </div>
          <div className="flex items-center gap-3">
            {/* View Mode Toggle */}
            <div className="flex items-center gap-2 bg-deep-space-50 rounded-lg p-1">
              <button
                onClick={() => setViewMode('diagram')}
                className={`px-3 py-1.5 text-sm rounded transition-colors ${
                  viewMode === 'diagram'
                    ? 'bg-blue-500/30 text-blue-400'
                    : 'text-gray-400 hover:text-gray-200'
                }`}
              >
                Diagram
              </button>
              <button
                onClick={() => setViewMode('list')}
                className={`px-3 py-1.5 text-sm rounded transition-colors ${
                  viewMode === 'list'
                    ? 'bg-blue-500/30 text-blue-400'
                    : 'text-gray-400 hover:text-gray-200'
                }`}
              >
                List
              </button>
            </div>

            {/* Export Buttons */}
            {onExport && (
              <div className="flex items-center gap-2">
                <button
                  onClick={() => onExport('pdf')}
                  className="px-4 py-2 bg-green-500/20 text-green-400 rounded-lg hover:bg-green-500/30 transition-colors text-sm"
                >
                  PDF
                </button>
                <button
                  onClick={() => onExport('docx')}
                  className="px-4 py-2 bg-blue-500/20 text-blue-400 rounded-lg hover:bg-blue-500/30 transition-colors text-sm"
                >
                  DOCX
                </button>
              </div>
            )}

            <button
              onClick={onClose}
              className="text-gray-400 hover:text-white transition-colors text-2xl"
            >
              ✕
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto">
          {viewMode === 'diagram' ? (
            <DiagramView
              node={node}
              connectionsByType={connectionsByType}
              expandedConnections={expandedConnections}
              onToggleConnection={toggleConnection}
            />
          ) : (
            <ListView
              connectionsByType={connectionsByType}
              expandedConnections={expandedConnections}
              onToggleConnection={toggleConnection}
            />
          )}
        </div>
      </motion.div>
    </motion.div>
  )
}

function DiagramView({
  node,
  connectionsByType,
  expandedConnections,
  onToggleConnection,
}: {
  node: Node
  connectionsByType: Record<string, Connection[]>
  expandedConnections: Set<string>
  onToggleConnection: (id: string) => void
}) {
  return (
    <div className="space-y-6">
      {/* Center Node */}
      <div className="flex justify-center mb-8">
        <div className="glass-panel border-2 border-cyan-400 rounded-lg p-6 text-center max-w-md">
          <h3 className="text-xl font-bold font-mono text-cyan-400 mb-2">{node.name}</h3>
          <div className="flex flex-wrap gap-2 justify-center mb-3">
            {node.labels.map((label) => (
              <span
                key={label}
                className="px-2 py-1 bg-cyan-500/20 text-cyan-400 rounded text-xs"
              >
                {label}
              </span>
            ))}
          </div>
          {node.riskScore !== undefined && (
            <div className="mt-3 pt-3 border-t border-glass-border">
              <div className="text-sm text-gray-400">Risk Score</div>
              <div
                className={`text-2xl font-bold font-mono ${
                  node.riskScore >= 80
                    ? 'text-red-400'
                    : node.riskScore >= 60
                    ? 'text-yellow-400'
                    : 'text-green-400'
                }`}
              >
                {node.riskScore}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Connections by Type */}
      {Object.entries(connectionsByType).map(([relType, conns]) => (
        <div key={relType} className="space-y-3">
          <div className="flex items-center gap-3">
            <div className="h-px flex-1 bg-gradient-to-r from-transparent via-glass-border to-transparent" />
            <h4 className="text-lg font-bold font-mono text-glow-cyan px-4">
              {relType} ({conns.length})
            </h4>
            <div className="h-px flex-1 bg-gradient-to-r from-transparent via-glass-border to-transparent" />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {conns.map((conn) => {
              const isExpanded = expandedConnections.has(conn.id)
              return (
                <motion.div
                  key={conn.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="glass-panel border border-green-500/30 rounded-lg p-4 cursor-pointer hover:border-green-500/50 transition-colors"
                  onClick={() => onToggleConnection(conn.id)}
                >
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex-1">
                      <div className="font-medium text-green-400 mb-1">{conn.name || conn.id}</div>
                      <div className="flex flex-wrap gap-1">
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
                    <div className="text-xs text-gray-500 ml-2">
                      {isExpanded ? '▼' : '▶'}
                    </div>
                  </div>

                  {isExpanded && conn.relationship_properties && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: 'auto', opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      className="mt-3 pt-3 border-t border-glass-border space-y-1 text-xs"
                    >
                      {Object.entries(conn.relationship_properties).map(([key, value]) => (
                        <div key={key} className="flex justify-between">
                          <span className="text-gray-400">{key}:</span>
                          <span className="font-mono text-gray-300">{String(value)}</span>
                        </div>
                      ))}
                    </motion.div>
                  )}
                </motion.div>
              )
            })}
          </div>
        </div>
      ))}
    </div>
  )
}

function ListView({
  connectionsByType,
  expandedConnections,
  onToggleConnection,
}: {
  connectionsByType: Record<string, Connection[]>
  expandedConnections: Set<string>
  onToggleConnection: (id: string) => void
}) {
  return (
    <div className="space-y-4">
      {Object.entries(connectionsByType).map(([relType, conns]) => (
        <div key={relType} className="space-y-2">
          <h4 className="text-lg font-bold font-mono text-glow-cyan mb-3">
            {relType} ({conns.length})
          </h4>
          <div className="space-y-2">
            {conns.map((conn) => {
              const isExpanded = expandedConnections.has(conn.id)
              return (
                <motion.div
                  key={conn.id}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="glass-panel border border-green-500/20 rounded-lg p-4 cursor-pointer hover:border-green-500/40 transition-colors"
                  onClick={() => onToggleConnection(conn.id)}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="font-medium text-green-400 mb-2">{conn.name || conn.id}</div>
                      <div className="flex flex-wrap gap-2 mb-2">
                        {conn.labels.map((label) => (
                          <span
                            key={label}
                            className="px-2 py-1 bg-green-500/20 text-green-400 rounded text-xs"
                          >
                            {label}
                          </span>
                        ))}
                      </div>
                      {isExpanded && (
                        <motion.div
                          initial={{ height: 0, opacity: 0 }}
                          animate={{ height: 'auto', opacity: 1 }}
                          className="mt-3 pt-3 border-t border-glass-border space-y-2 text-sm"
                        >
                          {conn.relationship_properties && Object.keys(conn.relationship_properties).length > 0 && (
                            <div>
                              <div className="text-xs text-gray-400 mb-1">Relationship Properties:</div>
                              <div className="space-y-1">
                                {Object.entries(conn.relationship_properties).map(([key, value]) => (
                                  <div key={key} className="flex justify-between text-xs">
                                    <span className="text-gray-400">{key}:</span>
                                    <span className="font-mono text-gray-300">{String(value)}</span>
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}
                          {conn.properties && Object.keys(conn.properties).length > 0 && (
                            <div>
                              <div className="text-xs text-gray-400 mb-1">Node Properties:</div>
                              <div className="space-y-1">
                                {Object.entries(conn.properties).map(([key, value]) => (
                                  <div key={key} className="flex justify-between text-xs">
                                    <span className="text-gray-400">{key}:</span>
                                    <span className="font-mono text-gray-300 max-w-[60%] truncate">
                                      {String(value)}
                                    </span>
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}
                        </motion.div>
                      )}
                    </div>
                    <div className="text-gray-500 ml-4">
                      {isExpanded ? '▼' : '▶'}
                    </div>
                  </div>
                </motion.div>
              )
            })}
          </div>
        </div>
      ))}
    </div>
  )
}
