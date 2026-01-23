import React from 'react'

interface LegendItem {
  color: string
  label: string
  description?: string
}

export default function GraphLegend() {
  const nodeTypeItems: LegendItem[] = [
    {
      color: '#3B82F6',
      label: 'Business',
      description: 'Default (no risk score)',
    },
    {
      color: '#EF4444',
      label: 'Business (High Risk)',
      description: 'Risk score ≥ 80',
    },
    {
      color: '#F59E0B',
      label: 'Business (Medium Risk)',
      description: 'Risk score 60-79',
    },
    {
      color: '#10B981',
      label: 'Business (Low Risk)',
      description: 'Risk score < 60',
    },
    {
      color: '#8B5CF6',
      label: 'Person',
    },
    {
      color: '#06B6D4',
      label: 'Transaction',
    },
    {
      color: '#EC4899',
      label: 'Invoice',
    },
    {
      color: '#6B7280',
      label: 'Other',
    },
  ]

  return (
    <div className="glass-panel border border-glass-border rounded-lg p-4 mb-4">
      <h3 className="text-sm font-bold font-mono text-glow-cyan mb-3 uppercase tracking-wider">
        Node Color Guide
      </h3>
      <div className="space-y-2">
        {nodeTypeItems.map((item, index) => (
          <div key={index} className="flex items-center gap-3 text-sm">
            <div
              className="w-4 h-4 rounded-full flex-shrink-0 border border-white/20"
              style={{ backgroundColor: item.color }}
            />
            <div className="flex-1">
              <div className="text-gray-200 font-medium">{item.label}</div>
              {item.description && (
                <div className="text-xs text-gray-400">{item.description}</div>
              )}
            </div>
          </div>
        ))}
      </div>
      
      <div className="mt-4 pt-4 border-t border-glass-border">
        <div className="text-xs text-gray-400 space-y-1">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-white/20 border border-white/40" />
            <span>Node size indicates importance (connections + risk)</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-white/10 border border-white/20" />
            <span>Faded nodes are further from center</span>
          </div>
        </div>
      </div>
    </div>
  )
}
