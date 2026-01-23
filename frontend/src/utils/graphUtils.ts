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

interface GraphFilters {
  nodeTypes: string[]
  riskLevel: 'all' | 'high' | 'medium' | 'low'
  minRiskScore: number
  maxRiskScore: number
  showLabels: boolean
  relationshipTypes: string[]
  maxLayers: number
  focusMode: boolean
}

export function calculateNodeDegrees(nodes: Node[], links: Link[]): Node[] {
  const degreeMap = new Map<string, number>()
  
  // Initialize all nodes with degree 0
  nodes.forEach((node) => {
    degreeMap.set(node.id, 0)
  })
  
  // Count connections
  links.forEach((link) => {
    const sourceId = typeof link.source === 'string' ? link.source : link.source.id
    const targetId = typeof link.target === 'string' ? link.target : link.target.id
    
    degreeMap.set(sourceId, (degreeMap.get(sourceId) || 0) + 1)
    degreeMap.set(targetId, (degreeMap.get(targetId) || 0) + 1)
  })
  
  // Update nodes with degree
  return nodes.map((node) => ({
    ...node,
    degree: degreeMap.get(node.id) || 0,
  }))
}

/**
 * Calculate hop distances from center node using BFS
 */
export function calculateHopDistances(
  centerNodeId: string,
  nodes: Node[],
  links: Link[]
): Map<string, number> {
  const distances = new Map<string, number>()
  const visited = new Set<string>()
  const queue: Array<{ id: string; distance: number }> = [{ id: centerNodeId, distance: 0 }]
  
  // Build adjacency list
  const adjacency = new Map<string, Set<string>>()
  nodes.forEach(node => adjacency.set(node.id, new Set()))
  links.forEach(link => {
    const sourceId = typeof link.source === 'string' ? link.source : link.source.id
    const targetId = typeof link.target === 'string' ? link.target : link.target.id
    adjacency.get(sourceId)?.add(targetId)
    adjacency.get(targetId)?.add(sourceId)
  })
  
  // BFS to calculate distances
  while (queue.length > 0) {
    const { id, distance } = queue.shift()!
    if (visited.has(id)) continue
    visited.add(id)
    distances.set(id, distance)
    
    const neighbors = adjacency.get(id) || new Set()
    neighbors.forEach(neighborId => {
      if (!visited.has(neighborId)) {
        queue.push({ id: neighborId, distance: distance + 1 })
      }
    })
  }
  
  return distances
}

