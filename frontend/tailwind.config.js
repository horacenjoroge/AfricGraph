/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'deep-space': {
          DEFAULT: '#0A0F1E',
          50: '#1A2B4A',
          100: '#152238',
          200: '#0F1A2E',
        },
        'glass': {
          DEFAULT: 'rgba(255, 255, 255, 0.05)',
          border: 'rgba(255, 255, 255, 0.1)',
        },
        'glow': {
          blue: '#3B82F6',
          purple: '#8B5CF6',
          red: '#EF4444',
          green: '#10B981',
        },
      },
      fontFamily: {
        mono: ['Roboto Mono', 'monospace'],
        sans: ['Inter', 'sans-serif'],
      },
      backdropBlur: {
        xs: '2px',
      },
      boxShadow: {
        'glow-blue': '0 0 20px rgba(59, 130, 246, 0.5)',
        'glow-purple': '0 0 20px rgba(139, 92, 246, 0.5)',
        'glow-red': '0 0 20px rgba(239, 68, 68, 0.5)',
        'glow-green': '0 0 20px rgba(16, 185, 129, 0.5)',
      },
    },
  },
  plugins: [],
}
