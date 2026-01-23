import { useState } from 'react'

interface GraphControlsProps {
  onFilterChange: (filters: GraphFilters) => void
  onLoadSubgraph: (nodeId: string, maxHops: number) => void
  availableRelationshipTypes?: string[]
}

export interface GraphFilters {
  nodeTypes: string[]
  riskLevel: 'all' | 'high' | 'medium' | 'low'
  minRiskScore: number
  maxRiskScore: number
  showLabels: boolean
  relationshipTypes: string[] // Filter by relationship types
  maxLayers: number // Progressive disclosure - show up to N layers
  focusMode: boolean // Focus on selected node only
}

export default function GraphControls({ onFilterChange, onLoadSubgraph, availableRelationshipTypes = [] }: GraphControlsProps) {
  const [filters, setFilters] = useState<GraphFilters>({
    nodeTypes: [],
    riskLevel: 'all',
    minRiskScore: 0,
    maxRiskScore: 100,
    showLabels: true,
    relationshipTypes: [],
    maxLayers: 5, // Show all layers by default (user can reduce if needed)
    focusMode: false,
  })
  const [subgraphNodeId, setSubgraphNodeId] = useState('')
  const [maxHops, setMaxHops] = useState(2)

  const handleFilterChange = (newFilters: Partial<GraphFilters>) => {
    const updated = { ...filters, ...newFilters }
    setFilters(updated)
    onFilterChange(updated)
  }

  return (
    <div className="glass-panel-strong rounded-lg p-6 space-y-4">
      <h3 className="text-lg font-bold mb-4">Graph Controls</h3>

      {/* Node Type Filter */}
      <div>
        <label className="block text-sm font-medium mb-2">Node Types</label>
        <div className="space-y-2">
          {['Business', 'Person', 'Transaction', 'Invoice'].map((type) => (
            <label key={type} className="flex items-center">
              <input
                type="checkbox"
                checked={filters.nodeTypes.includes(type)}
                onChange={(e) => {
                  const newTypes = e.target.checked
                    ? [...filters.nodeTypes, type]
                    : filters.nodeTypes.filter((t) => t !== type)
                  handleFilterChange({ nodeTypes: newTypes })
                }}
                className="mr-2"
              />
              <span className="text-sm">{type}</span>
            </label>
          ))}
        </div>
      </div>

      {/* Risk Level Filter */}
      <div>
        <label className="block text-sm font-medium mb-2">Risk Level</label>
        <select
          value={filters.riskLevel}
          onChange={(e) => handleFilterChange({ riskLevel: e.target.value as any })}
          className="w-full px-3 py-2 bg-deep-space-50 border border-glass-border rounded-lg"
        >
          <option value="all">All</option>
          <option value="high">High (≥80)</option>
          <option value="medium">Medium (60-79)</option>
          <option value="low">Low (&lt;60)</option>
        </select>
      </div>

      {/* Risk Score Range */}
      <div>
        <label className="block text-sm font-medium mb-2">Risk Score Range</label>
        <div className="grid grid-cols-2 gap-2">
          <input
            type="number"
            min="0"
            max="100"
            value={filters.minRiskScore}
            onChange={(e) => handleFilterChange({ minRiskScore: parseInt(e.target.value) })}
            className="px-3 py-2 bg-deep-space-50 border border-glass-border rounded-lg"
            placeholder="Min"
          />
          <input
            type="number"
            min="0"
            max="100"
            value={filters.maxRiskScore}
            onChange={(e) => handleFilterChange({ maxRiskScore: parseInt(e.target.value) })}
            className="px-3 py-2 bg-deep-space-50 border border-glass-border rounded-lg"
            placeholder="Max"
          />
        </div>
      </div>

      {/* Show Labels Toggle */}
      <div>
        <label className="flex items-center">
          <input
            type="checkbox"
            checked={filters.showLabels}
            onChange={(e) => handleFilterChange({ showLabels: e.target.checked })}
            className="mr-2"
          />
          <span className="text-sm">Show Relationship Labels</span>
        </label>
      </div>

      {/* Relationship Type Filter */}
      <div>
        <label className="block text-sm font-medium mb-2">Relationship Types</label>
        {availableRelationshipTypes.length === 0 ? (
          <div className="text-xs text-gray-400">Load a subgraph to see relationship types</div>
        ) : (
          <div className="space-y-2 max-h-32 overflow-y-auto">
            {availableRelationshipTypes.map((type) => (
            <label key={type} className="flex items-center">
              <input
                type="checkbox"
                checked={filters.relationshipTypes.includes(type)}
                onChange={(e) => {
                  const newTypes = e.target.checked
                    ? [...filters.relationshipTypes, type]
                    : filters.relationshipTypes.filter((t) => t !== type)
                  handleFilterChange({ relationshipTypes: newTypes })
                }}
                className="mr-2"
              />
              <span className="text-sm">{type}</span>
            </label>
            ))}
          </div>
        )}
        {filters.relationshipTypes.length > 0 && (
          <button
            onClick={() => handleFilterChange({ relationshipTypes: [] })}
            className="mt-2 text-xs text-blue-400 hover:text-blue-300"
          >
            Clear all
          </button>
        )}
      </div>

      {/* Progressive Disclosure - Max Layers */}
      <div>
        <label className="block text-sm font-medium mb-2">
          Show Layers: {filters.maxLayers === 5 ? 'All' : filters.maxLayers}
        </label>
        <input
          type="range"
          min="1"
          max="5"
          value={filters.maxLayers}
          onChange={(e) => handleFilterChange({ maxLayers: parseInt(e.target.value) })}
          className="w-full"
        />
        <div className="text-xs text-gray-400 mt-1">
          {filters.maxLayers === 5 
            ? 'Showing all layers (no limit)'
            : `Layer ${filters.maxLayers} = Center + up to ${filters.maxLayers} hops away`
          }
        </div>
      </div>

      {/* Focus Mode Toggle */}
      <div>
        <label className="flex items-center">
          <input
            type="checkbox"
            checked={filters.focusMode}
            onChange={(e) => handleFilterChange({ focusMode: e.target.checked })}
            className="mr-2"
          />
          <span className="text-sm">Focus Mode</span>
        </label>
        <div className="text-xs text-gray-400 mt-1 ml-6">
          Click a node to highlight only its connections
        </div>
      </div>

      {/* Subgraph Loader */}
      <div className="pt-4 border-t border-glass-border">
        <label className="block text-sm font-medium mb-2">Load Subgraph</label>
        <div className="space-y-2">
          <input
            type="text"
            value={subgraphNodeId}
            onChange={(e) => setSubgraphNodeId(e.target.value)}
            placeholder="Node ID"
            className="w-full px-3 py-2 bg-deep-space-50 border border-glass-border rounded-lg"
          />
          <div className="flex gap-2">
            <input
              type="number"
              min="1"
              max="5"
              value={maxHops}
              onChange={(e) => setMaxHops(parseInt(e.target.value))}
              className="w-20 px-3 py-2 bg-deep-space-50 border border-glass-border rounded-lg"
              placeholder="Hops"
            />
            <button
              onClick={() => onLoadSubgraph(subgraphNodeId, maxHops)}
              className="flex-1 px-4 py-2 bg-blue-500/20 text-blue-400 rounded-lg hover:bg-blue-500/30 transition-colors"
            >
              Load
            </button>
          </div>
        </div>
      </div>

    </div>
  )
}
