import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'
import { Shield, Mail, Phone, User, Building } from 'lucide-react'

export default function RequestAccess() {
  const [formData, setFormData] = useState({ name: '', badge_id: '', phone: '', station: '' })
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!formData.name || !formData.badge_id || !formData.phone || !formData.station) { 
      toast.error('Please fill all fields'); 
      return 
    }
    setLoading(true)
    // Simulate API request since there is no backend route for this yet
    setTimeout(() => {
      setLoading(false)
      toast.success('Access request submitted to admin!')
      navigate('/login')
    }, 1500)
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
            <h1 className="text-3xl font-bold text-gray-900 tracking-tight mb-2">Request Access</h1>
            <p className="text-gray-500 text-sm mb-6">Submit your details to request an account for the AI portal.</p>

            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="relative">
                <User className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
                <input
                  type="text"
                  value={formData.name}
                  onChange={e => setFormData({...formData, name: e.target.value})}
                  placeholder="Full Name (e.g. Rajan Kumar)"
                  className="w-full pl-11 pr-4 py-3 bg-white border border-gray-200 rounded-xl text-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-brand-800/20 focus:border-brand-800 transition-all text-gray-800"
                />
              </div>
              <div className="relative">
                <Mail className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
                <input
                  type="text"
                  value={formData.badge_id}
                  onChange={e => setFormData({...formData, badge_id: e.target.value})}
                  placeholder="Badge ID (e.g. KP002)"
                  className="w-full pl-11 pr-4 py-3 bg-white border border-gray-200 rounded-xl text-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-brand-800/20 focus:border-brand-800 transition-all text-gray-800"
                />
              </div>
              <div className="relative">
                <Phone className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
                <input
                  type="text"
                  value={formData.phone}
                  onChange={e => setFormData({...formData, phone: e.target.value})}
                  placeholder="Phone Number"
                  className="w-full pl-11 pr-4 py-3 bg-white border border-gray-200 rounded-xl text-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-brand-800/20 focus:border-brand-800 transition-all text-gray-800"
                />
              </div>
              <div className="relative">
                <Building className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
                <input
                  type="text"
                  value={formData.station}
                  onChange={e => setFormData({...formData, station: e.target.value})}
                  placeholder="Home Station"
                  className="w-full pl-11 pr-4 py-3 bg-white border border-gray-200 rounded-xl text-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-brand-800/20 focus:border-brand-800 transition-all text-gray-800"
                />
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full bg-[#1a1c1a] text-white rounded-xl py-3.5 font-medium text-sm hover:bg-black transition-colors disabled:opacity-50 mt-4 flex items-center justify-center gap-2"
              >
                {loading ? <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></span> : 'Submit Request'}
              </button>
            </form>

            <p className="text-center text-xs text-gray-500 mt-6">
              Already have an account? <span onClick={() => navigate('/login')} className="text-brand-800 font-medium cursor-pointer">Sign in here</span>
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
