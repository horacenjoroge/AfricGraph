import { useState, useRef } from 'react'
import { motion } from 'framer-motion'
import axios from 'axios'
import { useNotifications } from '../../contexts/NotificationContext'

interface IngestionJob {
  job_id: string
  job_type: string
  status: string
  created_at: string
  started_at?: string
  completed_at?: string
  error_message?: string
  stats?: Record<string, any>
}

export default function IngestionManagement() {
  const [jobs, setJobs] = useState<IngestionJob[]>([])
  const [loading, setLoading] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [showMobileMoneyForm, setShowMobileMoneyForm] = useState(false)
  const [showAccountingForm, setShowAccountingForm] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [mobileMoneyForm, setMobileMoneyForm] = useState({
    path: '',
    provider: 'mpesa',
    currency: 'KES',
  })
  const [accountingForm, setAccountingForm] = useState({
    connector: 'xero',
    modified_after: '',
  })
  const { showSuccess, showError } = useNotifications()

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      if (!file.name.endsWith('.csv')) {
        showError('Please select a CSV file')
        return
      }
      setSelectedFile(file)
      // Show filename in the form
      setMobileMoneyForm({ ...mobileMoneyForm, path: file.name })
    }
  }

  const uploadFile = async (file: File): Promise<string> => {
    const token = localStorage.getItem('auth_token')
    const formData = new FormData()
    formData.append('file', file)

    const response = await axios.post(
      '/api/v1/ingest/upload-csv',
      formData,
      {
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'multipart/form-data',
        },
      }
    )

    return response.data.file_path
  }

  const triggerMobileMoney = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!selectedFile) {
      showError('Please select a CSV file')
      return
    }

    try {
      setLoading(true)
      setUploading(true)
      
      // First upload the file
      const serverPath = await uploadFile(selectedFile)
      
      setUploading(false)
      
      // Then trigger ingestion with server path
      const token = localStorage.getItem('auth_token')
      const response = await axios.post(
        '/api/v1/ingest/mobile-money',
        {
          path: serverPath,
          provider: mobileMoneyForm.provider,
          currency: mobileMoneyForm.currency,
        },
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      )
      
      showSuccess(`Mobile money ingestion started. Job ID: ${response.data.job_id}. Check the Workflows page to monitor progress.`)
      setShowMobileMoneyForm(false)
      setMobileMoneyForm({ path: '', provider: 'mpesa', currency: 'KES' })
      setSelectedFile(null)
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
      
      // Poll for job status
      pollJobStatus(response.data.job_id)
    } catch (error: any) {
      console.error('Failed to trigger mobile money ingestion:', error)
      showError(error.response?.data?.detail || 'Failed to start ingestion')
    } finally {
      setLoading(false)
      setUploading(false)
    }
  }

  const triggerAccounting = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      setLoading(true)
      const token = localStorage.getItem('auth_token')
      const response = await axios.post(
        '/api/v1/ingest/accounting',
        {
          ...accountingForm,
          modified_after: accountingForm.modified_after || undefined,
        },
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      )
      showSuccess(`Accounting ingestion started. Job ID: ${response.data.job_id}. Check the Workflows page to monitor progress.`)
      setShowAccountingForm(false)
      setAccountingForm({ connector: 'xero', modified_after: '' })
      // Poll for job status
      pollJobStatus(response.data.job_id)
    } catch (error: any) {
      console.error('Failed to trigger accounting ingestion:', error)
      showError(error.response?.data?.detail || 'Failed to start ingestion')
    } finally {
      setLoading(false)
    }
  }

  const pollJobStatus = async (jobId: string) => {
    // Poll job status every 2 seconds
    const interval = setInterval(async () => {
      try {
        const token = localStorage.getItem('auth_token')
        const response = await axios.get(`/api/v1/ingest/jobs/${jobId}`, {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        })
        const job = response.data
        updateJobInList(job)

        if (job.status === 'completed' || job.status === 'success' || job.status === 'failed') {
          clearInterval(interval)
          if (job.status === 'completed' || job.status === 'success') {
            showSuccess(`Ingestion job ${jobId} completed successfully`)
          } else {
            showError(`Ingestion job ${jobId} failed: ${job.error_message || 'Unknown error'}`)
          }
        }
      } catch (error) {
        console.error('Failed to poll job status:', error)
        clearInterval(interval)
      }
    }, 2000)

    // Stop polling after 5 minutes
    setTimeout(() => clearInterval(interval), 5 * 60 * 1000)
  }

  const updateJobInList = (updatedJob: IngestionJob) => {
    setJobs((prev) => {
      const existing = prev.find((j) => j.job_id === updatedJob.job_id)
      if (existing) {
        return prev.map((j) => (j.job_id === updatedJob.job_id ? updatedJob : j))
      } else {
        return [updatedJob, ...prev]
      }
    })
  }

  const getJobStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-500/20 text-green-400'
      case 'failed':
        return 'bg-red-500/20 text-red-400'
      case 'running':
        return 'bg-blue-500/20 text-blue-400'
      case 'pending':
        return 'bg-yellow-500/20 text-yellow-400'
      default:
        return 'bg-gray-500/20 text-gray-400'
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-xl font-bold mb-2">Ingestion Jobs</h2>
        <p className="text-sm text-gray-400">Trigger and monitor data ingestion jobs</p>
        <div className="mt-3 glass-panel border border-blue-500/30 rounded-lg p-4">
          <div className="flex items-start gap-3">
            <div className="text-blue-400 text-xl">ℹ️</div>
            <div>
              <h4 className="font-medium text-gray-300 mb-1">How Ingestion Jobs Work</h4>
              <p className="text-sm text-gray-400 mb-2">
                Ingestion jobs are <strong>automatic</strong> - they process immediately without approval:
              </p>
              <ul className="text-sm text-gray-400 space-y-1 list-disc list-inside ml-2 mb-2">
                <li>Job is queued (status: <span className="text-yellow-400">PENDING</span>)</li>
                <li>Celery worker picks it up automatically</li>
                <li>Status changes to <span className="text-blue-400">RUNNING</span> during processing</li>
                <li>Completes as <span className="text-green-400">SUCCESS</span> or <span className="text-red-400">FAILED</span></li>
              </ul>
              <p className="text-sm text-gray-400">
                Check the <strong>Workflows</strong> page to monitor all jobs. If jobs stay pending, ensure Celery workers are running.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Trigger Buttons */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <button
          onClick={() => {
            setShowMobileMoneyForm(true)
            setShowAccountingForm(false)
          }}
          className="glass-panel border border-glass-border rounded-lg p-6 hover:border-blue-500/50 transition-colors text-left"
        >
          <h3 className="text-lg font-bold mb-2">Mobile Money Ingestion</h3>
          <p className="text-sm text-gray-400">Ingest M-Pesa or Airtel transaction data from CSV</p>
        </button>

        <button
          onClick={() => {
            setShowAccountingForm(true)
            setShowMobileMoneyForm(false)
          }}
          className="glass-panel border border-glass-border rounded-lg p-6 hover:border-blue-500/50 transition-colors text-left"
        >
          <h3 className="text-lg font-bold mb-2">Accounting Ingestion</h3>
          <p className="text-sm text-gray-400">Ingest data from Xero, QuickBooks, or Odoo</p>
        </button>
      </div>

      {/* Mobile Money Form */}
      {showMobileMoneyForm && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="glass-panel border border-blue-500/30 rounded-lg p-6"
        >
          <h3 className="text-lg font-bold mb-4">Mobile Money Ingestion</h3>
          <form onSubmit={triggerMobileMoney} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-2">
                CSV File
              </label>
              <div className="space-y-2">
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".csv"
                  onChange={handleFileSelect}
                  className="hidden"
                  id="csv-file-input"
                />
                <label
                  htmlFor="csv-file-input"
                  className="flex items-center justify-center w-full px-4 py-3 bg-deep-space-50 border border-glass-border rounded-lg cursor-pointer hover:bg-deep-space-100 transition-colors"
                >
                  <svg
                    className="w-5 h-5 mr-2 text-gray-400"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
                    />
                  </svg>
                  <span className="text-gray-300">
                    {selectedFile ? selectedFile.name : 'Choose CSV file...'}
                  </span>
                </label>
                {selectedFile && (
                  <p className="text-xs text-gray-500">
                    Selected: {selectedFile.name} ({(selectedFile.size / 1024).toFixed(2)} KB)
                  </p>
                )}
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-2">Provider</label>
              <select
                value={mobileMoneyForm.provider}
                onChange={(e) => setMobileMoneyForm({ ...mobileMoneyForm, provider: e.target.value })}
                className="w-full px-4 py-2 bg-deep-space-50 border border-glass-border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-300"
              >
                <option value="mpesa">M-Pesa</option>
                <option value="airtel">Airtel</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-2">Currency</label>
              <input
                type="text"
                value={mobileMoneyForm.currency}
                onChange={(e) => setMobileMoneyForm({ ...mobileMoneyForm, currency: e.target.value })}
                className="w-full px-4 py-2 bg-deep-space-50 border border-glass-border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-300"
                placeholder="KES"
                required
              />
            </div>
            <div className="flex gap-3">
              <button
                type="submit"
                disabled={loading || !selectedFile}
                className="px-6 py-2 bg-blue-500/20 text-blue-400 rounded-lg hover:bg-blue-500/30 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {uploading ? 'Uploading...' : loading ? 'Starting...' : 'Start Ingestion'}
              </button>
              <button
                type="button"
                onClick={() => {
                  setShowMobileMoneyForm(false)
                  setSelectedFile(null)
                  setMobileMoneyForm({ path: '', provider: 'mpesa', currency: 'KES' })
                  if (fileInputRef.current) {
                    fileInputRef.current.value = ''
                  }
                }}
                className="px-6 py-2 bg-gray-500/20 text-gray-400 rounded-lg hover:bg-gray-500/30 transition-colors"
              >
                Cancel
              </button>
            </div>
          </form>
        </motion.div>
      )}

      {/* Accounting Form */}
      {showAccountingForm && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="glass-panel border border-blue-500/30 rounded-lg p-6"
        >
          <h3 className="text-lg font-bold mb-4">Accounting Ingestion</h3>
          <form onSubmit={triggerAccounting} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-2">Connector</label>
              <select
                value={accountingForm.connector}
                onChange={(e) => setAccountingForm({ ...accountingForm, connector: e.target.value })}
                className="w-full px-4 py-2 bg-deep-space-50 border border-glass-border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-300"
              >
                <option value="xero">Xero</option>
                <option value="quickbooks">QuickBooks</option>
                <option value="odoo">Odoo</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-2">
                Modified After (Optional)
              </label>
              <input
                type="datetime-local"
                value={accountingForm.modified_after}
                onChange={(e) => setAccountingForm({ ...accountingForm, modified_after: e.target.value })}
                className="w-full px-4 py-2 bg-deep-space-50 border border-glass-border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-300"
              />
              <p className="text-xs text-gray-500 mt-1">
                Only sync records modified after this date (ISO format)
              </p>
            </div>
            <div className="flex gap-3">
              <button
                type="submit"
                disabled={loading}
                className="px-6 py-2 bg-blue-500/20 text-blue-400 rounded-lg hover:bg-blue-500/30 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? 'Starting...' : 'Start Ingestion'}
              </button>
              <button
                type="button"
                onClick={() => setShowAccountingForm(false)}
                className="px-6 py-2 bg-gray-500/20 text-gray-400 rounded-lg hover:bg-gray-500/30 transition-colors"
              >
                Cancel
              </button>
            </div>
          </form>
        </motion.div>
      )}

      {/* Jobs List */}
      {jobs.length > 0 && (
        <div className="space-y-4">
          <h3 className="text-lg font-bold">Recent Jobs</h3>
          {jobs.map((job) => (
            <motion.div
              key={job.job_id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="glass-panel rounded-lg p-6 border border-glass-border"
            >
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-3">
                  <h4 className="font-bold font-mono">{job.job_id}</h4>
                  <span className={`px-2 py-1 rounded text-xs font-medium ${getJobStatusColor(job.status)}`}>
                    {job.status.toUpperCase()}
                  </span>
                </div>
                <span className="text-sm text-gray-400">
                  {new Date(job.created_at).toLocaleString()}
                </span>
              </div>
              <div className="text-sm text-gray-400 space-y-1">
                <p>
                  <strong>Type:</strong> {job.job_type}
                </p>
                {job.started_at && (
                  <p>
                    <strong>Started:</strong> {new Date(job.started_at).toLocaleString()}
                  </p>
                )}
                {job.completed_at && (
                  <p>
                    <strong>Completed:</strong> {new Date(job.completed_at).toLocaleString()}
                  </p>
                )}
                {job.error_message && (
                  <p className="text-red-400">
                    <strong>Error:</strong> {job.error_message}
                  </p>
                )}
                {job.stats && Object.keys(job.stats).length > 0 && (
                  <div className="mt-2">
                    <strong>Stats:</strong>
                    <pre className="text-xs mt-1 bg-deep-space-50 p-2 rounded">
                      {JSON.stringify(job.stats, null, 2)}
                    </pre>
                  </div>
                )}
              </div>
            </motion.div>
          ))}
        </div>
      )}
    </div>
  )
}
