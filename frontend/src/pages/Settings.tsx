import { useState } from 'react'
import { motion } from 'framer-motion'

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState<'users' | 'config'>('users')

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold font-mono mb-2">Settings</h1>
        <p className="text-gray-400">System configuration and user management</p>
      </div>

      {/* Tabs */}
      <div className="glass-panel rounded-lg p-6">
        <div className="flex gap-4 border-b border-glass-border mb-6">
          <button
            onClick={() => setActiveTab('users')}
            className={`pb-4 px-4 font-medium transition-colors ${
              activeTab === 'users'
                ? 'text-blue-400 border-b-2 border-blue-400'
                : 'text-gray-400 hover:text-white'
            }`}
          >
            User Management
          </button>
          <button
            onClick={() => setActiveTab('config')}
            className={`pb-4 px-4 font-medium transition-colors ${
              activeTab === 'config'
                ? 'text-blue-400 border-b-2 border-blue-400'
                : 'text-gray-400 hover:text-white'
            }`}
          >
            Configuration
          </button>
        </div>

        {activeTab === 'users' && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-4"
          >
            <h2 className="text-xl font-bold mb-4">Users</h2>
            <div className="text-gray-400">
              User management interface placeholder. This would include:
              <ul className="list-disc list-inside mt-2 space-y-1">
                <li>Create/Edit/Delete users</li>
                <li>Assign roles and permissions</li>
                <li>View user activity</li>
              </ul>
            </div>
          </motion.div>
        )}

        {activeTab === 'config' && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-4"
          >
            <h2 className="text-xl font-bold mb-4">System Configuration</h2>
            <div className="text-gray-400">
              Configuration interface placeholder. This would include:
              <ul className="list-disc list-inside mt-2 space-y-1">
                <li>API settings</li>
                <li>Notification preferences</li>
                <li>Risk scoring thresholds</li>
                <li>Alert rules configuration</li>
              </ul>
            </div>
          </motion.div>
        )}
      </div>
    </div>
  )
}
