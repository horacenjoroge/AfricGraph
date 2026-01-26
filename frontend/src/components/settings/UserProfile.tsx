import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import axios from 'axios'
import { useNotifications } from '../../contexts/NotificationContext'

interface User {
  id: string
  email: string
  role: string
  is_active: boolean
  created_at: string
}

export default function UserProfile() {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)
  const [changingPassword, setChangingPassword] = useState(false)
  const [passwordForm, setPasswordForm] = useState({
    oldPassword: '',
    newPassword: '',
    confirmPassword: '',
  })
  const { showSuccess, showError } = useNotifications()
  const navigate = useNavigate()

  useEffect(() => {
    fetchUserProfile()
  }, [])

  const handleLogout = () => {
    // Clear authentication tokens
    localStorage.removeItem('auth_token')
    localStorage.removeItem('refresh_token')
    
    // Clear axios default headers
    delete axios.defaults.headers.common['Authorization']
    
    // Clear tenant context
    localStorage.removeItem('current_tenant_id')
    delete axios.defaults.headers.common['X-Tenant-ID']
    
    showSuccess('Logged out successfully')
    
    // Navigate to login page
    navigate('/login')
  }

  const fetchUserProfile = async () => {
    try {
      setLoading(true)
      // Get token from localStorage (check both possible keys)
      const authHeader = axios.defaults.headers.common['Authorization']
      const token = localStorage.getItem('auth_token') || localStorage.getItem('access_token') || (typeof authHeader === 'string' ? authHeader.replace('Bearer ', '') : '')
      if (!token) {
        // Not logged in - don't show error, just set user to null
        setUser(null)
        setLoading(false)
        return
      }

      const response = await axios.get('/auth/me', {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      })
      setUser(response.data)
    } catch (error: any) {
      console.error('Failed to fetch user profile:', error)
      if (error.response?.status === 401) {
        // Not authenticated - set user to null instead of showing error
        setUser(null)
      } else {
        showError('Failed to load user profile')
      }
    } finally {
      setLoading(false)
    }
  }

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (passwordForm.newPassword !== passwordForm.confirmPassword) {
      showError('New passwords do not match')
      return
    }

    if (passwordForm.newPassword.length < 8) {
      showError('Password must be at least 8 characters')
      return
    }

    try {
      setChangingPassword(true)
      const authHeader = axios.defaults.headers.common['Authorization']
      const token = localStorage.getItem('auth_token') || localStorage.getItem('access_token') || (typeof authHeader === 'string' ? authHeader.replace('Bearer ', '') : '')
      
      await axios.post(
        '/auth/change-password',
        {
          old_password: passwordForm.oldPassword,
          new_password: passwordForm.newPassword,
        },
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      )

      showSuccess('Password changed successfully')
      setPasswordForm({
        oldPassword: '',
        newPassword: '',
        confirmPassword: '',
      })
    } catch (error: any) {
      console.error('Failed to change password:', error)
      showError(error.response?.data?.detail || 'Failed to change password')
    } finally {
      setChangingPassword(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-gray-400">Loading profile...</div>
      </div>
    )
  }

  if (!user) {
    return (
      <div className="text-center py-12">
        <div className="glass-panel rounded-lg p-8 max-w-md mx-auto">
          <h3 className="text-xl font-bold mb-2">Not Authenticated</h3>
          <p className="text-gray-400 mb-6">
            You need to be logged in to view your profile. Authentication is required to access user settings.
          </p>
          <div className="text-sm text-gray-500 space-y-2">
            <p>To use this feature:</p>
            <ul className="list-disc list-inside text-left space-y-1">
              <li>Visit the login page to create an account or sign in</li>
              <li>Or use the API directly: <code className="bg-deep-space-50 px-2 py-1 rounded">POST /auth/login</code></li>
            </ul>
          </div>
          <div className="mt-6 flex gap-3 justify-center">
            <a
              href="/login"
              className="px-6 py-2 bg-blue-500/20 text-blue-400 rounded-lg hover:bg-blue-500/30 transition-colors"
            >
              Go to Login
            </a>
            <button
              onClick={fetchUserProfile}
              className="px-6 py-2 bg-gray-500/20 text-gray-400 rounded-lg hover:bg-gray-500/30 transition-colors"
            >
              Retry
            </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Profile Information */}
      <div className="glass-panel rounded-lg p-6">
        <h3 className="text-xl font-bold mb-4">Profile Information</h3>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-2">Email</label>
            <div className="px-4 py-2 bg-deep-space-50 border border-glass-border rounded-lg font-mono text-gray-300">
              {user.email}
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-400 mb-2">Role</label>
            <div className="px-4 py-2 bg-deep-space-50 border border-glass-border rounded-lg">
              <span className={`px-2 py-1 rounded text-xs font-medium ${
                user.role === 'admin' 
                  ? 'bg-purple-500/20 text-purple-400' 
                  : 'bg-blue-500/20 text-blue-400'
              }`}>
                {user.role.toUpperCase()}
              </span>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-400 mb-2">Account Status</label>
            <div className="px-4 py-2 bg-deep-space-50 border border-glass-border rounded-lg">
              <span className={`px-2 py-1 rounded text-xs font-medium ${
                user.is_active 
                  ? 'bg-green-500/20 text-green-400' 
                  : 'bg-red-500/20 text-red-400'
              }`}>
                {user.is_active ? 'ACTIVE' : 'INACTIVE'}
              </span>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-400 mb-2">Member Since</label>
            <div className="px-4 py-2 bg-deep-space-50 border border-glass-border rounded-lg text-gray-300">
              {new Date(user.created_at).toLocaleDateString('en-US', {
                year: 'numeric',
                month: 'long',
                day: 'numeric',
              })}
            </div>
          </div>
        </div>
      </div>

      {/* Change Password */}
      <div className="glass-panel rounded-lg p-6">
        <h3 className="text-xl font-bold mb-4">Change Password</h3>
        <form onSubmit={handleChangePassword} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-2">Current Password</label>
            <input
              type="password"
              value={passwordForm.oldPassword}
              onChange={(e) => setPasswordForm({ ...passwordForm, oldPassword: e.target.value })}
              className="w-full px-4 py-2 bg-deep-space-50 border border-glass-border rounded-lg focus:outline-none focus:ring-2 focus:ring-glow-blue text-gray-300"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-400 mb-2">New Password</label>
            <input
              type="password"
              value={passwordForm.newPassword}
              onChange={(e) => setPasswordForm({ ...passwordForm, newPassword: e.target.value })}
              className="w-full px-4 py-2 bg-deep-space-50 border border-glass-border rounded-lg focus:outline-none focus:ring-2 focus:ring-glow-blue text-gray-300"
              required
              minLength={8}
            />
            <p className="text-xs text-gray-500 mt-1">Must be at least 8 characters</p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-400 mb-2">Confirm New Password</label>
            <input
              type="password"
              value={passwordForm.confirmPassword}
              onChange={(e) => setPasswordForm({ ...passwordForm, confirmPassword: e.target.value })}
              className="w-full px-4 py-2 bg-deep-space-50 border border-glass-border rounded-lg focus:outline-none focus:ring-2 focus:ring-glow-blue text-gray-300"
              required
              minLength={8}
            />
          </div>

          <button
            type="submit"
            disabled={changingPassword}
            className="px-6 py-2 bg-blue-500/20 text-blue-400 rounded-lg hover:bg-blue-500/30 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {changingPassword ? 'Changing...' : 'Change Password'}
          </button>
        </form>
      </div>

      {/* Logout */}
      <div className="glass-panel rounded-lg p-6 border border-red-500/20">
        <h3 className="text-xl font-bold mb-4">Session</h3>
        <p className="text-sm text-gray-400 mb-4">
          Sign out of your account. You will need to log in again to access the system.
        </p>
        <button
          onClick={handleLogout}
          className="px-6 py-2 bg-red-500/20 text-red-400 rounded-lg hover:bg-red-500/30 transition-colors"
        >
          Logout
        </button>
      </div>
    </div>
  )
}
