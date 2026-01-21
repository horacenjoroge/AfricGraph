import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import axios from 'axios'

interface Business {
  id: string
  name: string
  sector?: string
  registration_number?: string
}

export default function BusinessDetailPage() {
  const { id } = useParams<{ id: string }>()
  const [business, setBusiness] = useState<Business | null>(null)
  const [riskScore, setRiskScore] = useState<number | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (id) {
      fetchBusinessDetails()
      fetchRiskScore()
    }
  }, [id])

  const fetchBusinessDetails = async () => {
    try {
      const response = await axios.get(`/api/v1/businesses/${id}`)
      setBusiness(response.data)
    } catch (error) {
      console.error('Failed to fetch business:', error)
    } finally {
      setLoading(false)
    }
  }

  const fetchRiskScore = async () => {
    try {
      const response = await axios.get(`/api/v1/risk/${id}`)
      setRiskScore(response.data.risk_score || null)
    } catch (error) {
      console.error('Failed to fetch risk score:', error)
    }
  }

  if (loading) {
    return <div className="text-center py-12 text-gray-400">Loading...</div>
  }

  if (!business) {
    return <div className="text-center py-12 text-red-400">Business not found</div>
  }

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.3 }}
      className="space-y-6"
    >
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold font-mono mb-2">{business.name}</h1>
          <p className="text-gray-400 font-mono text-sm">ID: {business.id}</p>
        </div>
        <Link
          to="/businesses"
          className="px-4 py-2 glass-panel rounded-lg hover:bg-glass transition-colors"
        >
          ← Back to Search
        </Link>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Business Info */}
        <div className="lg:col-span-2 space-y-6">
          <div className="glass-panel rounded-lg p-6">
            <h2 className="text-xl font-bold mb-4">Business Information</h2>
            <dl className="space-y-3">
              <div>
                <dt className="text-sm text-gray-400">Name</dt>
                <dd className="text-lg font-medium">{business.name}</dd>
              </div>
              {business.registration_number && (
                <div>
                  <dt className="text-sm text-gray-400">Registration Number</dt>
                  <dd className="text-lg font-mono">{business.registration_number}</dd>
                </div>
              )}
              {business.sector && (
                <div>
                  <dt className="text-sm text-gray-400">Sector</dt>
                  <dd className="text-lg">{business.sector}</dd>
                </div>
              )}
            </dl>
          </div>

          {/* Graph Visualization Placeholder */}
          <div className="glass-panel rounded-lg p-6">
            <h2 className="text-xl font-bold mb-4">Business Network</h2>
            <div className="h-64 flex items-center justify-center text-gray-400 border border-glass-border rounded-lg">
              Graph visualization placeholder
            </div>
          </div>
        </div>

        {/* Risk Score */}
        <div className="space-y-6">
          <div className="glass-panel rounded-lg p-6">
            <h2 className="text-xl font-bold mb-4">Risk Score</h2>
            {riskScore !== null ? (
              <div className="text-center">
                <div className={`text-6xl font-mono font-bold mb-2 ${
                  riskScore >= 80 ? 'text-red-400 glow-red' :
                  riskScore >= 60 ? 'text-yellow-400' :
                  'text-green-400 glow-green'
                }`}>
                  {riskScore}
                </div>
                <div className="text-sm text-gray-400">out of 100</div>
              </div>
            ) : (
              <div className="text-center text-gray-400">No risk data available</div>
            )}
          </div>
        </div>
      </div>
    </motion.div>
  )
}
