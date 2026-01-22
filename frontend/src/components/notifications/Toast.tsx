import { useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'

export interface Toast {
  id: string
  message: string
  type: 'success' | 'error' | 'warning' | 'info'
  duration?: number
}

interface ToastProps {
  toast: Toast
  onClose: (id: string) => void
}

function ToastComponent({ toast, onClose }: ToastProps) {
  useEffect(() => {
    if (toast.duration !== 0) {
      const timer = setTimeout(() => {
        onClose(toast.id)
      }, toast.duration || 5000)
      return () => clearTimeout(timer)
    }
  }, [toast.id, toast.duration, onClose])

  const getToastStyles = () => {
    switch (toast.type) {
      case 'error':
        return 'bg-red-500/20 border-red-500/50 text-red-400'
      case 'success':
        return 'bg-green-500/20 border-green-500/50 text-green-400'
      case 'warning':
        return 'bg-yellow-500/20 border-yellow-500/50 text-yellow-400'
      case 'info':
        return 'bg-blue-500/20 border-blue-500/50 text-blue-400'
      default:
        return 'bg-gray-500/20 border-gray-500/50 text-gray-400'
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: -20, scale: 0.95 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, y: -10, scale: 0.95 }}
      className={`glass-panel-strong border rounded-lg p-4 mb-3 flex items-center justify-between min-w-[300px] max-w-[500px] ${getToastStyles()}`}
    >
      <div className="flex-1 pr-4">
        <p className="text-sm font-medium font-sans">{toast.message}</p>
      </div>
      <button
        onClick={() => onClose(toast.id)}
        className="flex-shrink-0 text-gray-400 hover:text-white transition-colors"
        aria-label="Close"
      >
        <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <line x1="18" y1="6" x2="6" y2="18" />
          <line x1="6" y1="6" x2="18" y2="18" />
        </svg>
      </button>
    </motion.div>
  )
}

interface ToastContainerProps {
  toasts: Toast[]
  onClose: (id: string) => void
}

export default function ToastContainer({ toasts, onClose }: ToastContainerProps) {
  return (
    <div className="fixed top-4 right-4 z-50 pointer-events-none">
      <div className="pointer-events-auto">
        <AnimatePresence>
          {toasts.map((toast) => (
            <ToastComponent key={toast.id} toast={toast} onClose={onClose} />
          ))}
        </AnimatePresence>
      </div>
    </div>
  )
}
