import { ReactNode, useState, useEffect } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { motion } from 'framer-motion'
import axios from 'axios'
import {
  DashboardIcon,
  BusinessIcon,
  GraphIcon,
  RiskIcon,
  AlertIcon,
  WorkflowIcon,
  AuditIcon,
  SettingsIcon,
  AdminIcon,
  TransactionIcon,
} from '../icons/IconComponents'
import ThemeToggle from '../ThemeToggle'
import TenantSelector from '../tenancy/TenantSelector'

interface DashboardLayoutProps {
  children?: ReactNode
}

const baseNavItems = [
  { path: '/', label: 'Dashboard', Icon: DashboardIcon },
  { path: '/businesses', label: 'Businesses', Icon: BusinessIcon },
  { path: '/transactions', label: 'Transactions', Icon: TransactionIcon },
  { path: '/graph', label: 'Graph Explorer', Icon: GraphIcon },
  { path: '/risk', label: 'Risk Analysis', Icon: RiskIcon },
  { path: '/fraud', label: 'Fraud Alerts', Icon: AlertIcon },
  { path: '/workflows', label: 'Workflows', Icon: WorkflowIcon },
  { path: '/audit', label: 'Audit Logs', Icon: AuditIcon },
  { path: '/settings', label: 'Settings', Icon: SettingsIcon },
]

export default function DashboardLayout({ children }: DashboardLayoutProps) {
  const location = useLocation()
  const [isAdmin, setIsAdmin] = useState(false)
  const [checkingRole, setCheckingRole] = useState(true)

  useEffect(() => {
    checkAdminRole()
  }, [])

  const checkAdminRole = async () => {
    try {
      const token = localStorage.getItem('auth_token')
      if (!token) {
        setCheckingRole(false)
        return
      }

      const response = await axios.get('/auth/me', {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      })

      setIsAdmin(response.data.role === 'admin')
    } catch (error) {
      console.error('Failed to check admin role:', error)
    } finally {
      setCheckingRole(false)
    }
  }

  const navItems = checkingRole
    ? baseNavItems
    : isAdmin
    ? [...baseNavItems, { path: '/admin', label: 'Admin', Icon: AdminIcon }]
    : baseNavItems

  return (
    <div className="min-h-screen bg-deep-space flex">
      {/* Sidebar */}
      <aside className="w-64 glass-panel-strong border-r border-glass-border p-6">
        <div className="mb-8 pb-6 border-b border-glass-border">
          <div className="mb-8 pb-6 border-b border-glass-border">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-2xl font-bold font-mono text-glow-cyan tracking-wider">
                  AFRICGRAPH
                </h1>
                <p className="text-xs mt-1 font-mono" style={{ color: 'var(--text-secondary)' }}>INTELLIGENCE CONSOLE v1.0</p>
              </div>
              <ThemeToggle />
            </div>
          </div>
        </div>

        <nav className="space-y-1">
          {navItems.map((item, index) => {
            const isActive = location.pathname === item.path
            const Icon = item.Icon
            return (
              <motion.div
                key={item.path}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.05 }}
              >
                <Link
                  to={item.path}
                  className={`flex items-center gap-3 px-4 py-3 transition-all ${
                    isActive
                      ? 'text-glow-cyan border-l-2 border-glow-cyan bg-glow-cyan/10'
                      : 'hover:bg-glass/50 border-l-2 border-transparent'
                  }`}
                  style={{
                    color: isActive ? undefined : 'var(--text-secondary)',
                  }}
                  onMouseEnter={(e) => {
                    if (!isActive) {
                      e.currentTarget.style.color = 'var(--text-primary)'
                    }
                  }}
                  onMouseLeave={(e) => {
                    if (!isActive) {
                      e.currentTarget.style.color = 'var(--text-secondary)'
                    }
                  }}
                >
                  <Icon className={`w-4 h-4 ${isActive ? 'text-glow-cyan' : ''}`} />
                  <span className="font-medium text-sm">{item.label}</span>
                </Link>
              </motion.div>
            )
          })}
        </nav>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-auto relative z-10">
        {/* Top Bar with Tenant Selector */}
        <div className="sticky top-0 z-20 glass-panel border-b border-glass-border px-8 py-4 flex items-center justify-between">
          <div></div>
          <TenantSelector />
        </div>
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, ease: "easeOut" }}
          className="p-8"
        >
          {children}
        </motion.div>
      </main>
    </div>
  )
}
