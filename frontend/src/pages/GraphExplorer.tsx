import { useState, useEffect, useRef, useCallback } from 'react'
import ForceGraph3D from 'react-force-graph-3d'
import axios from 'axios'
import GraphControls, { GraphFilters } from '../components/graph/GraphControls'
import NodeDetailsPanel from '../components/graph/NodeDetailsPanel'
import {
  calculateNodeDegrees,
  filterGraph,
  getNodeColorByType,
  getNodeSizeByImportance,
} from '../utils/graphUtils'

interface Node {
  id: string
  name: string
  labels: string[]
  riskScore?: number
  degree?: number
  properties?: Record<string, any>
}

interface Link {
  source: string | Node
  target: string | Node
  type: string
}

export default function GraphExplorerPage() {
  const [allNodes, setAllNodes] = useState<Node[]>([])
  const [allLinks, setAllLinks] = useState<Link[]>([])
  const [displayNodes, setDisplayNodes] = useState<Node[]>([])
  const [displayLinks, setDisplayLinks] = useState<Link[]>([])
  const [selectedNode, setSelectedNode] = useState<Node | null>(null)
  const [loading, setLoading] = useState(false)
  const [filters, setFilters] = useState<GraphFilters>({
    nodeTypes: [],
    riskLevel: 'all',
    minRiskScore: 0,
    maxRiskScore: 100,
    showLabels: true,
  })
  const graphRef = useRef<any>()

  useEffect(() => {
    loadGraphData()
  }, [])

  useEffect(() => {
    // Recalculate degrees when nodes/links change
    const nodesWithDegrees = calculateNodeDegrees(allNodes, allLinks)
    setAllNodes(nodesWithDegrees)

    // Apply filters
    const filtered = filterGraph(nodesWithDegrees, allLinks, filters)
    setDisplayNodes(filtered.nodes)
    setDisplayLinks(filtered.links)
  }, [allNodes, allLinks, filters])

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
        { id: '4', name: 'Business C', labels: ['Business'], riskScore: 85 },
        { id: '5', name: 'Transaction T1', labels: ['Transaction'] },
      ]
      const mockLinks: Link[] = [
        { source: '1', target: '2', type: 'SUPPLIED_BY' },
        { source: '3', target: '1', type: 'OWNS' },
        { source: '1', target: '4', type: 'CONNECTED_TO' },
        { source: '1', target: '5', type: 'INVOLVES' },
        { source: '2', target: '5', type: 'INVOLVES' },
      ]
      setAllNodes(mockNodes)
      setAllLinks(mockLinks)
    } catch (error) {
      console.error('Failed to load graph:', error)
    } finally {
      setLoading(false)
    }
  }

  const loadSubgraph = async (nodeId: string, maxHops: number) => {
    setLoading(true)
    try {
      const response = await axios.get(`/api/v1/graph/subgraph/${nodeId}`, {
        params: { max_hops: maxHops, format: 'json' },
      })
      
      const subgraph = response.data
      const nodes: Node[] = subgraph.nodes.map((n: any) => ({
        id: String(n.id),
        name: n.properties?.name || n.id,
        labels: n.labels || [],
        properties: n.properties,
      }))
      
      const links: Link[] = subgraph.relationships.map((r: any) => ({
        source: r.from_id,
        target: r.to_id,
        type: r.type,
      }))
      
      setAllNodes(nodes)
      setAllLinks(links)
    } catch (error) {
      console.error('Failed to load subgraph:', error)
      alert('Failed to load subgraph. Using mock data.')
      loadGraphData()
    } finally {
      setLoading(false)
    }
  }

  const exportGraph = useCallback(() => {
    if (!graphRef.current) return
    
    // Capture screenshot using canvas
    const canvas = graphRef.current.getGraphCanvas()
    if (canvas) {
      const dataUrl = canvas.toDataURL('image/png')
      const link = document.createElement('a')
      link.download = `graph-export-${Date.now()}.png`
      link.href = dataUrl
      link.click()
    } else {
      // Fallback: use html2canvas if available
      alert('Export functionality requires canvas access. Please ensure the graph is fully loaded.')
    }
  }, [])

  const handleNodeClick = useCallback((node: any) => {
    setSelectedNode(node)
  }, [])

  const handleLoadNeighbors = useCallback((nodeId: string) => {
    loadSubgraph(nodeId, 1)
    setSelectedNode(null)
  }, [])

  return (
    <div className="h-screen flex flex-col bg-deep-space">
      <div className="p-6 border-b border-glass-border">
        <h1 className="text-3xl font-bold font-mono mb-2">Graph Explorer</h1>
        <p className="text-gray-400">Interactive 3D knowledge graph visualization</p>
      </div>

      <div className="flex-1 flex relative overflow-hidden">
        {/* Controls Sidebar */}
        <div className="w-80 border-r border-glass-border overflow-y-auto p-6">
          <GraphControls
            onFilterChange={setFilters}
            onExport={exportGraph}
            onLoadSubgraph={loadSubgraph}
          />
        </div>

        {/* Graph Canvas */}
        <div className="flex-1 relative">
          {loading ? (
            <div className="absolute inset-0 flex items-center justify-center text-gray-400">
              <div className="text-center">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-400 mx-auto mb-4"></div>
                <div>Loading graph...</div>
              </div>
            </div>
          ) : (
            <ForceGraph3D
              ref={graphRef}
              graphData={{ nodes: displayNodes, links: displayLinks }}
              nodeLabel={(node: any) => {
                const riskText = node.riskScore ? ` (Risk: ${node.riskScore})` : ''
                const degreeText = node.degree ? ` [${node.degree} connections]` : ''
                return `${node.name}${riskText}${degreeText}`
              }}
              nodeColor={(node: any) => getNodeColorByType(node)}
              nodeVal={(node: any) => getNodeSizeByImportance(node)}
              linkLabel={(link: any) => (filters.showLabels ? link.type : '')}
              linkColor={() => 'rgba(255, 255, 255, 0.3)'}
              linkWidth={1}
              linkDirectionalArrowLength={4}
              linkDirectionalArrowRelPos={1}
              linkCurvature={0.1}
              onNodeClick={handleNodeClick}
              backgroundColor="#0A0F1E"
              showNavInfo={true}
              nodeThreeObject={(node: any) => {
                const color = getNodeColorByType(node)
                const size = getNodeSizeByImportance(node)
                
                // Create glowing sphere
                const geometry = new (window as any).THREE.SphereGeometry(size / 10, 16, 16)
                const material = new (window as any).THREE.MeshPhongMaterial({
                  color,
                  transparent: true,
                  opacity: 0.9,
                  emissive: color,
                  emissiveIntensity: 0.3,
                })
                const sphere = new (window as any).THREE.Mesh(geometry, material)
                
                // Add glow effect for high-risk nodes
                if (node.riskScore !== undefined && node.riskScore >= 80) {
                  const glowGeometry = new (window as any).THREE.SphereGeometry(size / 8, 16, 16)
                  const glowMaterial = new (window as any).THREE.MeshBasicMaterial({
                    color: '#EF4444',
                    transparent: true,
                    opacity: 0.2,
                  })
                  const glow = new (window as any).THREE.Mesh(glowGeometry, glowMaterial)
                  
                  // Animate pulse
                  const animate = () => {
                    const time = Date.now() * 0.001
                    const scale = 1 + Math.sin(time * 2) * 0.2
                    glow.scale.set(scale, scale, scale)
                    requestAnimationFrame(animate)
                  }
                  animate()
                  
                  const group = new (window as any).THREE.Group()
                  group.add(glow)
                  group.add(sphere)
                  return group
                }
                
                return sphere
              }}
              linkThreeObject={(link: any) => {
                // Create curved line for relationships
                const geometry = new (window as any).THREE.BufferGeometry()
                const material = new (window as any).THREE.LineBasicMaterial({
                  color: 0xffffff,
                  transparent: true,
                  opacity: 0.3,
                })
                return new (window as any).THREE.Line(geometry, material)
              }}
            />
          )}

          {/* Node Details Panel */}
          <NodeDetailsPanel
            node={selectedNode}
            onClose={() => setSelectedNode(null)}
            onLoadNeighbors={handleLoadNeighbors}
          />
        </div>
      </div>
    </div>
  )
}
