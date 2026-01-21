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

export default function WorkflowsPage() {
  const [workflows, setWorkflows] = useState<Workflow[]>([])
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    fetchWorkflows()
  }, [])

  const fetchWorkflows = async () => {
    setLoading(true)
    try {
      const response = await axios.get('/api/v1/workflows')
      setWorkflows(response.data.workflows || [])
    } catch (error) {
      console.error('Failed to fetch workflows:', error)
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

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold font-mono mb-2">Workflows</h1>
        <p className="text-gray-400">Approval queue and workflow management</p>
      </div>

      <div className="glass-panel rounded-lg overflow-hidden">
        <div className="p-6 border-b border-glass-border">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-bold">Pending Approvals</h2>
            <button
              onClick={fetchWorkflows}
              className="px-4 py-2 bg-blue-500/20 text-blue-400 rounded-lg hover:bg-blue-500/30 transition-colors"
            >
              Refresh
            </button>
          </div>
        </div>

        {loading ? (
          <div className="p-8 text-center text-gray-400">Loading workflows...</div>
        ) : workflows.length === 0 ? (
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
    </div>
  )
}
