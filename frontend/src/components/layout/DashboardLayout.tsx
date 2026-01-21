import { ReactNode } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { motion } from 'framer-motion'

interface DashboardLayoutProps {
  children: ReactNode
}

const navItems = [
  { path: '/', label: 'Dashboard', icon: '📊' },
  { path: '/businesses', label: 'Businesses', icon: '🏢' },
  { path: '/graph', label: 'Graph Explorer', icon: '🕸️' },
  { path: '/risk', label: 'Risk Analysis', icon: '⚠️' },
  { path: '/fraud', label: 'Fraud Alerts', icon: '🚨' },
  { path: '/workflows', label: 'Workflows', icon: '📋' },
  { path: '/audit', label: 'Audit Logs', icon: '📝' },
  { path: '/settings', label: 'Settings', icon: '⚙️' },
]

export default function DashboardLayout({ children }: DashboardLayoutProps) {
  const location = useLocation()

  return (
    <div className="min-h-screen bg-deep-space flex">
      {/* Sidebar */}
      <aside className="w-64 glass-panel-strong border-r border-glass-border p-6">
        <div className="mb-8">
          <h1 className="text-2xl font-bold font-mono text-glow-blue">
            AfricGraph
          </h1>
          <p className="text-xs text-gray-400 mt-1">Intelligence Console</p>
        </div>

        <nav className="space-y-2">
          {navItems.map((item) => {
            const isActive = location.pathname === item.path
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`block px-4 py-3 rounded-lg transition-all ${
                  isActive
                    ? 'bg-glow-blue/20 text-blue-400 glow-blue'
                    : 'text-gray-300 hover:bg-glass hover:text-white'
                }`}
              >
                <span className="mr-3">{item.icon}</span>
                <span className="font-medium">{item.label}</span>
              </Link>
            )
          })}
        </nav>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-auto">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
          className="p-8"
        >
          {children}
        </motion.div>
      </main>
    </div>
  )
}
