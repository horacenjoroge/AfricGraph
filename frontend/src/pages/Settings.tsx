import { useState } from 'react'
import { motion } from 'framer-motion'
import UserProfile from '../components/settings/UserProfile'
import Preferences from '../components/settings/Preferences'
import TenantInfo from '../components/settings/TenantInfo'
import TenantPerformanceDashboard from '../components/tenancy/TenantPerformanceDashboard'

type TabType = 'profile' | 'preferences' | 'tenant' | 'analytics'

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState<TabType>('profile')

  const tabs: { id: TabType; label: string }[] = [
    { id: 'profile', label: 'Profile' },
    { id: 'preferences', label: 'Preferences' },
    { id: 'tenant', label: 'Tenant' },
    { id: 'analytics', label: 'Performance' },
  ]

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold font-mono mb-2">Settings</h1>
        <p className="text-gray-400">Manage your profile, preferences, and tenant settings</p>
      </div>

      {/* Tabs */}
      <div className="glass-panel rounded-lg p-6">
        <div className="flex gap-4 border-b border-glass-border mb-6">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`pb-4 px-4 font-medium transition-colors ${
                activeTab === tab.id
                  ? 'text-blue-400 border-b-2 border-blue-400'
                  : 'text-gray-400 hover:text-white'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        <motion.div
          key={activeTab}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.2 }}
        >
          {activeTab === 'profile' && <UserProfile />}
          {activeTab === 'preferences' && <Preferences />}
          {activeTab === 'tenant' && <TenantInfo />}
          {activeTab === 'analytics' && <TenantPerformanceDashboard />}
        </motion.div>
      </div>
    </div>
  )
}
