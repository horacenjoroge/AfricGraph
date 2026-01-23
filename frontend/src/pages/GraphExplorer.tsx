import { useState, useEffect, useRef, useCallback, useMemo } from 'react'
import ForceGraph3D from 'react-force-graph-3d'
import axios from 'axios'
import GraphControls, { GraphFilters } from '../components/graph/GraphControls'
import NodeDetailsPanel from '../components/graph/NodeDetailsPanel'
import HowItWorks from '../components/HowItWorks'
import {
  calculateNodeDegrees,
  filterGraph,
  getNodeColorByType,
  getNodeSizeByImportance,
} from '../utils/graphUtils'
import { exportGraphAsImage, exportGraphAsJSON } from '../utils/exportGraph'

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
  const [graphDimensions, setGraphDimensions] = useState({ width: 800, height: 600 })

  useEffect(() => {
    loadGraphData()
  }, [])

  // Update graph dimensions when container resizes
  useEffect(() => {
    const updateDimensions = () => {
      if (graphContainerRef.current) {
        setGraphDimensions({
          width: graphContainerRef.current.clientWidth,
          height: graphContainerRef.current.clientHeight,
        })
      }
    }

    updateDimensions()
    window.addEventListener('resize', updateDimensions)
    return () => window.removeEventListener('resize', updateDimensions)
  }, [])

  useEffect(() => {
    // Recalculate degrees when nodes/links change
    if (allNodes.length === 0 && allLinks.length === 0) {
      setDisplayNodes([])
      setDisplayLinks([])
      return
    }

    console.log('Recalculating graph display:', {
      nodeCount: allNodes.length,
      linkCount: allLinks.length,
      filters,
    })

    const nodesWithDegrees = calculateNodeDegrees(allNodes, allLinks)
    console.log('Nodes with degrees:', nodesWithDegrees.length)

    // Apply filters
    const filtered = filterGraph(nodesWithDegrees, allLinks, filters)
    console.log('Filtered result:', {
      nodeCount: filtered.nodes.length,
      linkCount: filtered.links.length,
    })
    
    // Create a node map for link resolution
    const nodeMap = new Map(filtered.nodes.map(n => [n.id, n]))
    
    // Convert link source/target from IDs to node objects for react-force-graph-3d
    const resolvedLinks = filtered.links.map(link => {
      const sourceId = typeof link.source === 'string' ? link.source : link.source.id
      const targetId = typeof link.target === 'string' ? link.target : link.target.id
      const sourceNode = nodeMap.get(sourceId)
      const targetNode = nodeMap.get(targetId)
      
      if (!sourceNode || !targetNode) {
        console.warn('Link references missing node:', { sourceId, targetId, link })
        return null
      }
      
      return {
        ...link,
        source: sourceNode,
        target: targetNode,
      }
    }).filter((link): link is Link => link !== null)
    
    console.log('Resolved links:', resolvedLinks.length)
    
    setDisplayNodes(filtered.nodes)
    setDisplayLinks(resolvedLinks)
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
        params: { max_hops: maxHops, format: 'visualization' },
      })
      
      const subgraph = response.data
      console.log('Subgraph response:', subgraph)
      
      // Visualization format returns 'edges' not 'relationships'
      const edges = subgraph.edges || subgraph.relationships || []
      
      const nodes: Node[] = (subgraph.nodes || []).map((n: any) => {
        // Handle null riskScore values
        const riskScore = n.riskScore ?? n.properties?.risk_score ?? n.properties?.riskScore
        return {
          id: String(n.id),
          name: n.label || n.properties?.name || n.id,
          labels: Array.isArray(n.labels) ? n.labels : (n.labels ? [n.labels] : []),
          riskScore: riskScore !== null && riskScore !== undefined ? Number(riskScore) : undefined,
          properties: n.properties || {},
        }
      })
      
      const links: Link[] = edges.map((r: any) => ({
        source: String(r.source || r.from_id),
        target: String(r.target || r.to_id),
        type: r.type || '',
      }))
      
      console.log('Transformed nodes:', nodes)
      console.log('Transformed links:', links)
      console.log('Node count:', nodes.length, 'Link count:', links.length)
      
      if (nodes.length === 0) {
        console.warn('No nodes found in subgraph response')
        console.warn('Raw subgraph data:', JSON.stringify(subgraph, null, 2))
      }
      
      // Set nodes and links - this will trigger the useEffect to recalculate degrees and apply filters
      setAllNodes(nodes)
      setAllLinks(links)
    } catch (error: any) {
      console.error('Failed to load subgraph:', error)
      console.error('Error details:', error.response?.data || error.message)
      // Error notification will be handled by the notification system if needed
      loadGraphData()
    } finally {
      setLoading(false)
    }
  }

  const graphContainerRef = useRef<HTMLDivElement>(null)

  const exportGraph = useCallback(async () => {
    try {
      if (graphContainerRef.current) {
        await exportGraphAsImage(graphContainerRef.current)
      } else {
        // Fallback: export as JSON
        exportGraphAsJSON(displayNodes, displayLinks)
        alert('Graph exported as JSON. Image export requires graph container reference.')
      }
    } catch (error) {
      console.error('Export failed:', error)
      // Fallback to JSON export
      exportGraphAsJSON(displayNodes, displayLinks)
      alert('Image export failed. Graph data exported as JSON instead.')
    }
  }, [displayNodes, displayLinks])

  const handleNodeClick = useCallback((node: any) => {
    setSelectedNode(node)
  }, [])

  const handleLoadNeighbors = useCallback((nodeId: string) => {
    loadSubgraph(nodeId, 1)
    setSelectedNode(null)
  }, [])

  // Memoize graph data to prevent unnecessary re-renders
  const graphData = useMemo(() => ({
    nodes: displayNodes,
    links: displayLinks,
  }), [displayNodes, displayLinks])

  return (
    <div className="h-screen flex flex-col bg-deep-space">
      <div className="px-6 py-4 border-b border-glass-border glass-panel">
        <h1 className="text-3xl font-bold font-mono mb-1 text-glow-cyan tracking-tight">
          GRAPH EXPLORER
        </h1>
        <p className="text-gray-500 font-mono text-xs uppercase tracking-wider">
          Interactive 3D Knowledge Graph Visualization
        </p>
      </div>

      <div className="flex-1 flex relative" style={{ height: 'calc(100vh - 100px)', overflow: 'hidden' }}>
        {/* Controls Sidebar - 40% */}
        <div className="w-[40%] border-r border-glass-border overflow-y-auto p-6 glass-panel" style={{ maxHeight: '100%' }}>
          <HowItWorks />
          <GraphControls
            onFilterChange={setFilters}
            onExport={exportGraph}
            onLoadSubgraph={loadSubgraph}
          />
        </div>

        {/* Graph Canvas - 60% */}
        <div ref={graphContainerRef} className="flex-1 relative" style={{ height: '100%', overflow: 'hidden' }}>
          {loading ? (
            <div className="absolute inset-0 flex items-center justify-center text-gray-400">
              <div className="text-center">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-400 mx-auto mb-4"></div>
                <div>Loading graph...</div>
              </div>
            </div>
          ) : displayNodes.length === 0 && allNodes.length === 0 ? (
            <div className="absolute inset-0 flex items-center justify-center text-gray-400">
              <div className="text-center">
                <div className="text-lg mb-2">No graph data available</div>
                <div className="text-sm">Load a subgraph by entering a Node ID above</div>
                {allNodes.length > 0 && (
                  <div className="text-xs mt-2 text-yellow-400">
                    Data loaded but filtered out. Check your filter settings.
                  </div>
                )}
              </div>
            </div>
          ) : displayNodes.length === 0 && allNodes.length > 0 ? (
            <div className="absolute inset-0 flex items-center justify-center text-gray-400">
              <div className="text-center">
                <div className="text-lg mb-2">All nodes filtered out</div>
                <div className="text-sm">Adjust your filter settings to see nodes</div>
                <div className="text-xs mt-2">Total nodes: {allNodes.length}</div>
              </div>
            </div>
          ) : (
            <ForceGraph3D
              ref={graphRef}
              graphData={graphData}
              width={graphDimensions.width}
              height={graphDimensions.height}
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
              backgroundColor="#030712"
              showNavInfo={true}
              onEngineStop={() => {
                console.log('Graph engine stopped, nodes:', displayNodes.length, 'links:', displayLinks.length)
                if (graphRef.current) {
                  // Zoom to fit
                  graphRef.current.zoomToFit(400)
                }
              }}
              onRenderFramePre={() => {
                // Ensure lighting is set up
                if (graphRef.current && (window as any).THREE) {
                  const THREE = (window as any).THREE
                  const scene = graphRef.current.scene()
                  if (scene) {
                    // Add ambient light if not present
                    const lights = scene.children.filter((child: any) => child.type === 'AmbientLight')
                    if (lights.length === 0) {
                      const ambientLight = new THREE.AmbientLight(0xffffff, 0.6)
                      scene.add(ambientLight)
                    }
                    
                    // Add directional light if not present
                    const dirLights = scene.children.filter((child: any) => child.type === 'DirectionalLight')
                    if (dirLights.length === 0) {
                      const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8)
                      directionalLight.position.set(1, 1, 1)
                      scene.add(directionalLight)
                    }
                  }
                }
              }}
              nodeThreeObject={(node: any) => {
                if (!(window as any).THREE) {
                  console.error('THREE.js not loaded')
                  return null
                }
                
                const THREE = (window as any).THREE
                const color = getNodeColorByType(node)
                const size = getNodeSizeByImportance(node)
                
                // Create glowing sphere
                const geometry = new THREE.SphereGeometry(size / 10, 16, 16)
                const material = new THREE.MeshPhongMaterial({
                  color,
                  transparent: true,
                  opacity: 0.9,
                  emissive: color,
                  emissiveIntensity: 0.3,
                })
                const sphere = new THREE.Mesh(geometry, material)
                
                // Add glow effect for high-risk nodes
                if (node.riskScore !== undefined && node.riskScore >= 80) {
                  const glowGeometry = new THREE.SphereGeometry(size / 8, 16, 16)
                  const glowMaterial = new THREE.MeshBasicMaterial({
                    color: '#EF4444',
                    transparent: true,
                    opacity: 0.2,
                  })
                  const glow = new THREE.Mesh(glowGeometry, glowMaterial)
                  
                  // Animate pulse
                  const animate = () => {
                    const time = Date.now() * 0.001
                    const scale = 1 + Math.sin(time * 2) * 0.2
                    glow.scale.set(scale, scale, scale)
                    requestAnimationFrame(animate)
                  }
                  animate()
                  
                  const group = new THREE.Group()
                  group.add(glow)
                  group.add(sphere)
                  return group
                }
                
                return sphere
              }}
              linkThreeObject={(link: any) => {
                if (!(window as any).THREE) {
                  return null
                }
                
                const THREE = (window as any).THREE
                // Create curved line for relationships
                const geometry = new THREE.BufferGeometry()
                const material = new THREE.LineBasicMaterial({
                  color: 0xffffff,
                  transparent: true,
                  opacity: 0.3,
                })
                return new THREE.Line(geometry, material)
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
