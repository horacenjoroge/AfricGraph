import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'

export default function HowItWorks() {
  const [isOpen, setIsOpen] = useState(false)

  const steps = [
    {
      title: 'Graph Exploration',
      description: 'Navigate the 3D knowledge graph to discover relationships between businesses, people, and transactions. Click nodes to see details.',
      icon: '🔍',
    },
    {
      title: 'Risk Analysis',
      description: 'View comprehensive risk scores calculated from payment behavior, supplier concentration, and network exposure.',
      icon: '⚠️',
    },
    {
      title: 'Fraud Detection',
      description: 'Real-time alerts for suspicious patterns including circular payments, duplicate invoices, and unusual transactions.',
      icon: '🚨',
    },
    {
      title: 'Workflow Management',
      description: 'Approve or reject workflows for supplier onboarding, large payments, and credit limit increases.',
      icon: '📋',
    },
    {
      title: 'Audit Trail',
      description: 'Complete audit log of all actions, permission decisions, and data changes for compliance.',
      icon: '📝',
    },
  ]

  return (
    <div className="glass-panel border border-glass-border p-4 mb-6">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between text-left"
      >
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-full bg-glow-cyan/20 flex items-center justify-center border border-glow-cyan/40">
            <svg className="w-4 h-4 text-glow-cyan" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="10" />
              <line x1="12" y1="16" x2="12" y2="12" />
              <line x1="12" y1="8" x2="12.01" y2="8" />
            </svg>
          </div>
          <div>
            <h3 className="font-mono font-bold text-sm text-glow-cyan uppercase tracking-wider">
              How It Works
            </h3>
            <p className="text-xs text-gray-500 font-mono">Quick guide to using AfricGraph</p>
          </div>
        </div>
        <motion.div
          animate={{ rotate: isOpen ? 180 : 0 }}
          transition={{ duration: 0.2 }}
        >
          <svg className="w-5 h-5 text-gray-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <polyline points="6 9 12 15 18 9" />
          </svg>
        </motion.div>
      </button>

      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.3 }}
            className="overflow-hidden"
          >
            <div className="pt-4 space-y-3 border-t border-glass-border mt-4">
              {steps.map((step, index) => (
                <motion.div
                  key={step.title}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.1 }}
                  className="flex gap-3 p-3 glass-panel border border-glass-border hover:border-glow-cyan/30 transition-colors"
                >
                  <div className="flex-shrink-0 w-8 h-8 rounded bg-glow-cyan/10 flex items-center justify-center text-lg">
                    {step.icon}
                  </div>
                  <div className="flex-1">
                    <h4 className="font-mono font-semibold text-sm mb-1 text-white">
                      {step.title}
                    </h4>
                    <p className="text-xs text-gray-400 font-sans leading-relaxed">
                      {step.description}
                    </p>
                  </div>
                </motion.div>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
