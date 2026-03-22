import { useState, useEffect } from 'react'
import { Outlet, useNavigate, useLocation } from 'react-router-dom'
import { authAPI } from '../api'
import { 
  Shield, 
  LayoutDashboard, 
  Search, 
  Map, 
  BookOpen, 
  Globe, 
  LogOut,
  Bell,
  Menu
} from 'lucide-react'

export default function Layout({ children }) {
  const navigate = useNavigate()
  const location = useLocation()
  const [user, setUser] = useState(null)

  useEffect(() => {
    authAPI.me()
      .then(res => setUser(res.data))
      .catch(() => {
        localStorage.removeItem('kpai_token')
        localStorage.removeItem('kpai_officer')
        navigate('/login')
      })
  }, [navigate])

  const menu = [
    { name: 'Dashboard', path: '/', icon: LayoutDashboard },
    { name: 'FIR Analysis', path: '/fir', icon: Search },
    { name: 'Case Intelligence', path: '/cases', icon: Map },
    { name: 'MO Patterns', path: '/patterns', icon: Map }, // Map/Target
    { name: 'Legal Assistant', path: '/legal', icon: BookOpen },
    { name: 'Malayalam FIR', path: '/malayalam', icon: Globe },
  ]

  const logout = () => { 
    localStorage.removeItem('kpai_token')
    localStorage.removeItem('kpai_officer')
    navigate('/login') 
  }

  if (!user) return null

  return (
    <div className="flex h-screen bg-surface-50 overflow-hidden text-gray-800">
      
      {/* Sidebar */}
      <aside className="w-[280px] bg-white border-r border-gray-100 flex-shrink-0 flex flex-col">
        {/* Brand */}
        <div className="flex items-center gap-3 px-8 py-8">
          <div className="w-8 h-8 rounded-xl bg-brand-800 flex items-center justify-center">
            <Shield className="text-white" size={18} strokeWidth={2.5} />
          </div>
          <span className="font-bold text-gray-900 tracking-tight text-lg">Kerala Police AI</span>
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-4 space-y-1.5 mt-4">
          <p className="px-4 text-[10px] font-semibold text-gray-400 uppercase tracking-widest mb-4">GENERAL</p>
          {menu.map(m => {
            const Icon = m.icon
            const active = location.pathname === m.path
            return (
              <button
                key={m.name}
                onClick={() => navigate(m.path)}
                className={`w-full flex items-center gap-3 px-4 py-3.5 rounded-2xl transition-all text-sm font-medium ${
                  active 
                    ? 'bg-surface-50 text-brand-800 shadow-sm' 
                    : 'text-gray-500 hover:bg-surface-50/50 hover:text-gray-800'
                }`}
              >
                <Icon size={18} strokeWidth={active ? 2.5 : 2} className={active ? 'text-brand-800' : 'text-gray-400'} />
                {m.name}
              </button>
            )
          })}
        </nav>

        {/* User Card */}
        <div className="p-4 mb-4 mx-4 border-t border-gray-100 pt-6">
          <div className="flex items-center gap-3 px-2 mb-4">
            <div className="w-10 h-10 rounded-full bg-surface-100 border border-gray-200 flex items-center justify-center flex-shrink-0">
              <span className="text-brand-800 font-bold text-sm">SI</span>
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-semibold text-gray-900 truncate">{user.name}</p>
              <p className="text-xs text-gray-500 truncate">{user.station}</p>
            </div>
          </div>
          <button 
            onClick={logout} 
            className="w-full flex items-center justify-center gap-2 text-sm text-red-600 font-medium py-2.5 rounded-xl hover:bg-red-50 transition-colors"
          >
            <LogOut size={16} /> Logout
          </button>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 bg-surface-50">
        
        {/* Top Header */}
        <header className="h-20 bg-white border-b border-gray-100 flex items-center justify-between px-10 flex-shrink-0 z-10">
          <div className="flex items-center gap-4">
            <button className="text-gray-400 hover:text-gray-600 lg:hidden">
              <Menu size={20} />
            </button>
            <h1 className="text-xl font-bold text-gray-800">
              {menu.find(m => m.path === location.pathname)?.name || 'Dashboard'}
            </h1>
          </div>
          
          <div className="flex items-center gap-4">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={16} />
              <input 
                type="text" 
                placeholder="Search cases..." 
                className="w-64 pl-10 pr-4 py-2.5 bg-surface-50 border border-transparent rounded-full text-sm focus:bg-white focus:border-brand-800/30 focus:outline-none focus:ring-4 focus:ring-brand-800/10 transition-all text-gray-700"
              />
            </div>
            <button className="w-10 h-10 rounded-full border border-gray-200 flex items-center justify-center text-gray-500 hover:bg-surface-50 transition-colors relative">
              <span className="absolute top-2.5 right-2.5 w-2 h-2 bg-red-500 border border-white rounded-full"></span>
              <Bell size={18} />
            </button>
          </div>
        </header>

        {/* Scrollable Content */}
        <main className="flex-1 overflow-y-auto scroll-y p-10">
          {children}
        </main>
      </div>
    </div>
  )
}
