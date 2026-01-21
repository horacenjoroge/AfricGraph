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

export function filterGraph(
  nodes: Node[],
  links: Link[],
  filters: GraphFilters
): { nodes: Node[]; links: Link[] } {
  let filteredNodes = [...nodes]
  let filteredLinks = [...links]

  // Filter by node types
  if (filters.nodeTypes.length > 0) {
    filteredNodes = filteredNodes.filter((node) =>
      node.labels.some((label) => filters.nodeTypes.includes(label))
    )
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

  // Filter links to only include connections between filtered nodes
  const nodeIds = new Set(filteredNodes.map((n) => n.id))
  filteredLinks = filteredLinks.filter((link) => {
    const sourceId = typeof link.source === 'string' ? link.source : link.source.id
    const targetId = typeof link.target === 'string' ? link.target : link.target.id
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

export function getNodeSizeByImportance(node: Node): number {
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
