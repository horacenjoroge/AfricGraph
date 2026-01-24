import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'

interface Preferences {
  theme: 'dark' | 'light'
  notifications: {
    email: boolean
    inApp: boolean
    alerts: boolean
  }
  graphExplorer: {
    defaultMaxHops: number
    defaultNodeTypes: string[]
    defaultShowLabels: boolean
  }
}

export default function Preferences() {
  const [preferences, setPreferences] = useState<Preferences>({
    theme: 'dark',
    notifications: {
      email: true,
      inApp: true,
      alerts: true,
    },
    graphExplorer: {
      defaultMaxHops: 2,
      defaultNodeTypes: [],
      defaultShowLabels: true,
    },
  })

  useEffect(() => {
    loadPreferences()
  }, [])

  const loadPreferences = () => {
    const saved = localStorage.getItem('user_preferences')
    if (saved) {
      try {
        const parsed = JSON.parse(saved)
        setPreferences((prev) => ({ ...prev, ...parsed }))
      } catch (e) {
        console.error('Failed to parse preferences:', e)
      }
    }

    // Load theme from ThemeToggle
    const theme = localStorage.getItem('theme') || 'dark'
    setPreferences((prev) => ({ ...prev, theme: theme as 'dark' | 'light' }))
  }

  const savePreferences = (newPrefs: Partial<Preferences>) => {
    const updated = { ...preferences, ...newPrefs }
    setPreferences(updated)
    localStorage.setItem('user_preferences', JSON.stringify(updated))
  }

  const handleThemeChange = (theme: 'dark' | 'light') => {
    savePreferences({ theme })
    localStorage.setItem('theme', theme)
    document.documentElement.classList.toggle('light-mode', theme === 'light')
    document.documentElement.classList.toggle('dark-mode', theme === 'dark')
  }

  return (
    <div className="space-y-6">
      {/* Theme Preferences */}
      <div className="glass-panel rounded-lg p-6">
        <h3 className="text-xl font-bold mb-4">Theme</h3>
        <div className="space-y-3">
          <label className="flex items-center gap-3 cursor-pointer">
            <input
              type="radio"
              name="theme"
              value="dark"
              checked={preferences.theme === 'dark'}
              onChange={() => handleThemeChange('dark')}
              className="w-4 h-4 text-blue-600"
            />
            <div>
              <div className="font-medium text-gray-300">Dark Mode</div>
              <div className="text-xs text-gray-500">Default dark theme</div>
            </div>
          </label>

          <label className="flex items-center gap-3 cursor-pointer">
            <input
              type="radio"
              name="theme"
              value="light"
              checked={preferences.theme === 'light'}
              onChange={() => handleThemeChange('light')}
              className="w-4 h-4 text-blue-600"
            />
            <div>
              <div className="font-medium text-gray-300">Light Mode</div>
              <div className="text-xs text-gray-500">Light theme</div>
            </div>
          </label>
        </div>
      </div>

      {/* Notification Preferences */}
      <div className="glass-panel rounded-lg p-6">
        <h3 className="text-xl font-bold mb-4">Notifications</h3>
        <div className="space-y-4">
          <label className="flex items-center justify-between cursor-pointer">
            <div>
              <div className="font-medium text-gray-300">Email Notifications</div>
              <div className="text-xs text-gray-500">Receive notifications via email</div>
            </div>
            <input
              type="checkbox"
              checked={preferences.notifications.email}
              onChange={(e) =>
                savePreferences({
                  notifications: { ...preferences.notifications, email: e.target.checked },
                })
              }
              className="w-5 h-5 text-blue-600 rounded"
            />
          </label>

          <label className="flex items-center justify-between cursor-pointer">
            <div>
              <div className="font-medium text-gray-300">In-App Notifications</div>
              <div className="text-xs text-gray-500">Show notifications in the application</div>
            </div>
            <input
              type="checkbox"
              checked={preferences.notifications.inApp}
              onChange={(e) =>
                savePreferences({
                  notifications: { ...preferences.notifications, inApp: e.target.checked },
                })
              }
              className="w-5 h-5 text-blue-600 rounded"
            />
          </label>

          <label className="flex items-center justify-between cursor-pointer">
            <div>
              <div className="font-medium text-gray-300">Alert Notifications</div>
              <div className="text-xs text-gray-500">Receive alerts for fraud and risk events</div>
            </div>
            <input
              type="checkbox"
              checked={preferences.notifications.alerts}
              onChange={(e) =>
                savePreferences({
                  notifications: { ...preferences.notifications, alerts: e.target.checked },
                })
              }
              className="w-5 h-5 text-blue-600 rounded"
            />
          </label>
        </div>
      </div>

      {/* Graph Explorer Preferences */}
      <div className="glass-panel rounded-lg p-6">
        <h3 className="text-xl font-bold mb-4">Graph Explorer</h3>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-2">
              Default Max Hops: {preferences.graphExplorer.defaultMaxHops}
            </label>
            <input
              type="range"
              min="1"
              max="5"
              value={preferences.graphExplorer.defaultMaxHops}
              onChange={(e) =>
                savePreferences({
                  graphExplorer: {
                    ...preferences.graphExplorer,
                    defaultMaxHops: parseInt(e.target.value),
                  },
                })
              }
              className="w-full"
            />
            <div className="text-xs text-gray-500 mt-1">
              Number of relationship hops to explore by default
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-400 mb-2">Default Node Types</label>
            <div className="space-y-2">
              {['Business', 'Person', 'Transaction', 'Invoice'].map((type) => (
                <label key={type} className="flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={preferences.graphExplorer.defaultNodeTypes.includes(type)}
                    onChange={(e) => {
                      const newTypes = e.target.checked
                        ? [...preferences.graphExplorer.defaultNodeTypes, type]
                        : preferences.graphExplorer.defaultNodeTypes.filter((t) => t !== type)
                      savePreferences({
                        graphExplorer: { ...preferences.graphExplorer, defaultNodeTypes: newTypes },
                      })
                    }}
                    className="mr-2"
                  />
                  <span className="text-sm text-gray-300">{type}</span>
                </label>
              ))}
            </div>
          </div>

          <label className="flex items-center justify-between cursor-pointer">
            <div>
              <div className="font-medium text-gray-300">Show Relationship Labels</div>
              <div className="text-xs text-gray-500">Display relationship type labels on graph</div>
            </div>
            <input
              type="checkbox"
              checked={preferences.graphExplorer.defaultShowLabels}
              onChange={(e) =>
                savePreferences({
                  graphExplorer: {
                    ...preferences.graphExplorer,
                    defaultShowLabels: e.target.checked,
                  },
                })
              }
              className="w-5 h-5 text-blue-600 rounded"
            />
          </label>
        </div>
      </div>
    </div>
  )
}