export function filterGraph(
  nodes: Node[],
  links: Link[],
  filters: GraphFilters,
  centerNodeId: string | null = null,
  hopDistances: Map<string, number> = new Map(),
  focusedNodeId: string | null = null
): { nodes: Node[]; links: Link[] } {
  let filteredNodes = [...nodes]
  let filteredLinks = [...links]

  // Progressive disclosure: filter by max layers (hop distance)
  // Only apply if we have hop distances calculated and center node exists
  // Treat maxLayers >= 5 as "show all" (no limit)
  if (centerNodeId && filters.maxLayers > 0 && filters.maxLayers < 5 && hopDistances.size > 0) {
    const centerDistance = hopDistances.get(centerNodeId)
    // Only apply layer filter if center node has a valid distance (0)
    if (centerDistance === 0) {
      filteredNodes = filteredNodes.filter((node) => {
        if (node.id === centerNodeId) return true // Always show center node
        const distance = hopDistances.get(node.id)
        // Include nodes within maxLayers distance (0 = center, 1 = direct, 2 = 1-hop, etc.)
        return distance !== undefined && distance <= filters.maxLayers
      })
    }
    // If center node distance is not 0, don't apply layer filter (show all)
  }
  // If maxLayers >= 5, don't apply layer filter (show all nodes)

  // Focus mode: show only focused node and its direct connections
  if (filters.focusMode && focusedNodeId) {
    const focusedNodeIds = new Set([focusedNodeId])
    filteredLinks.forEach(link => {
      const sourceId = typeof link.source === 'string' ? link.source : link.source.id
      const targetId = typeof link.target === 'string' ? link.target : link.target.id
      if (sourceId === focusedNodeId) focusedNodeIds.add(targetId)
      if (targetId === focusedNodeId) focusedNodeIds.add(sourceId)
    })
    filteredNodes = filteredNodes.filter(node => focusedNodeIds.has(node.id))
  }

  // Filter by node types - but ALWAYS include center node
  // Do this BEFORE relationship filtering so we can find all connected nodes
  if (filters.nodeTypes.length > 0) {
    filteredNodes = filteredNodes.filter((node) => {
      // Always include center node regardless of type filter
      if (centerNodeId && node.id === centerNodeId) return true
      return node.labels.some((label) => filters.nodeTypes.includes(label))
    })
  }

  // Filter by relationship types - but keep ALL links connected to center node
  if (filters.relationshipTypes.length > 0) {
    filteredLinks = filteredLinks.filter((link) => {
      const sourceId = typeof link.source === 'string' ? link.source : link.source.id
      const targetId = typeof link.target === 'string' ? link.target : link.target.id
      
      // Always include links connected to center node, regardless of relationship type filter
      if (centerNodeId && (sourceId === centerNodeId || targetId === centerNodeId)) {
        return true
      }
      
      // For other links, apply the relationship type filter
      return filters.relationshipTypes.includes(link.type)
    })
  }

  // Filter by risk level
  if (filters.riskLevel !== 'all') {
    filteredNodes = filteredNodes.filter((node) => {
      if (node.riskScore === undefined) return false
      switch (filters.riskLevel) {
        case 'high':
          return node.riskScore >= 80
        case 'medium':
          return node.riskScore >= 60 && node.riskScore < 80
        case 'low':
          return node.riskScore < 60
        default:
          return true
      }
    })
  }

  // Filter by risk score range
  filteredNodes = filteredNodes.filter((node) => {
    if (node.riskScore === undefined) return true
    return (
      node.riskScore >= filters.minRiskScore &&
      node.riskScore <= filters.maxRiskScore
    )
  })

  // BEFORE filtering links by node membership, find all nodes connected to center from ORIGINAL links
  // This ensures we include connected nodes even if they were filtered out by node type
  const nodeIds = new Set(filteredNodes.map((n) => n.id))
  if (centerNodeId && nodeIds.has(centerNodeId)) {
    // Check ORIGINAL links (before relationship type filtering) to find all nodes connected to center
    const allCenterLinks = links.filter((link) => {
      const sourceId = typeof link.source === 'string' ? link.source : link.source.id
      const targetId = typeof link.target === 'string' ? link.target : link.target.id
      return sourceId === centerNodeId || targetId === centerNodeId
    })
    
    // Find nodes connected to center that aren't in filtered nodes
    const missingNodes = new Set<string>()
    allCenterLinks.forEach(link => {
      const sourceId = typeof link.source === 'string' ? link.source : link.source.id
      const targetId = typeof link.target === 'string' ? link.target : link.target.id
      if (sourceId === centerNodeId && !nodeIds.has(targetId)) {
        missingNodes.add(targetId)
      } else if (targetId === centerNodeId && !nodeIds.has(sourceId)) {
        missingNodes.add(sourceId)
      }
    })
    
    // Add missing nodes back to filtered nodes
    if (missingNodes.size > 0) {
      const allNodesMap = new Map(nodes.map(n => [n.id, n]))
      missingNodes.forEach(nodeId => {
        const node = allNodesMap.get(nodeId)
        if (node && !filteredNodes.find(n => n.id === nodeId)) {
          filteredNodes.push(node)
          nodeIds.add(nodeId)
        }
      })
    }
  }
  
  // Now filter links to only include connections between filtered nodes
  // BUT always include links connected to center node (even if target node was just added)
  filteredLinks = filteredLinks.filter((link) => {
    const sourceId = typeof link.source === 'string' ? link.source : link.source.id
    const targetId = typeof link.target === 'string' ? link.target : link.target.id
    
    // Always include links connected to center node
    if (centerNodeId && (sourceId === centerNodeId || targetId === centerNodeId)) {
      // Include the link if at least one end (center node) is in filtered nodes
      return nodeIds.has(sourceId) || nodeIds.has(targetId)
    }
    
    // For other links, both nodes must be in filtered nodes
    return nodeIds.has(sourceId) && nodeIds.has(targetId)
  })

  return { nodes: filteredNodes, links: filteredLinks }
}

