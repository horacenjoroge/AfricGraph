import { useState, useEffect, useRef, useCallback, useMemo } from 'react'
import { useSearchParams } from 'react-router-dom'
import ForceGraph3D from 'react-force-graph-3d'
import axios from 'axios'
import GraphControls, { GraphFilters } from '../components/graph/GraphControls'
import NodeDetailsPanel from '../components/graph/NodeDetailsPanel'
import ConnectionsDiagram from '../components/graph/ConnectionsDiagram'
import HowItWorks from '../components/HowItWorks'
import GraphLegend from '../components/graph/GraphLegend'
import {
  calculateNodeDegrees,
  calculateHopDistances,
  filterGraph,
  getNodeColorByType,
  getNodeSizeByImportance,
  getNodeOpacity,
  getLinkOpacity,
} from '../utils/graphUtils'
import { exportConnectionsAsPDF, exportConnectionsAsDOCX } from '../utils/exportDocument'

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
  const [searchParams, setSearchParams] = useSearchParams()
  const [allNodes, setAllNodes] = useState<Node[]>([])
  const [allLinks, setAllLinks] = useState<Link[]>([])
  const [displayNodes, setDisplayNodes] = useState<Node[]>([])
  const [displayLinks, setDisplayLinks] = useState<Link[]>([])
  const [selectedNode, setSelectedNode] = useState<Node | null>(null)
  const [focusedNode, setFocusedNode] = useState<Node | null>(null)
  const [loading, setLoading] = useState(false)
  const [showConnectionsDiagram, setShowConnectionsDiagram] = useState(false)
  const [nodeConnections, setNodeConnections] = useState<any[]>([])
  const [centerNodeId, setCenterNodeId] = useState<string | null>(null)
  const [nodeHopDistances, setNodeHopDistances] = useState<Map<string, number>>(new Map())
  const [nodeSizes, setNodeSizes] = useState<Map<string, number>>(new Map())
  const [availableRelationshipTypes, setAvailableRelationshipTypes] = useState<string[]>([])
  const [filters, setFilters] = useState<GraphFilters>({
    nodeTypes: [],
    riskLevel: 'all',
    minRiskScore: 0,
    maxRiskScore: 100,
    showLabels: true,
    relationshipTypes: [],
    maxLayers: 5, // Show all layers by default (no progressive disclosure initially)
    focusMode: false,
  })
  const graphRef = useRef<any>()
  const [graphDimensions, setGraphDimensions] = useState({ width: 800, height: 600 })
  const [cameraDistance, setCameraDistance] = useState(400)

  // Define loadGraphData first so it's available for error fallback
  const loadGraphData = useCallback(async () => {
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
  }, [])

  // Define loadSubgraph before useEffect so it's available
  const loadSubgraph = useCallback(async (nodeId: string, maxHops: number) => {
    setLoading(true)
    try {
      const tenantId = localStorage.getItem('current_tenant_id')
      const headers = tenantId ? { 'X-Tenant-ID': tenantId } : {}
      
      console.log('Loading subgraph for node:', nodeId, 'with tenant:', tenantId)
      
      const response = await axios.get(`/api/v1/graph/subgraph/${nodeId}`, {
        params: { max_hops: maxHops, format: 'visualization' },
        headers: headers,
      })
      
      console.log('Subgraph API response:', {
        status: response.status,
        nodeCount: response.data?.nodes?.length || 0,
        edgeCount: response.data?.edges?.length || 0,
        centerNodeId: response.data?.center_node_id,
      })
      
      const subgraph = response.data
      console.log('Subgraph response:', subgraph)
      console.log('Subgraph keys:', Object.keys(subgraph))
      console.log('Nodes array:', Array.isArray(subgraph.nodes), 'length:', subgraph.nodes?.length)
      console.log('Edges array:', Array.isArray(subgraph.edges), 'length:', subgraph.edges?.length)
      
      // Visualization format returns 'edges' not 'relationships'
      const edges = subgraph.edges || subgraph.relationships || []
      
      if (!subgraph.nodes || subgraph.nodes.length === 0) {
        console.error('No nodes in subgraph response!', {
          responseData: subgraph,
          nodeId: nodeId,
          tenantId: tenantId,
        })
        // Still set empty arrays so UI can show error message
        setAllNodes([])
        setAllLinks([])
        setLoading(false)
        return
      }
      
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
        source: String(r.source || r.from || r.from_id),
        target: String(r.target || r.to || r.to_id),
        type: r.type || '',
      }))
      
      console.log('Transformed nodes:', nodes)
      console.log('Transformed links:', links)
      console.log('Node count:', nodes.length, 'Link count:', links.length)
      
      // Debug: Check links connected to the requested center node
      const centerLinks = links.filter(link => {
        return link.source === nodeId || link.target === nodeId
      })
      console.log(`Links connected to ${nodeId}:`, centerLinks.length)
      console.log('Sample center links:', centerLinks.slice(0, 5))
      
      if (nodes.length === 0) {
        console.warn('No nodes found in subgraph response')
        console.warn('Raw subgraph data:', JSON.stringify(subgraph, null, 2))
      }
      
      // Set center node ID - use the requested nodeId if it exists in nodes, otherwise use first node
      let centerId = nodeId
      if (centerId && !nodes.find(n => n.id === centerId)) {
        // Requested center node not found, use first node
        centerId = nodes[0]?.id || null
      } else if (!centerId) {
        centerId = nodes[0]?.id || null
      }
      setCenterNodeId(centerId)
      
      // Reset focus when loading new subgraph
      setFocusedNode(null)
      
      // Reset camera distance when loading new subgraph
      setCameraDistance(400)
      
      // Extract unique relationship types from links
      const relTypes = Array.from(new Set(links.map(link => link.type).filter(Boolean)))
      setAvailableRelationshipTypes(relTypes)
      
      // Debug: Log what we received
      console.log('Loaded subgraph:', {
        centerNodeId: centerId,
        totalNodes: nodes.length,
        totalLinks: links.length,
        centerNodeLinks: links.filter(link => {
          const sourceId = typeof link.source === 'string' ? link.source : link.source.id
          const targetId = typeof link.target === 'string' ? link.target : link.target.id
          return sourceId === centerId || targetId === centerId
        }).length,
        sampleLinks: links.slice(0, 5).map(link => ({
          source: typeof link.source === 'string' ? link.source : link.source.id,
          target: typeof link.target === 'string' ? link.target : link.target.id,
          type: link.type
        }))
      })
      
      // Set nodes and links - this will trigger the useEffect to recalculate degrees and apply filters
      setAllNodes(nodes)
      setAllLinks(links)
    } catch (error: any) {
      console.error('Failed to load subgraph:', error)
      console.error('Error details:', error.response?.data || error.message)
      // Fallback to loading mock data if subgraph load fails
      loadGraphData()
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    // Check for node parameter in URL
    const nodeParam = searchParams.get('node')
    if (nodeParam) {
      // Auto-load the node subgraph
      console.log('Loading node from URL parameter:', nodeParam)
      loadSubgraph(nodeParam, 2)
    } else {
      // Only load mock data if no node parameter
      loadGraphData()
    }
  }, [searchParams, loadSubgraph, loadGraphData])

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

  // Calculate hop distances when center node or data changes
  useEffect(() => {
    if (centerNodeId && allNodes.length > 0) {
      // Verify center node exists in nodes
      const centerExists = allNodes.some(n => n.id === centerNodeId)
      if (centerExists && allLinks.length > 0) {
        const distances = calculateHopDistances(centerNodeId, allNodes, allLinks)
        setNodeHopDistances(distances)
        console.log('Hop distances calculated:', {
          centerNodeId,
          totalNodes: allNodes.length,
          distancesCalculated: distances.size,
          sampleDistances: Array.from(distances.entries()).slice(0, 5)
        })
      } else if (centerExists) {
        // Center node exists but no links - set distance 0 for center only
        const distances = new Map([[centerNodeId, 0]])
        setNodeHopDistances(distances)
      } else {
        // Center node not found - clear distances
        console.warn('Center node not found in nodes:', centerNodeId)
        setNodeHopDistances(new Map())
      }
    } else {
      setNodeHopDistances(new Map())
    }
  }, [centerNodeId, allNodes, allLinks])

  // Calculate and lock node sizes once
  useEffect(() => {
    if (allNodes.length > 0) {
      const nodesWithDegrees = calculateNodeDegrees(allNodes, allLinks)
      const sizeMap = new Map<string, number>()
      nodesWithDegrees.forEach(node => {
        sizeMap.set(node.id, getNodeSizeByImportance(node))
      })
      setNodeSizes(sizeMap)
    }
  }, [allNodes, allLinks])

  useEffect(() => {
    // Recalculate degrees when nodes/links change
    if (allNodes.length === 0 && allLinks.length === 0) {
      setDisplayNodes([])
      setDisplayLinks([])
      return
    }

    const nodesWithDegrees = calculateNodeDegrees(allNodes, allLinks)

    // Debug logging
    console.log('Filtering graph:', {
      totalNodes: nodesWithDegrees.length,
      totalLinks: allLinks.length,
      centerNodeId,
      hopDistancesSize: nodeHopDistances.size,
      maxLayers: filters.maxLayers,
      focusMode: filters.focusMode,
      focusedNodeId: focusedNode?.id,
    })

    // Apply filters with new features
    const filtered = filterGraph(
      nodesWithDegrees,
      allLinks,
      filters,
      centerNodeId,
      nodeHopDistances,
      focusedNode?.id || null
    )
    
    console.log('After filtering:', {
      filteredNodes: filtered.nodes.length,
      filteredLinks: filtered.links.length,
      centerNodeId,
    })
    
    // Debug: Check links connected to center node
    if (centerNodeId) {
      const centerLinks = filtered.links.filter(link => {
        const sourceId = typeof link.source === 'string' ? link.source : link.source.id
        const targetId = typeof link.target === 'string' ? link.target : link.target.id
        return sourceId === centerNodeId || targetId === centerNodeId
      })
      console.log('Links connected to center node:', centerLinks.length)
      console.log('Center node links:', centerLinks.map(link => ({
        source: typeof link.source === 'string' ? link.source : link.source.id,
        target: typeof link.target === 'string' ? link.target : link.target.id,
        type: link.type
      })))
    }
    
    // Create a node map for link resolution
    const nodeMap = new Map(filtered.nodes.map(n => [n.id, n]))
    
    // Initialize node positions - start all nodes close together so links can work
    if (centerNodeId && nodeHopDistances.size > 0) {
      filtered.nodes.forEach((node: any) => {
        if (node.id === centerNodeId) {
          // Center node at origin - don't hard pin, use centering force instead
          node.x = 0
          node.y = 0
          node.z = 0
          // Don't hard pin - let centering force handle it
          node.fx = undefined
          node.fy = undefined
          node.fz = undefined
        } else {
          // Position other nodes close to center initially - link forces will organize them
          const distance = nodeHopDistances.get(node.id) || 1
          // Start very close so link forces can immediately pull them
          const radius = distance === 1 ? 30 : distance * 60
          
          // Random position on sphere at this radius
          const theta = Math.random() * Math.PI * 2 // Azimuth
          const phi = Math.acos(Math.random() * 2 - 1) // Polar angle
          
          node.x = radius * Math.sin(phi) * Math.cos(theta)
          node.y = radius * Math.sin(phi) * Math.sin(theta)
          node.z = radius * Math.cos(phi)
          
          // Don't pin non-center nodes
          node.fx = undefined
          node.fy = undefined
          node.fz = undefined
        }
      })
    }
    
    // Convert link source/target from IDs to node objects for react-force-graph-3d
    const resolvedLinks = filtered.links.map(link => {
      const sourceId = typeof link.source === 'string' ? link.source : link.source.id
      const targetId = typeof link.target === 'string' ? link.target : link.target.id
      const sourceNode = nodeMap.get(sourceId)
      const targetNode = nodeMap.get(targetId)
      
      if (!sourceNode || !targetNode) {
        return null
      }
      
      return {
        ...link,
        source: sourceNode,
        target: targetNode,
      }
    }).filter((link): link is Link => link !== null)
    
    setDisplayNodes(filtered.nodes)
    setDisplayLinks(resolvedLinks)
  }, [allNodes, allLinks, filters, centerNodeId, nodeHopDistances, focusedNode])



  const graphContainerRef = useRef<HTMLDivElement>(null)

  const handleNodeClick = useCallback((node: any) => {
    setSelectedNode(node)
    // Toggle focus mode on click if enabled
    if (filters.focusMode) {
      setFocusedNode(focusedNode?.id === node.id ? null : node)
    }
  }, [filters.focusMode, focusedNode])

  const clearFocus = useCallback(() => {
    setFocusedNode(null)
  }, [])

  const handleLoadNeighbors = useCallback((nodeId: string) => {
    loadSubgraph(nodeId, 1)
    setSelectedNode(null)
  }, [])

  const handleShowConnections = useCallback(async (node: Node) => {
    try {
      setLoading(true)
      const response = await axios.get(`/api/v1/graph/node/${node.id}/details`)
      setNodeConnections(response.data.connections || [])
      setShowConnectionsDiagram(true)
    } catch (error) {
      console.error('Failed to load connections:', error)
      alert('Failed to load connections. Please try again.')
    } finally {
      setLoading(false)
    }
  }, [])

  const handleExportConnections = useCallback(async (format: 'pdf' | 'docx') => {
    if (!selectedNode) return
    
    try {
      if (format === 'pdf') {
        await exportConnectionsAsPDF(selectedNode, nodeConnections)
      } else {
        await exportConnectionsAsDOCX(selectedNode, nodeConnections)
      }
    } catch (error) {
      console.error('Export failed:', error)
      alert(`Failed to export as ${format.toUpperCase()}. Please try again.`)
    }
  }, [selectedNode, nodeConnections])

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
          <GraphLegend />
          <GraphControls
            onFilterChange={(newFilters) => {
              setFilters(newFilters)
              // Clear focus when focus mode is disabled
              if (!newFilters.focusMode && focusedNode) {
                setFocusedNode(null)
              }
            }}
            onLoadSubgraph={loadSubgraph}
            availableRelationshipTypes={availableRelationshipTypes}
          />
        </div>

        {/* Graph Canvas - 60% */}
        <div ref={graphContainerRef} className="flex-1 relative" style={{ height: '100%', overflow: 'hidden' }}>
          {/* Zoom Controls */}
          <div className="absolute top-4 right-4 z-20 flex flex-col gap-2">
            <button
              onClick={() => {
                if (graphRef.current) {
                  const currentDistance = cameraDistance
                  const newDistance = Math.max(100, currentDistance - 50)
                  setCameraDistance(newDistance)
                  graphRef.current.cameraPosition({ x: 0, y: 0, z: newDistance })
                }
              }}
              className="glass-panel border border-glass-border rounded-lg p-2 hover:bg-cyan-500/20 transition-colors"
              title="Zoom In"
            >
              <svg className="w-5 h-5 text-cyan-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
            </button>
            <button
              onClick={() => {
                if (graphRef.current) {
                  const currentDistance = cameraDistance
                  const newDistance = Math.min(2000, currentDistance + 50)
                  setCameraDistance(newDistance)
                  graphRef.current.cameraPosition({ x: 0, y: 0, z: newDistance })
                }
              }}
              className="glass-panel border border-glass-border rounded-lg p-2 hover:bg-cyan-500/20 transition-colors"
              title="Zoom Out"
            >
              <svg className="w-5 h-5 text-cyan-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 12H4" />
              </svg>
            </button>
          </div>
          
          {/* Summary Statistics Overlay */}
          {displayNodes.length > 0 && (
            <div className="absolute top-4 left-4 glass-panel-strong rounded-lg p-4 z-10 min-w-[200px]">
              <h4 className="text-sm font-bold mb-2 text-cyan-400">Graph Summary</h4>
              <div className="space-y-1 text-xs">
                <div className="flex justify-between">
                  <span className="text-gray-400">Total Nodes:</span>
                  <span className="font-mono">{displayNodes.length}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Connections:</span>
                  <span className="font-mono">{displayLinks.length}</span>
                </div>
                {centerNodeId && (
                  <div className="flex justify-between">
                    <span className="text-gray-400">Center:</span>
                    <span className="font-mono text-cyan-400">{centerNodeId}</span>
                  </div>
                )}
                <div className="flex justify-between">
                  <span className="text-gray-400">Layers Shown:</span>
                  <span className="font-mono">{filters.maxLayers}</span>
                </div>
                {filters.relationshipTypes.length > 0 && (
                  <div className="mt-2 pt-2 border-t border-glass-border">
                    <div className="text-gray-400 mb-1">Relationship Types:</div>
                    <div className="flex flex-wrap gap-1">
                      {filters.relationshipTypes.map(type => (
                        <span key={type} className="px-1.5 py-0.5 bg-blue-500/20 text-blue-400 rounded text-xs">
                          {type}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
                {focusedNode && (
                  <div className="mt-2 pt-2 border-t border-glass-border">
                    <div className="text-gray-400 mb-1">Focused:</div>
                    <div className="font-mono text-yellow-400">{focusedNode.name || focusedNode.id}</div>
                    <button
                      onClick={clearFocus}
                      className="mt-1 text-xs text-red-400 hover:text-red-300"
                    >
                      Clear Focus
                    </button>
                  </div>
                )}
              </div>
            </div>
          )}
          
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
                const isCenterNode = node.id === centerNodeId
                const centerLabel = isCenterNode ? ' [CENTER]' : ''
                const riskText = node.riskScore ? ` (Risk: ${node.riskScore})` : ''
                const degreeText = node.degree ? ` [${node.degree} connections]` : ''
                return `${node.name}${centerLabel}${riskText}${degreeText}`
              }}
              nodeColor={(node: any) => {
                const isCenterNode = node.id === centerNodeId
                // Center node is always bright cyan, others use their type-based color
                const color = isCenterNode ? '#00FFFF' : getNodeColorByType(node)
                const opacity = getNodeOpacity(
                  node.id,
                  nodeHopDistances,
                  centerNodeId,
                  focusedNode?.id || null,
                  filters.focusMode
                )
                // Convert hex to rgba with opacity (center node always full opacity)
                const r = parseInt(color.slice(1, 3), 16)
                const g = parseInt(color.slice(3, 5), 16)
                const b = parseInt(color.slice(5, 7), 16)
                return `rgba(${r}, ${g}, ${b}, ${isCenterNode ? 1.0 : opacity})`
              }}
              nodeVal={(node: any) => {
                // Use locked size to prevent Framer Motion size jumps
                const lockedSize = nodeSizes.get(node.id)
                return getNodeSizeByImportance(node, lockedSize)
              }}
              linkLabel={(link: any) => (filters.showLabels ? link.type : '')}
              linkColor={(link: any) => {
                const sourceId = typeof link.source === 'string' ? link.source : link.source.id
                const targetId = typeof link.target === 'string' ? link.target : link.target.id
                const isConnectedToCenter = centerNodeId && (sourceId === centerNodeId || targetId === centerNodeId)
                
                // Make links connected to center node bright cyan
                if (isConnectedToCenter) {
                  const opacity = getLinkOpacity(link, focusedNode?.id || null, filters.focusMode)
                  return `rgba(0, 255, 255, ${Math.max(opacity, 0.9)})` // Bright cyan, minimum 90% opacity
                }
                
                const opacity = getLinkOpacity(link, focusedNode?.id || null, filters.focusMode)
                return `rgba(255, 255, 255, ${opacity})`
              }}
              linkWidth={(link: any) => {
                const sourceId = typeof link.source === 'string' ? link.source : link.source.id
                const targetId = typeof link.target === 'string' ? link.target : link.target.id
                const isConnectedToCenter = centerNodeId && (sourceId === centerNodeId || targetId === centerNodeId)
                
                // Make links to center node thicker
                if (isConnectedToCenter) {
                  return 4 // Thick cyan lines for center node connections
                }
                
                // Make links to focused node thicker
                if (filters.focusMode && focusedNode) {
                  if (sourceId === focusedNode.id || targetId === focusedNode.id) {
                    return 2
                  }
                }
                return 1.5 // Slightly thicker default links
              }}
              linkDirectionalArrowLength={4}
              linkDirectionalArrowRelPos={1}
              linkCurvature={0.1}
              onNodeClick={handleNodeClick}
              backgroundColor="#030712"
              showNavInfo={true}
              // Prevent center node from being dragged too far
              onNodeDrag={(node: any) => {
                // Allow center node to move slightly but pull it back
                if (centerNodeId && node.id === centerNodeId) {
                  const dist = Math.sqrt(node.x ** 2 + node.y ** 2 + node.z ** 2)
                  if (dist > 50) {
                    // If dragged too far, reset to origin
                    node.fx = 0
                    node.fy = 0
                    node.fz = 0
                  } else {
                    // Allow small movements
                    node.fx = undefined
                    node.fy = undefined
                    node.fz = undefined
                  }
                }
              }}
              // Customize force simulation for radial layout
              d3Force={(d3: any) => {
                // Center node attraction - gently pull center node back to origin
                if (centerNodeId) {
                  d3.force('centerNode', (alpha: number) => {
                    displayNodes.forEach((node: any) => {
                      if (node.id === centerNodeId) {
                        // Strong attraction to origin
                        const dist = Math.sqrt(node.x ** 2 + node.y ** 2 + node.z ** 2)
                        if (dist > 1) {
                          const force = -dist * alpha * 0.5
                          node.vx += (node.x / dist) * force
                          node.vy += (node.y / dist) * force
                          node.vz += (node.z / dist) * force
                        }
                      }
                    })
                  })
                }
                
                // Strong attraction force for nodes connected to center node
                if (centerNodeId) {
                  d3.force('centerAttraction', (alpha: number) => {
                    const centerNode = displayNodes.find((n: any) => n.id === centerNodeId)
                    if (!centerNode) return
                    
                    displayNodes.forEach((node: any) => {
                      if (node.id === centerNodeId) return
                      
                      // Check if this node is connected to center
                      const isConnected = displayLinks.some((link: any) => {
                        const sourceId = typeof link.source === 'string' ? link.source : link.source.id
                        const targetId = typeof link.target === 'string' ? link.target : link.target.id
                        return (sourceId === centerNodeId && targetId === node.id) ||
                               (targetId === centerNodeId && sourceId === node.id)
                      })
                      
                      if (isConnected) {
                        // Calculate vector from center to this node
                        const dx = node.x - centerNode.x
                        const dy = node.y - centerNode.y
                        const dz = node.z - centerNode.z
                        const dist = Math.sqrt(dx ** 2 + dy ** 2 + dz ** 2)
                        
                        if (dist > 0.1) {
                          // Target distance for direct connections
                          const targetDist = 60
                          const force = (targetDist - dist) * alpha * 0.3
                          
                          node.vx += (dx / dist) * force
                          node.vy += (dy / dist) * force
                          node.vz += (dz / dist) * force
                        }
                      }
                    })
                  })
                }
                
                // Reduce repulsion to keep nodes closer together
                const charge = d3.force('charge')
                if (charge) {
                  charge.strength(-15) // Reduced repulsion
                }
                
                // Strong link force to pull connected nodes together
                const link = d3.force('link')
                if (link) {
                  link.strength((link: any) => {
                    const sourceId = typeof link.source === 'string' ? link.source : link.source.id
                    const targetId = typeof link.target === 'string' ? link.target : link.target.id
                    const isConnectedToCenter = centerNodeId && (sourceId === centerNodeId || targetId === centerNodeId)
                    // Very strong links for center node connections
                    return isConnectedToCenter ? 1.2 : 0.6
                  })
                  link.distance((link: any) => {
                    const sourceId = typeof link.source === 'string' ? link.source : link.source.id
                    const targetId = typeof link.target === 'string' ? link.target : link.target.id
                    const isConnectedToCenter = centerNodeId && (sourceId === centerNodeId || targetId === centerNodeId)
                    // Short distance for center node connections
                    return isConnectedToCenter ? 60 : 100
                  })
                }
              }}
              cooldownTicks={200}
              onEngineTick={() => {
                // Log progress during simulation
                if (centerNodeId && displayNodes.length > 0) {
                  const centerNode = displayNodes.find((n: any) => n.id === centerNodeId)
                  if (centerNode) {
                    // Count nodes connected to center
                    const connectedNodes = displayLinks.filter((link: any) => {
                      const sourceId = typeof link.source === 'string' ? link.source : link.source.id
                      const targetId = typeof link.target === 'string' ? link.target : link.target.id
                      return sourceId === centerNodeId || targetId === centerNodeId
                    }).length
                    
                    // Log first few ticks to debug
                    if (Math.random() < 0.01) { // Log ~1% of ticks
                      console.log('Force simulation:', {
                        centerNodePos: { x: centerNode.x, y: centerNode.y, z: centerNode.z },
                        connectedNodes,
                        totalLinks: displayLinks.length,
                      })
                    }
                  }
                }
              }}
              onEngineStop={() => {
                console.log('Graph engine stopped, nodes:', displayNodes.length, 'links:', displayLinks.length)
                if (graphRef.current && centerNodeId) {
                  // Center camera on the center node - only on initial load
                  const centerNode = displayNodes.find((n: any) => n.id === centerNodeId)
                  if (centerNode) {
                    console.log('Center node final position:', { x: centerNode.x, y: centerNode.y, z: centerNode.z })
                    // Only set initial camera position if not already set by user
                    if (cameraDistance === 400) {
                      graphRef.current.cameraPosition({ x: 0, y: 0, z: cameraDistance })
                      graphRef.current.zoomToFit(cameraDistance, 20)
                    }
                  }
                } else if (graphRef.current && displayNodes.length > 0 && cameraDistance === 400) {
                  // Only auto-zoom if camera hasn't been manually adjusted
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
                const isCenterNode = node.id === centerNodeId
                const color = isCenterNode ? '#00FFFF' : getNodeColorByType(node) // Bright cyan for center node
                const lockedSize = nodeSizes.get(node.id)
                let size = getNodeSizeByImportance(node, lockedSize)
                
                // Make center node significantly larger
                if (isCenterNode) {
                  size = size * 2.5
                }
                
                const opacity = getNodeOpacity(
                  node.id,
                  nodeHopDistances,
                  centerNodeId,
                  focusedNode?.id || null,
                  filters.focusMode
                )
                
                // Create glowing sphere with opacity
                const geometry = new THREE.SphereGeometry(size / 10, 16, 16)
                const material = new THREE.MeshPhongMaterial({
                  color,
                  transparent: true,
                  opacity: isCenterNode ? 1.0 : opacity * 0.9, // Full opacity for center node
                  emissive: color,
                  emissiveIntensity: isCenterNode ? 1.2 : 0.3, // Very bright glow for center node
                })
                const sphere = new THREE.Mesh(geometry, material)
                
                // Special treatment for center node: add pulsing outer glow
                if (isCenterNode) {
                  const outerGlowGeometry = new THREE.SphereGeometry(size / 7, 16, 16)
                  const outerGlowMaterial = new THREE.MeshBasicMaterial({
                    color: '#00FFFF',
                    transparent: true,
                    opacity: 0.3,
                  })
                  const outerGlow = new THREE.Mesh(outerGlowGeometry, outerGlowMaterial)
                  
                  // Animate pulse for center node
                  const animate = () => {
                    const time = Date.now() * 0.001
                    const scale = 1 + Math.sin(time * 3) * 0.15
                    outerGlow.scale.set(scale, scale, scale)
                    outerGlowMaterial.opacity = 0.3 + Math.sin(time * 3) * 0.2
                    requestAnimationFrame(animate)
                  }
                  animate()
                  
                  const group = new THREE.Group()
                  group.add(outerGlow)
                  group.add(sphere)
                  return group
                }
                
                // Add glow effect for high-risk nodes (non-center)
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
            />
          )}

          {/* Node Details Panel */}
          <NodeDetailsPanel
            node={selectedNode}
            onClose={() => setSelectedNode(null)}
            onLoadNeighbors={handleLoadNeighbors}
            onShowConnections={selectedNode ? () => handleShowConnections(selectedNode) : undefined}
          />

          {/* Connections Diagram Modal */}
          {showConnectionsDiagram && selectedNode && (
            <ConnectionsDiagram
              node={selectedNode}
              connections={nodeConnections}
              onClose={() => setShowConnectionsDiagram(false)}
              onExport={handleExportConnections}
            />
          )}
        </div>
      </div>
    </div>
  )
}
