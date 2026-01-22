import { createContext, useContext, useState, useCallback, ReactNode } from 'react'
import { Toast } from '../components/notifications/Toast'
import ToastContainer from '../components/notifications/Toast'

interface NotificationContextType {
  showToast: (message: string, type?: 'success' | 'error' | 'warning' | 'info', duration?: number) => void
  showError: (message: string) => void
  showSuccess: (message: string) => void
  showWarning: (message: string) => void
  showInfo: (message: string) => void
}

const NotificationContext = createContext<NotificationContextType | undefined>(undefined)

export function NotificationProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([])

  const showToast = useCallback((message: string, type: Toast['type'] = 'info', duration = 5000) => {
    const id = Math.random().toString(36).substring(7)
    setToasts((prev) => [...prev, { id, message, type, duration }])
  }, [])

  const removeToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((toast) => toast.id !== id))
  }, [])

  const showError = useCallback((message: string) => {
    showToast(message, 'error', 7000)
  }, [showToast])

  const showSuccess = useCallback((message: string) => {
    showToast(message, 'success', 3000)
  }, [showToast])

  const showWarning = useCallback((message: string) => {
    showToast(message, 'warning', 5000)
  }, [showToast])

  const showInfo = useCallback((message: string) => {
    showToast(message, 'info', 4000)
  }, [showToast])

  return (
    <NotificationContext.Provider value={{ showToast, showError, showSuccess, showWarning, showInfo }}>
      {children}
      <ToastContainer toasts={toasts} onClose={removeToast} />
    </NotificationContext.Provider>
  )
}

export function useNotifications() {
  const context = useContext(NotificationContext)
  if (!context) {
    throw new Error('useNotifications must be used within NotificationProvider')
  }
  return context
}