export function getNodeColorByType(node: Node): string {
  // Color by primary label
  const primaryLabel = node.labels[0] || ''
  
  switch (primaryLabel) {
    case 'Business':
      // Color by risk if available
      if (node.riskScore !== undefined) {
        if (node.riskScore >= 80) return '#EF4444' // Red - high risk
        if (node.riskScore >= 60) return '#F59E0B' // Yellow - medium risk
        return '#10B981' // Green - low risk
      }
      return '#3B82F6' // Blue - default business
    case 'Person':
      return '#8B5CF6' // Purple
    case 'Transaction':
      return '#06B6D4' // Cyan
    case 'Invoice':
      return '#EC4899' // Pink
    default:
      return '#6B7280' // Gray
  }
}

export function getNodeSizeByImportance(node: Node, lockedSize?: number): number {
  // Use locked size if provided (prevents Framer Motion size jumps)
  if (lockedSize !== undefined) {
    return lockedSize
  }

  // Base size
  let size = 4

  // Increase size by degree (connections)
  if (node.degree !== undefined) {
    size += Math.min(node.degree * 0.5, 5) // Cap at +5
  }

  // Increase size by risk score
  if (node.riskScore !== undefined) {
    if (node.riskScore >= 80) {
      size += 3 // High risk nodes are larger
    } else if (node.riskScore >= 60) {
      size += 1.5
    }
  }

  // Increase size for Business nodes
  if (node.labels.includes('Business')) {
    size += 1
  }

  return Math.min(size, 12) // Cap maximum size
}

/**
 * Get node opacity based on hop distance (visual hierarchy)
 */
export function getNodeOpacity(
  nodeId: string,
  hopDistances: Map<string, number>,
  centerNodeId: string | null,
  focusedNodeId: string | null,
  focusMode: boolean
): number {
  if (focusMode && focusedNodeId) {
    // In focus mode, highlight focused node and its connections
    if (nodeId === focusedNodeId) return 1.0
    const distance = hopDistances.get(nodeId)
    if (distance === 1) return 0.8 // Direct connections
    return 0.3 // Everything else dimmed
  }
  
  if (centerNodeId && nodeId === centerNodeId) {
    return 1.0 // Center node always fully visible
  }
  
  const distance = hopDistances.get(nodeId)
  if (distance === undefined) return 0.5
  
  // Fade based on distance: layer 1 = 0.9, layer 2 = 0.7, layer 3+ = 0.5
  return Math.max(0.5, 1.0 - (distance - 1) * 0.2)
}

/**
 * Get link opacity based on relationship type and focus
 */
export function getLinkOpacity(
  link: Link,
  focusedNodeId: string | null,
  focusMode: boolean
): number {
  if (focusMode && focusedNodeId) {
    const sourceId = typeof link.source === 'string' ? link.source : link.source.id
    const targetId = typeof link.target === 'string' ? link.target : link.target.id
    if (sourceId === focusedNodeId || targetId === focusedNodeId) {
      return 0.9 // Highlight connections to focused node
    }
    return 0.2 // Dim other connections
  }
  return 0.7 // Default opacity - increased for better visibility
}
