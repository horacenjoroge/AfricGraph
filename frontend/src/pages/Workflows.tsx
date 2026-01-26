import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import axios from 'axios'

interface Workflow {
  id: string
  workflow_type: string
  status: string
  current_step: string
  created_at: string
  business_id?: string
}

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

export default function WorkflowsPage() {
  const [workflows, setWorkflows] = useState<Workflow[]>([])
  const [ingestionJobs, setIngestionJobs] = useState<IngestionJob[]>([])
  const [loading, setLoading] = useState(false)
  const [activeTab, setActiveTab] = useState<'workflows' | 'ingestion'>('ingestion')

  useEffect(() => {
    fetchWorkflows()
    fetchIngestionJobs()
  }, [])

  const fetchWorkflows = async () => {
    try {
      const response = await axios.get('/api/v1/workflows')
      setWorkflows(response.data.workflows || [])
    } catch (error: any) {
      // Workflows endpoint might not exist yet, that's okay
      if (error.response?.status !== 404) {
        console.error('Failed to fetch workflows:', error)
      }
      setWorkflows([])
    }
  }

  const fetchIngestionJobs = async () => {
    setLoading(true)
    try {
      const token = localStorage.getItem('auth_token')
      const response = await axios.get('/api/v1/ingest/jobs', {
        params: { limit: 50 },
        headers: {
          Authorization: `Bearer ${token}`,
        },
      })
      setIngestionJobs(response.data.jobs || [])
    } catch (error) {
      console.error('Failed to fetch ingestion jobs:', error)
      setIngestionJobs([])
    } finally {
      setLoading(false)
    }
  }

  const approveWorkflow = async (workflowId: string) => {
    try {
      await axios.post(`/api/v1/workflows/${workflowId}/approve`)
      fetchWorkflows()
    } catch (error) {
      console.error('Failed to approve workflow:', error)
    }
  }

  const getJobStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'success':
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
      <div>
        <h1 className="text-3xl font-bold font-mono mb-2">Workflows & Jobs</h1>
        <p className="text-gray-400">Monitor workflows and ingestion jobs</p>
      </div>

      {/* Tabs */}
      <div className="glass-panel rounded-lg p-6">
        <div className="flex gap-4 border-b border-glass-border mb-6">
          <button
            onClick={() => setActiveTab('ingestion')}
            className={`pb-4 px-4 font-medium transition-colors ${
              activeTab === 'ingestion'
                ? 'text-blue-400 border-b-2 border-blue-400'
                : 'text-gray-400 hover:text-white'
            }`}
          >
            Ingestion Jobs
          </button>
          <button
            onClick={() => setActiveTab('workflows')}
            className={`pb-4 px-4 font-medium transition-colors ${
              activeTab === 'workflows'
                ? 'text-blue-400 border-b-2 border-blue-400'
                : 'text-gray-400 hover:text-white'
            }`}
          >
            Workflows
          </button>
        </div>

        {activeTab === 'ingestion' && (
          <div>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold">Ingestion Jobs</h2>
              <button
                onClick={fetchIngestionJobs}
                className="px-4 py-2 bg-blue-500/20 text-blue-400 rounded-lg hover:bg-blue-500/30 transition-colors"
              >
                Refresh
              </button>
            </div>

            {/* Info Box */}
            <div className="mb-6 glass-panel border border-blue-500/30 rounded-lg p-4">
              <div className="flex items-start gap-3">
                <div className="text-blue-400 text-xl">ℹ️</div>
                <div>
                  <h4 className="font-medium text-gray-300 mb-1">How Ingestion Jobs Work</h4>
                  <p className="text-sm text-gray-400 mb-2">
                    Ingestion jobs are <strong>automatic</strong> - they don't require approval. When you start a job:
                  </p>
                  <ol className="text-sm text-gray-400 space-y-1 list-decimal list-inside ml-2">
                    <li>Job is created with status <span className="text-yellow-400">PENDING</span> (queued in RabbitMQ)</li>
                    <li>Celery worker picks up the job automatically</li>
                    <li>Status changes to <span className="text-blue-400">RUNNING</span> while processing</li>
                    <li>Status becomes <span className="text-green-400">SUCCESS</span> or <span className="text-red-400">FAILED</span> when complete</li>
                  </ol>
                </div>
              </div>
            </div>

            {loading ? (
              <div className="p-8 text-center text-gray-400">Loading ingestion jobs...</div>
            ) : ingestionJobs.length === 0 ? (
              <div className="p-8 text-center text-gray-400">No ingestion jobs found</div>
            ) : (
              <div className="space-y-4">
                {ingestionJobs.map((job, index) => (
                  <motion.div
                    key={job.job_id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.05 }}
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
        )}

        {activeTab === 'workflows' && (
          <div>
            <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-bold">Pending Approvals</h2>
            <button
              onClick={fetchWorkflows}
              className="px-4 py-2 bg-blue-500/20 text-blue-400 rounded-lg hover:bg-blue-500/30 transition-colors"
            >
              Refresh
            </button>
        </div>

            {workflows.length === 0 ? (
          <div className="p-8 text-center text-gray-400">No pending workflows</div>
        ) : (
          <div className="divide-y divide-glass-border">
            {workflows.map((workflow, index) => (
              <motion.div
                key={workflow.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
                className="p-6 hover:bg-glass transition-colors"
              >
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="font-bold text-lg mb-1">{workflow.workflow_type}</h3>
                    <div className="text-sm text-gray-400 space-y-1">
                      <div>Status: <span className="text-white">{workflow.status}</span></div>
                      <div>Current Step: <span className="text-white">{workflow.current_step}</span></div>
                      {workflow.business_id && (
                        <div>Business: <span className="font-mono">{workflow.business_id}</span></div>
                      )}
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={() => approveWorkflow(workflow.id)}
                      className="px-4 py-2 bg-green-500/20 text-green-400 rounded-lg hover:bg-green-500/30 transition-colors"
                    >
                      Approve
                    </button>
                    <button className="px-4 py-2 bg-red-500/20 text-red-400 rounded-lg hover:bg-red-500/30 transition-colors">
                      Reject
                    </button>
                  </div>
                </div>
              </motion.div>
            ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
