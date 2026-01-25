import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import axios from 'axios'
import { useNotifications } from '../contexts/NotificationContext'

interface Business {
  id: string
  name: string
  sector?: string
  registration_number?: string
}

export default function BusinessSearchPage() {
  const [businesses, setBusinesses] = useState<Business[]>([])
  const [loading, setLoading] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [sectorFilter, setSectorFilter] = useState('')
  const { showError, showInfo } = useNotifications()

  useEffect(() => {
    // Only fetch if there's a search query or filter, or on initial load
    if (searchQuery || sectorFilter) {
      fetchBusinesses()
    } else {
      // On initial load without filters, fetch all businesses silently
      fetchBusinessesSilent()
    }
  }, [searchQuery, sectorFilter])

  const fetchBusinessesSilent = async () => {
    setLoading(true)
    try {
      const tenantId = localStorage.getItem('current_tenant_id')
      if (!tenantId) {
        console.warn('No tenant selected - businesses may not be visible')
        setBusinesses([])
        return
      }
      
      const response = await axios.get(`/api/v1/businesses/search`, {
        headers: { 'X-Tenant-ID': tenantId }
      })
      const businesses = response.data.businesses || []
      setBusinesses(businesses)
    } catch (error: any) {
      console.error('Failed to fetch businesses:', error)
      // Silent failure on initial load - don't show notifications
      setBusinesses([])
    } finally {
      setLoading(false)
    }
  }

  const fetchBusinesses = async () => {
    // Only fetch if there's actually a search query or filter
    if (!searchQuery && !sectorFilter) {
      return
    }

    setLoading(true)
    try {
      const tenantId = localStorage.getItem('current_tenant_id')
      if (!tenantId) {
        showError('Please select a tenant to search businesses')
        setBusinesses([])
        return
      }
      
      const params = new URLSearchParams()
      if (searchQuery) params.append('query', searchQuery)
      if (sectorFilter) params.append('sector', sectorFilter)
      
      const response = await axios.get(`/api/v1/businesses/search?${params}`, {
        headers: { 'X-Tenant-ID': tenantId }
      })
      const businesses = response.data.businesses || []
      setBusinesses(businesses)
      
      if (businesses.length === 0 && (searchQuery || sectorFilter)) {
        // Show specific message with the search query
        const searchTerm = searchQuery || sectorFilter
        showInfo(`No businesses found matching "${searchTerm}"`)
      }
    } catch (error: any) {
      console.error('Failed to fetch businesses:', error)
      
      // Check if it's a 404 with a specific business ID/name in the error
      if (error.response?.status === 404) {
        const errorDetail = error.response?.data?.detail || ''
        
        // If the error mentions a specific business ID/name, show that
        if (errorDetail.includes("Business '") || errorDetail.includes('not found')) {
          // Extract business name/ID from error message
          const match = errorDetail.match(/Business '([^']+)' not found/)
          if (match && match[1]) {
            showError(`Business "${match[1]}" not found`)
          } else {
            showError(errorDetail || 'Business not found')
          }
        } else {
          // Generic 404 - might be endpoint not found
          showError('Search endpoint not available. Please check if the API is running.')
        }
      } else if (error.response?.status === 403) {
        showError('Access denied. Please check your tenant settings.')
      } else {
        // Check if error has a specific business name/ID
        const errorDetail = error.response?.data?.detail || ''
        if (errorDetail.includes("Business '") || errorDetail.includes('not found')) {
          const match = errorDetail.match(/Business '([^']+)' not found/)
          if (match && match[1]) {
            showError(`Business "${match[1]}" not found`)
          } else {
            showError(errorDetail)
          }
        } else {
          showError(errorDetail || 'Failed to search businesses. Please try again.')
        }
      }
      setBusinesses([])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold font-mono mb-2">Business Search</h1>
        <p className="text-gray-400">Search and filter businesses</p>
      </div>

      {/* Search and Filters */}
      <div className="glass-panel rounded-lg p-6 space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium mb-2">Search</label>
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search by name or ID..."
              className="w-full px-4 py-2 bg-deep-space-50 border border-glass-border rounded-lg focus:outline-none focus:ring-2 focus:ring-glow-blue"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-2">Sector</label>
            <select
              value={sectorFilter}
              onChange={(e) => setSectorFilter(e.target.value)}
              className="w-full px-4 py-2 bg-deep-space-50 border border-glass-border rounded-lg focus:outline-none focus:ring-2 focus:ring-glow-blue"
            >
              <option value="">All Sectors</option>
              <option value="Technology">Technology</option>
              <option value="Finance">Finance</option>
              <option value="Retail">Retail</option>
              <option value="Manufacturing">Manufacturing</option>
            </select>
          </div>
        </div>
      </div>

      {/* Results Table */}
      <div className="glass-panel rounded-lg overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-deep-space-50">
              <tr>
                <th className="px-6 py-4 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                  Name
                </th>
                <th className="px-6 py-4 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                  ID
                </th>
                <th className="px-6 py-4 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                  Sector
                </th>
                <th className="px-6 py-4 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-glass-border">
              {loading ? (
                <tr>
                  <td colSpan={4} className="px-6 py-8 text-center text-gray-400">
                    Loading...
                  </td>
                </tr>
              ) : businesses.length === 0 ? (
                <tr>
                  <td colSpan={4} className="px-6 py-8 text-center text-gray-400">
                    No businesses found
                  </td>
                </tr>
              ) : (
                businesses.map((business) => (
                  <motion.tr
                    key={business.id}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="hover:bg-glass transition-colors"
                  >
                    <td className="px-6 py-4 whitespace-nowrap font-medium">
                      {business.name}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap font-mono text-sm text-gray-400">
                      {business.id}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-400">
                      {business.sector || '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <Link
                        to={`/businesses/${business.id}`}
                        className="text-blue-400 hover:text-blue-300 text-sm font-medium"
                      >
                        View Details →
                      </Link>
                    </td>
                  </motion.tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
