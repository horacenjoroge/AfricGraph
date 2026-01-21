import { useState, useEffect } from 'react'
import { RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, ResponsiveContainer } from 'recharts'
import axios from 'axios'

interface RiskFactors {
  payment_behavior: number
  supplier_concentration: number
  ownership_complexity: number
  cashflow_health: number
  network_exposure: number
}

export default function RiskAnalysisPage() {
  const [riskFactors, setRiskFactors] = useState<RiskFactors | null>(null)
  const [loading, setLoading] = useState(false)
  const [businessId, setBusinessId] = useState('')

  const fetchRiskAnalysis = async () => {
    if (!businessId) return
    
    setLoading(true)
    try {
      const response = await axios.get(`/api/v1/risk/${businessId}`)
      // Transform response data to match RiskFactors interface
      const factors = response.data.factor_scores || {}
      setRiskFactors({
        payment_behavior: factors.payment_behavior?.score || 0,
        supplier_concentration: factors.supplier_concentration?.score || 0,
        ownership_complexity: factors.ownership_complexity?.score || 0,
        cashflow_health: factors.cashflow_health?.score || 0,
        network_exposure: factors.network_exposure?.score || 0,
      })
    } catch (error) {
      console.error('Failed to fetch risk analysis:', error)
    } finally {
      setLoading(false)
    }
  }

  const chartData = riskFactors ? [
    { factor: 'Payment', value: riskFactors.payment_behavior },
    { factor: 'Suppliers', value: riskFactors.supplier_concentration },
    { factor: 'Ownership', value: riskFactors.ownership_complexity },
    { factor: 'Cashflow', value: riskFactors.cashflow_health },
    { factor: 'Network', value: riskFactors.network_exposure },
  ] : []

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold font-mono mb-2">Risk Analysis</h1>
        <p className="text-gray-400">Detailed risk breakdown by factor</p>
      </div>

      <div className="glass-panel rounded-lg p-6">
        <div className="mb-4">
          <label className="block text-sm font-medium mb-2">Business ID</label>
          <div className="flex gap-2">
            <input
              type="text"
              value={businessId}
              onChange={(e) => setBusinessId(e.target.value)}
              placeholder="Enter business ID..."
              className="flex-1 px-4 py-2 bg-deep-space-50 border border-glass-border rounded-lg focus:outline-none focus:ring-2 focus:ring-glow-blue"
            />
            <button
              onClick={fetchRiskAnalysis}
              disabled={loading}
              className="px-6 py-2 bg-blue-500/20 text-blue-400 rounded-lg hover:bg-blue-500/30 transition-colors disabled:opacity-50"
            >
              {loading ? 'Loading...' : 'Analyze'}
            </button>
          </div>
        </div>
      </div>

      {riskFactors && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Radar Chart */}
          <div className="glass-panel rounded-lg p-6">
            <h2 className="text-xl font-bold mb-4">Risk Factor Radar</h2>
            <ResponsiveContainer width="100%" height={400}>
              <RadarChart data={chartData}>
                <PolarGrid />
                <PolarAngleAxis dataKey="factor" />
                <PolarRadiusAxis angle={90} domain={[0, 100]} />
                <Radar
                  name="Risk"
                  dataKey="value"
                  stroke="#3B82F6"
                  fill="#3B82F6"
                  fillOpacity={0.6}
                />
              </RadarChart>
            </ResponsiveContainer>
          </div>

          {/* Risk Factor Details */}
          <div className="glass-panel rounded-lg p-6">
            <h2 className="text-xl font-bold mb-4">Factor Breakdown</h2>
            <div className="space-y-4">
              {Object.entries(riskFactors).map(([factor, score]) => (
                <div key={factor}>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium capitalize">
                      {factor.replace('_', ' ')}
                    </span>
                    <span className={`font-mono font-bold ${
                      score >= 80 ? 'text-red-400' :
                      score >= 60 ? 'text-yellow-400' :
                      'text-green-400'
                    }`}>
                      {score}
                    </span>
                  </div>
                  <div className="w-full bg-deep-space-50 rounded-full h-2">
                    <div
                      className={`h-2 rounded-full ${
                        score >= 80 ? 'bg-red-400' :
                        score >= 60 ? 'bg-yellow-400' :
                        'bg-green-400'
                      }`}
                      style={{ width: `${score}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
