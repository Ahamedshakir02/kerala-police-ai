import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../components/AuthContext'
import toast from 'react-hot-toast'
import { Shield, Mail, Lock } from 'lucide-react'

export default function Login() {
  const [badgeId, setBadgeId] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()
  const { login } = useAuth()

  const handleLogin = async (e) => {
    e.preventDefault()
    if (!badgeId || !password) { toast.error('Enter credentials'); return }
    setLoading(true)
    try {
      const res = await login(badgeId, password)
      if (res.success) {
        toast.success('Authentication successful')
        // Navigation is handled automatically by App.jsx route:
        // officer ? <Navigate to="/" /> : <Login />
      } else {
        toast.error(res.error)
      }
    } finally { setLoading(false) }
  }

  return (
    <div className="min-h-screen bg-surface-50 flex items-center justify-center p-6">
      <div className="w-full max-w-5xl bg-white rounded-[32px] shadow-float flex h-[600px] p-3 animate-fade-in">
        
        {/* Left Form Section */}
        <div className="w-1/2 p-12 flex flex-col relative justify-center">
          <div className="absolute top-10 left-12 flex items-center gap-2">
            <Shield className="text-brand-800" size={24} />
            <span className="font-bold text-gray-800 tracking-tight text-lg">KP-AI</span>
          </div>

          <div className="max-w-sm w-full mx-auto">
            <h1 className="text-4xl font-bold text-gray-900 tracking-tight mb-2">Welcome Back!</h1>
            <p className="text-gray-500 text-sm mb-8">Enter your credentials to access the internal intelligence portal.</p>

            <form onSubmit={handleLogin} className="space-y-5">
              <div className="relative">
                <Mail className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
                <input
                  type="text"
                  value={badgeId}
                  onChange={e => setBadgeId(e.target.value)}
                  placeholder="Badge ID (e.g. KP001)"
                  className="w-full pl-11 pr-4 py-3.5 bg-white border border-gray-200 rounded-xl text-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-brand-800/20 focus:border-brand-800 transition-all text-gray-800"
                />
              </div>
              <div className="relative">
                <Lock className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
                <input
                  type="password"
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                  placeholder="Password"
                  className="w-full pl-11 pr-4 py-3.5 bg-white border border-gray-200 rounded-xl text-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-brand-800/20 focus:border-brand-800 transition-all text-gray-800"
                />
              </div>

              <div className="flex items-center justify-between mt-2 mb-6">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input type="checkbox" className="w-4 h-4 rounded border-gray-300 text-brand-800 focus:ring-brand-800 accent-brand-800" />
                  <span className="text-xs text-gray-500">Remember Me</span>
                </label>
                <button type="button" className="text-xs text-brand-800 hover:text-brand-900 font-medium">Forgot password?</button>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full bg-[#1a1c1a] text-white rounded-xl py-3.5 font-medium text-sm hover:bg-black transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
              >
                {loading ? <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></span> : 'Sign In'}
              </button>
            </form>

            <p className="text-center text-xs text-gray-500 mt-8">
              Don't have an account? <span onClick={() => navigate('/request-access')} className="text-brand-800 font-medium cursor-pointer">Request access</span>
            </p>
          </div>
        </div>

        {/* Right Illustration Section */}
        <div className="w-1/2 relative bg-brand-50 rounded-[24px] overflow-hidden flex items-center justify-center">
          <img 
            src="/login-illustration.png" 
            alt="Kerala Police AI Illustration" 
            className="w-full h-full object-cover mix-blend-multiply opacity-90 scale-105"
          />
        </div>
      </div>
    </div>
  )
}
