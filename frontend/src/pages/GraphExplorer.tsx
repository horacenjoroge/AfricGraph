import { useState, useEffect, useRef } from 'react'
import ForceGraph3D from 'react-force-graph-3d'
import axios from 'axios'

interface Node {
  id: string
  name: string
  labels: string[]
  riskScore?: number
}

interface Link {
  source: string
  target: string
  type: string
}

export default function GraphExplorerPage() {
  const [nodes, setNodes] = useState<Node[]>([])
  const [links, setLinks] = useState<Link[]>([])
  const [selectedNode, setSelectedNode] = useState<Node | null>(null)
  const [loading, setLoading] = useState(false)
  const graphRef = useRef<any>()

  useEffect(() => {
    // Load initial graph data
    loadGraphData()
  }, [])

  const loadGraphData = async () => {
    setLoading(true)
    try {
      // Fetch graph data from API
      // For now, using mock data structure
      // Replace with actual API call: /api/v1/graph/subgraph/{node_id}
      const mockNodes: Node[] = [
        { id: '1', name: 'Business A', labels: ['Business'], riskScore: 75 },
        { id: '2', name: 'Business B', labels: ['Business'], riskScore: 45 },
        { id: '3', name: 'Person X', labels: ['Person'] },
      ]
      const mockLinks: Link[] = [
        { source: '1', target: '2', type: 'SUPPLIED_BY' },
        { source: '3', target: '1', type: 'OWNS' },
      ]
      setNodes(mockNodes)
      setLinks(mockLinks)
    } catch (error) {
      console.error('Failed to load graph:', error)
    } finally {
      setLoading(false)
    }
  }

  const getNodeColor = (node: Node) => {
    if (node.riskScore !== undefined) {
      if (node.riskScore >= 80) return '#EF4444' // Red - high risk
      if (node.riskScore >= 60) return '#F59E0B' // Yellow - medium risk
      return '#10B981' // Green - low risk
    }
    return '#3B82F6' // Blue - default
  }

  const getNodeSize = (node: Node) => {
    if (node.riskScore !== undefined && node.riskScore >= 80) {
      return 8 // Larger for high-risk nodes
    }
    return 5
  }

  return (
    <div className="h-screen flex flex-col">
      <div className="p-6 border-b border-glass-border">
        <h1 className="text-3xl font-bold font-mono mb-2">Graph Explorer</h1>
        <p className="text-gray-400">Interactive knowledge graph visualization</p>
      </div>

      <div className="flex-1 relative">
        {loading ? (
          <div className="absolute inset-0 flex items-center justify-center text-gray-400">
            Loading graph...
          </div>
        ) : (
          <ForceGraph3D
            ref={graphRef}
            graphData={{ nodes, links }}
            nodeLabel={(node: any) => `${node.name}${node.riskScore ? ` (Risk: ${node.riskScore})` : ''}`}
            nodeColor={(node: any) => getNodeColor(node)}
            nodeVal={(node: any) => getNodeSize(node)}
            linkColor={() => 'rgba(255, 255, 255, 0.3)'}
            linkWidth={1}
            linkDirectionalArrowLength={4}
            linkDirectionalArrowRelPos={1}
            onNodeClick={(node: any) => setSelectedNode(node)}
            backgroundColor="#0A0F1E"
            showNavInfo={false}
            nodeThreeObject={(node: any) => {
              const sprite = new (window as any).THREE.Sprite(
                new (window as any).THREE.SpriteMaterial({
                  color: getNodeColor(node),
                  transparent: true,
                  opacity: 0.9,
                })
              )
              sprite.scale.set(getNodeSize(node) * 2, getNodeSize(node) * 2, 1)
              
              // Add glow effect for high-risk nodes
              if (node.riskScore >= 80) {
                const glow = new (window as any).THREE.Sprite(
                  new (window as any).THREE.SpriteMaterial({
                    color: '#EF4444',
                    transparent: true,
                    opacity: 0.3,
                  })
                )
                glow.scale.set(getNodeSize(node) * 4, getNodeSize(node) * 4, 1)
                const group = new (window as any).THREE.Group()
                group.add(glow)
                group.add(sprite)
                return group
              }
              
              return sprite
            }}
          />
        )}

        {/* Node Info Panel */}
        {selectedNode && (
          <div className="absolute top-4 right-4 glass-panel-strong rounded-lg p-6 w-80">
            <h3 className="text-xl font-bold mb-2">{selectedNode.name}</h3>
            <div className="space-y-2 text-sm">
              <div>
                <span className="text-gray-400">ID:</span>{' '}
                <span className="font-mono">{selectedNode.id}</span>
              </div>
              <div>
                <span className="text-gray-400">Labels:</span>{' '}
                {selectedNode.labels.join(', ')}
              </div>
              {selectedNode.riskScore !== undefined && (
                <div>
                  <span className="text-gray-400">Risk Score:</span>{' '}
                  <span className={`font-mono ${
                    selectedNode.riskScore >= 80 ? 'text-red-400' :
                    selectedNode.riskScore >= 60 ? 'text-yellow-400' :
                    'text-green-400'
                  }`}>
                    {selectedNode.riskScore}
                  </span>
                </div>
              )}
            </div>
            <button
              onClick={() => setSelectedNode(null)}
              className="mt-4 px-4 py-2 bg-red-500/20 text-red-400 rounded-lg hover:bg-red-500/30 transition-colors"
            >
              Close
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
