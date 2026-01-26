import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import api from '../utils/api'
import { useNotifications } from '../contexts/NotificationContext'

interface Transaction {
  id: string
  amount: number
  currency: string
  date: string
  type: string
  description: string
  source_provider: string
  people: Array<{ id: string; name: string }>
}

interface Person {
  id: string
  name: string
  transaction_count: number
}

export default function TransactionsPage() {
  const [activeTab, setActiveTab] = useState<'transactions' | 'people'>('transactions')
  const [transactions, setTransactions] = useState<Transaction[]>([])
  const [people, setPeople] = useState<Person[]>([])
  const [loading, setLoading] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [transactionTypeFilter, setTransactionTypeFilter] = useState('')
  const [pagination, setPagination] = useState({
    transactions: { total: 0, limit: 50, offset: 0 },
    people: { total: 0, limit: 50, offset: 0 },
  })
  const { showError } = useNotifications()

  useEffect(() => {
    if (activeTab === 'transactions') {
      fetchTransactions()
    } else {
      fetchPeople()
    }
  }, [activeTab, searchQuery, transactionTypeFilter, pagination.transactions.offset, pagination.people.offset])

  const fetchTransactions = async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams()
      params.append('limit', pagination.transactions.limit.toString())
      params.append('offset', pagination.transactions.offset.toString())
      if (searchQuery) params.append('search', searchQuery)
      if (transactionTypeFilter) params.append('transaction_type', transactionTypeFilter)

      const response = await api.get(`/graph/transactions?${params}`)
      setTransactions(response.data.transactions || [])
      setPagination(prev => ({
        ...prev,
        transactions: {
          ...prev.transactions,
          total: response.data.total || 0,
        },
      }))
    } catch (error: any) {
      console.error('Failed to fetch transactions:', error)
      showError(error.response?.data?.detail || 'Failed to load transactions')
      setTransactions([])
    } finally {
      setLoading(false)
    }
  }

  const fetchPeople = async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams()
      params.append('limit', pagination.people.limit.toString())
      params.append('offset', pagination.people.offset.toString())
      if (searchQuery) params.append('search', searchQuery)

      const response = await api.get(`/graph/people?${params}`)
      setPeople(response.data.people || [])
      setPagination(prev => ({
        ...prev,
        people: {
          ...prev.people,
          total: response.data.total || 0,
        },
      }))
    } catch (error: any) {
      console.error('Failed to fetch people:', error)
      showError(error.response?.data?.detail || 'Failed to load people')
      setPeople([])
    } finally {
      setLoading(false)
    }
  }

  const formatCurrency = (amount: number, currency: string) => {
    return new Intl.NumberFormat('en-KE', {
      style: 'currency',
      currency: currency || 'KES',
      minimumFractionDigits: 2,
    }).format(amount)
  }

  const formatDate = (dateStr: string) => {
    if (!dateStr) return '-'
    try {
      const date = new Date(dateStr)
      return date.toLocaleDateString('en-KE', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
      })
    } catch {
      return dateStr
    }
  }

  const handlePageChange = (tab: 'transactions' | 'people', direction: 'prev' | 'next') => {
    const currentPagination = pagination[tab]
    const newOffset =
      direction === 'next'
        ? currentPagination.offset + currentPagination.limit
        : Math.max(0, currentPagination.offset - currentPagination.limit)

    setPagination(prev => ({
      ...prev,
      [tab]: {
        ...prev[tab],
        offset: newOffset,
      },
    }))
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold font-mono mb-2">Transactions & People</h1>
        <p className="text-gray-400">Browse ingested mobile money transactions and counterparties</p>
      </div>

      {/* Tabs */}
      <div className="glass-panel rounded-lg p-1 flex gap-2">
        <button
          onClick={() => {
            setActiveTab('transactions')
            setSearchQuery('')
            setTransactionTypeFilter('')
          }}
          className={`flex-1 px-4 py-2 rounded-md transition-all font-medium ${
            activeTab === 'transactions'
              ? 'bg-glow-cyan/20 text-glow-cyan border border-glow-cyan/30'
              : 'text-gray-400 hover:text-white'
          }`}
        >
          Transactions ({pagination.transactions.total})
        </button>
        <button
          onClick={() => {
            setActiveTab('people')
            setSearchQuery('')
          }}
          className={`flex-1 px-4 py-2 rounded-md transition-all font-medium ${
            activeTab === 'people'
              ? 'bg-glow-cyan/20 text-glow-cyan border border-glow-cyan/30'
              : 'text-gray-400 hover:text-white'
          }`}
        >
          People ({pagination.people.total})
        </button>
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
              placeholder={activeTab === 'transactions' ? 'Search by description or ID...' : 'Search by name or ID...'}
              className="w-full px-4 py-2 bg-deep-space-50 border border-glass-border rounded-lg focus:outline-none focus:ring-2 focus:ring-glow-blue"
            />
          </div>
          {activeTab === 'transactions' && (
            <div>
              <label className="block text-sm font-medium mb-2">Transaction Type</label>
              <select
                value={transactionTypeFilter}
                onChange={(e) => setTransactionTypeFilter(e.target.value)}
                className="w-full px-4 py-2 bg-deep-space-50 border border-glass-border rounded-lg focus:outline-none focus:ring-2 focus:ring-glow-blue"
              >
                <option value="">All Types</option>
                <option value="payment_in">Payment In</option>
                <option value="payment_out">Payment Out</option>
                <option value="transfer">Transfer</option>
                <option value="withdrawal">Withdrawal</option>
                <option value="deposit">Deposit</option>
              </select>
            </div>
          )}
        </div>
      </div>

      {/* Transactions Table */}
      {activeTab === 'transactions' && (
        <div className="glass-panel rounded-lg overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-deep-space-50">
                <tr>
                  <th className="px-6 py-4 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                    Date
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                    Description
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                    Amount
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                    Type
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                    Counterparty
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-glass-border">
                {loading ? (
                  <tr>
                    <td colSpan={6} className="px-6 py-8 text-center text-gray-400">
                      Loading...
                    </td>
                  </tr>
                ) : transactions.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="px-6 py-8 text-center text-gray-400">
                      No transactions found
                    </td>
                  </tr>
                ) : (
                  transactions.map((tx) => (
                    <motion.tr
                      key={tx.id}
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      className="hover:bg-glass transition-colors"
                    >
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-mono text-gray-400">
                        {formatDate(tx.date)}
                      </td>
                      <td className="px-6 py-4 text-sm max-w-md truncate" title={tx.description}>
                        {tx.description || '-'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap font-medium">
                        {formatCurrency(tx.amount, tx.currency)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className="px-2 py-1 text-xs rounded bg-glow-cyan/20 text-glow-cyan">
                          {tx.type || '-'}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-sm">
                        {tx.people && tx.people.length > 0 ? (
                          <div className="flex flex-col gap-1">
                            {tx.people.slice(0, 2).map((person) => (
                              <span key={person.id} className="text-gray-300">
                                {person.name}
                              </span>
                            ))}
                            {tx.people.length > 2 && (
                              <span className="text-gray-500 text-xs">+{tx.people.length - 2} more</span>
                            )}
                          </div>
                        ) : (
                          <span className="text-gray-500">-</span>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <Link
                          to={`/graph?node=${tx.id}`}
                          className="text-blue-400 hover:text-blue-300 text-sm font-medium"
                        >
                          View →
                        </Link>
                      </td>
                    </motion.tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
          {/* Pagination */}
          {!loading && transactions.length > 0 && (
            <div className="px-6 py-4 border-t border-glass-border flex items-center justify-between">
              <div className="text-sm text-gray-400">
                Showing {pagination.transactions.offset + 1} to{' '}
                {Math.min(pagination.transactions.offset + pagination.transactions.limit, pagination.transactions.total)}{' '}
                of {pagination.transactions.total} transactions
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => handlePageChange('transactions', 'prev')}
                  disabled={pagination.transactions.offset === 0}
                  className="px-4 py-2 bg-deep-space-50 border border-glass-border rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-glass transition-colors"
                >
                  Previous
                </button>
                <button
                  onClick={() => handlePageChange('transactions', 'next')}
                  disabled={pagination.transactions.offset + pagination.transactions.limit >= pagination.transactions.total}
                  className="px-4 py-2 bg-deep-space-50 border border-glass-border rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-glass transition-colors"
                >
                  Next
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* People Table */}
      {activeTab === 'people' && (
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
                    Transactions
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
                ) : people.length === 0 ? (
                  <tr>
                    <td colSpan={4} className="px-6 py-8 text-center text-gray-400">
                      No people found
                    </td>
                  </tr>
                ) : (
                  people.map((person) => (
                    <motion.tr
                      key={person.id}
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      className="hover:bg-glass transition-colors"
                    >
                      <td className="px-6 py-4 whitespace-nowrap font-medium">{person.name}</td>
                      <td className="px-6 py-4 whitespace-nowrap font-mono text-sm text-gray-400">{person.id}</td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className="px-2 py-1 text-xs rounded bg-glow-cyan/20 text-glow-cyan">
                          {person.transaction_count}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <Link
                          to={`/graph?node=${person.id}`}
                          className="text-blue-400 hover:text-blue-300 text-sm font-medium"
                        >
                          View →
                        </Link>
                      </td>
                    </motion.tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
          {/* Pagination */}
          {!loading && people.length > 0 && (
            <div className="px-6 py-4 border-t border-glass-border flex items-center justify-between">
              <div className="text-sm text-gray-400">
                Showing {pagination.people.offset + 1} to{' '}
                {Math.min(pagination.people.offset + pagination.people.limit, pagination.people.total)} of{' '}
                {pagination.people.total} people
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => handlePageChange('people', 'prev')}
                  disabled={pagination.people.offset === 0}
                  className="px-4 py-2 bg-deep-space-50 border border-glass-border rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-glass transition-colors"
                >
                  Previous
                </button>
                <button
                  onClick={() => handlePageChange('people', 'next')}
                  disabled={pagination.people.offset + pagination.people.limit >= pagination.people.total}
                  className="px-4 py-2 bg-deep-space-50 border border-glass-border rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-glass transition-colors"
                >
                  Next
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
