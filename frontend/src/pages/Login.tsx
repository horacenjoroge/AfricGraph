import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import axios from 'axios'
import { useNotifications } from '../contexts/NotificationContext'

export default function LoginPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [loading, setLoading] = useState(false)
  const [isRegister, setIsRegister] = useState(false)
  const navigate = useNavigate()
  const { showSuccess, showError } = useNotifications()

  // Sanitize input: remove potentially dangerous characters (but keep password characters)
  const sanitizeInput = (value: string): string => {
    // For passwords, only remove HTML tags and script-like patterns
    // Keep special characters that are valid in passwords
    return value
      .replace(/<[^>]*>/g, '') // Remove HTML tags
      .replace(/<script|javascript:|on\w+=/gi, '') // Remove script patterns
      .trim()
  }

  // Sanitize email: allow only valid email characters
  const sanitizeEmail = (value: string): string => {
    // Allow only alphanumeric, @, ., -, _, + characters (common in emails)
    return value.replace(/[^a-zA-Z0-9@._+-]/g, '').trim()
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    // Sanitize inputs
    const sanitizedEmail = sanitizeEmail(email)
    const sanitizedPassword = sanitizeInput(password)
    
    if (!sanitizedEmail || !sanitizedPassword) {
      showError('Please enter email and password')
      return
    }

    // Validate email format
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    if (!emailRegex.test(sanitizedEmail)) {
      showError('Please enter a valid email address')
      return
    }

    // Validate password length
    if (sanitizedPassword.length < 8) {
      showError('Password must be at least 8 characters long')
      return
    }
    
    // Bcrypt has a 72-byte limit, so we need to check byte length, not character length
    const passwordBytes = new TextEncoder().encode(sanitizedPassword).length
    if (passwordBytes > 72) {
      showError('Password is too long. Maximum length is 72 bytes (approximately 72 characters for ASCII, less for Unicode).')
      return
    }

    setLoading(true)
    try {
      if (isRegister) {
        // Register
        const response = await axios.post('/auth/register', {
          email: sanitizedEmail.toLowerCase(),
          password: sanitizedPassword,
        })
        showSuccess('Registration successful! Please login.')
        setIsRegister(false)
        setPassword('')
        setEmail(sanitizedEmail.toLowerCase())
      } else {
        // Login
        const response = await axios.post('/auth/login', {
          email: sanitizedEmail.toLowerCase(),
          password: sanitizedPassword,
        })
        
        // Store tokens
        localStorage.setItem('auth_token', response.data.access_token)
        localStorage.setItem('refresh_token', response.data.refresh_token)
        
        // Set axios default header
        axios.defaults.headers.common['Authorization'] = `Bearer ${response.data.access_token}`
        
        showSuccess('Login successful!')
        navigate('/')
      }
    } catch (error: any) {
      console.error('Auth error:', error)
      console.error('Error response:', error.response)
      console.error('Error data:', error.response?.data)
      console.error('Error status:', error.response?.status)
      
      // Extract detailed error message
      let errorMessage = isRegister ? 'Registration failed' : 'Login failed'
      
      if (error.response) {
        // Backend returned an error response
        const status = error.response.status
        const data = error.response.data
        
        if (status === 404) {
          errorMessage = isRegister 
            ? 'Registration endpoint not found. Please check if the backend server is running.'
            : 'Login endpoint not found. Please check if the backend server is running.'
        } else if (data?.error) {
          // Check for 'error' field first (some FastAPI errors use this)
          errorMessage = String(data.error)
        } else if (data?.detail) {
          errorMessage = String(data.detail)
        } else if (data?.message) {
          errorMessage = String(data.message)
        } else if (typeof data === 'string') {
          errorMessage = data
        } else if (status === 400) {
          errorMessage = 'Invalid request. Please check your input.'
        } else if (status === 401) {
          errorMessage = 'Invalid email or password.'
        } else if (status === 409) {
          errorMessage = 'Email already registered'
        } else if (status === 500) {
          errorMessage = 'Server error. Please try again later.'
        } else {
          errorMessage = `Request failed with status ${status}. Please try again.`
        }
      } else if (error.request) {
        // Request was made but no response received
        errorMessage = 'No response from server. Please check if the backend server is running on port 8000.'
      } else {
        // Error setting up the request
        errorMessage = error.message || 'An unexpected error occurred'
      }
      
      // Ensure we always have a message to display
      if (!errorMessage || errorMessage.trim() === '') {
        errorMessage = isRegister ? 'Registration failed. Please try again.' : 'Login failed. Please try again.'
      }
      
      console.error('Final error message:', errorMessage)
      showError(errorMessage)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-deep-space flex items-center justify-center p-4">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="glass-panel-strong rounded-lg p-8 w-full max-w-md border border-glass-border"
      >
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold font-mono mb-2 text-glow-cyan">AFRICGRAPH</h1>
          <p className="text-gray-400">{isRegister ? 'Create Account' : 'Sign In'}</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-2">Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(sanitizeEmail(e.target.value))}
              className="w-full px-4 py-2 bg-deep-space-50 border border-glass-border rounded-lg focus:outline-none focus:ring-2 focus:ring-glow-blue text-gray-300"
              placeholder="Email"
              required
              autoComplete="email"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-400 mb-2">Password</label>
            <div className="relative">
              <input
                type={showPassword ? 'text' : 'password'}
                value={password}
                onChange={(e) => setPassword(sanitizeInput(e.target.value))}
                className="w-full px-4 py-2 pr-10 bg-deep-space-50 border border-glass-border rounded-lg focus:outline-none focus:ring-2 focus:ring-glow-blue text-gray-300"
                placeholder="Password"
                required
                minLength={8}
                autoComplete={isRegister ? 'new-password' : 'current-password'}
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-300 transition-colors focus:outline-none"
                aria-label={showPassword ? 'Hide password' : 'Show password'}
              >
                {showPassword ? (
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.29 3.29m0 0L3 3m3.29 3.29L3 3m14.29 14.29L21 21m0 0l-3.29-3.29M21 21l-3.29-3.29" />
                  </svg>
                ) : (
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                  </svg>
                )}
              </button>
            </div>
            {isRegister && (
              <p className="text-xs text-gray-500 mt-1">Password must be at least 8 characters</p>
            )}
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full px-4 py-2 bg-blue-500/20 text-blue-400 rounded-lg hover:bg-blue-500/30 transition-colors disabled:opacity-50 disabled:cursor-not-allowed font-medium"
          >
            {loading ? 'Processing...' : isRegister ? 'Register' : 'Sign In'}
          </button>
        </form>

        <div className="mt-6 text-center">
          <button
            onClick={() => {
              setIsRegister(!isRegister)
              setPassword('')
            }}
            className="text-sm text-gray-400 hover:text-gray-300 transition-colors"
          >
            {isRegister ? 'Already have an account? Sign in' : "Don't have an account? Register"}
          </button>
        </div>

        <div className="mt-6 pt-6 border-t border-glass-border text-center">
          <p className="text-xs text-gray-500">
            For development: You can also use the API directly
          </p>
        </div>
      </motion.div>
    </div>
  )
}
