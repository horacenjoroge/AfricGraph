import { useState } from 'react'
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
  const [error, setError] = useState<string | null>(null)
  const [businessName, setBusinessName] = useState<string | null>(null)

  // Validate business exists before fetching risk
  const validateBusiness = async (id: string): Promise<boolean> => {
    try {
      const response = await axios.get(`/api/v1/businesses/${id}`)
      setBusinessName(response.data.name || id)
      return true
    } catch (error: any) {
      if (error.response?.status === 404) {
        setError(`Business '${id}' not found. Please enter a valid business ID.`)
      } else {
        setError('Failed to validate business. Please try again.')
      }
      return false
    }
  }

  const fetchRiskAnalysis = async () => {
    if (!businessId.trim()) {
      setError('Please enter a business ID')
      return
    }
    
    setError(null)
    setRiskFactors(null)
    setBusinessName(null)
    setLoading(true)
    
    try {
      // First validate business exists
      const isValid = await validateBusiness(businessId.trim())
      if (!isValid) {
        setLoading(false)
        return
      }
      
      // Then fetch risk analysis
      const response = await axios.get(`/api/v1/risk/${businessId.trim()}`)
      
      // Backend returns 'factors' not 'factor_scores'
      const factors = response.data.factors || {}
      setRiskFactors({
        payment_behavior: factors.payment_behavior?.score || 0,
        supplier_concentration: factors.supplier_concentration?.score || 0,
        ownership_complexity: factors.ownership_complexity?.score || 0,
        cashflow_health: factors.cashflow_health?.score || 0,
        network_exposure: factors.network_exposure?.score || 0,
      })
    } catch (error: any) {
      console.error('Failed to fetch risk analysis:', error)
      if (error.response?.status === 404) {
        setError(`Business '${businessId}' not found or has no risk data.`)
      } else if (error.response?.status >= 500) {
        setError('Server error. Please try again later.')
      } else {
        setError(error.response?.data?.detail || 'Failed to fetch risk analysis. Please try again.')
      }
      setRiskFactors(null)
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
              onChange={(e) => {
                setBusinessId(e.target.value)
                setError(null) // Clear error when user types
                setBusinessName(null) // Clear business name when user types
              }}
              onKeyPress={(e) => {
                if (e.key === 'Enter' && !loading && businessId.trim()) {
                  fetchRiskAnalysis()
                }
              }}
              placeholder="Enter business ID (e.g., BIZ001)..."
              className="flex-1 px-4 py-2 bg-deep-space-50 border border-glass-border rounded-lg focus:outline-none focus:ring-2 focus:ring-glow-blue"
            />
            <button
              onClick={fetchRiskAnalysis}
              disabled={loading || !businessId.trim()}
              className="px-6 py-2 bg-blue-500/20 text-blue-400 rounded-lg hover:bg-blue-500/30 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Loading...' : 'Analyze'}
            </button>
          </div>
          {businessName && (
            <p className="text-sm text-gray-400 mt-2">
              Analyzing: <span className="font-mono text-cyan-400">{businessName}</span>
            </p>
          )}
          {error && (
            <div className="mt-2 p-3 bg-red-500/20 border border-red-500/50 rounded-lg">
              <p className="text-sm text-red-400">{error}</p>
            </div>
          )}
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
