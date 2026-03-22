import { useState, useEffect } from 'react'
import { dashboardAPI } from '../api'
import { 
  LineChart, Line, BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, AreaChart, Area
} from 'recharts'
import { Shield, FileText, AlertTriangle, Target, TrendingUp, Users } from 'lucide-react'

const StatCard = ({ title, value, subtitle, icon: Icon, trend }) => (
  <div className="premium-card p-6 flex items-start gap-5">
    <div className="w-12 h-12 rounded-2xl bg-brand-50 text-brand-800 flex items-center justify-center flex-shrink-0 mt-1">
      <Icon size={24} strokeWidth={2} />
    </div>
    <div className="flex-1">
      <p className="text-sm font-semibold text-gray-500 mb-1">{title}</p>
      <div className="flex items-end gap-3">
        <h3 className="text-3xl font-bold text-gray-900">{value || 0}</h3>
        {trend && (
          <span className={`text-sm font-medium mb-1 ${trend > 0 ? 'text-brand-600' : 'text-red-500'}`}>
            {trend > 0 ? '+' : ''}{trend}%
          </span>
        )}
      </div>
      <p className="text-sm text-gray-400 mt-2">{subtitle}</p>
    </div>
  </div>
)

export default function Dashboard() {
  const [stats, setStats] = useState(null)
  
  useEffect(() => {
    dashboardAPI.getStats().then(res => setStats(res.data)).catch(console.error)
  }, [])

  if (!stats) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="w-10 h-10 border-4 border-brand-200 border-t-brand-800 rounded-full animate-spin"></div>
      </div>
    )
  }

  // Soft dribbble color palette for charts
  const colors = ['#145338', '#6A6E6C', '#97A09B', '#c4dfd1']

  return (
    <div className="space-y-8 animate-fade-in max-w-7xl mx-auto">
      
      {/* Header Area */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Intelligence Overview</h2>
          <p className="text-gray-500 mt-1">Real-time crime analytics and pattern detection for Kerala.</p>
        </div>
        <div className="flex gap-3">
          <button className="px-5 py-2.5 bg-white border border-gray-200 text-gray-700 rounded-xl text-sm font-medium hover:bg-surface-50 transition-colors shadow-sm">
            Export Report
          </button>
          <button className="premium-button py-2.5">
            Refresh Data
          </button>
        </div>
      </div>

      {/* KPI Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard title="Total FIRs Indexed" value={stats.total_firs} subtitle="Across all districts" icon={FileText} trend={12.5} />
        <StatCard title="High Risk Cases" value={stats.high_risk_cases} subtitle="Requires immediate action" icon={AlertTriangle} trend={-4.2} />
        <StatCard title="Active MO Patterns" value={stats.active_patterns} subtitle="Detected by AI in last 30d" icon={Target} trend={2.1} />
        <StatCard title="Officers Online" value="1,248" subtitle="Active sessions" icon={Users} trend={0.8} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* District Chart */}
        <div className="premium-card p-8 lg:col-span-2">
          <div className="flex items-center justify-between mb-8">
            <div>
              <h3 className="text-lg font-bold text-gray-900">Crime Volume by District</h3>
              <p className="text-sm text-gray-500 mt-1">7-day rolling average of registered FIRs</p>
            </div>
            <select className="bg-surface-50 border border-gray-200 text-gray-700 text-sm rounded-lg px-3 py-2 outline-none focus:border-brand-800">
              <option>Last 30 Days</option>
              <option>Last 3 Months</option>
              <option>Year to Date</option>
            </select>
          </div>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={stats.crimes_by_district}>
                <defs>
                  <linearGradient id="colorCount" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#145338" stopOpacity={0.1}/>
                    <stop offset="95%" stopColor="#145338" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E5E7EB" />
                <XAxis dataKey="district" axisLine={false} tickLine={false} tick={{fill: '#6B7280', fontSize: 12}} dy={10} />
                <YAxis axisLine={false} tickLine={false} tick={{fill: '#6B7280', fontSize: 12}} dx={-10} />
                <Tooltip 
                  contentStyle={{ borderRadius: '16px', border: 'none', boxShadow: '0 10px 40px -10px rgba(0,0,0,0.1)' }}
                  cursor={{stroke: '#145338', strokeWidth: 1, strokeDasharray: '4 4'}}
                />
                <Area type="monotone" dataKey="count" stroke="#145338" strokeWidth={3} fillOpacity={1} fill="url(#colorCount)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Categories Chart */}
        <div className="premium-card p-8 flex flex-col">
          <div>
            <h3 className="text-lg font-bold text-gray-900">Categorical Distribution</h3>
            <p className="text-sm text-gray-500 mt-1">Top reported crime types</p>
          </div>
          <div className="flex-1 mt-8 min-h-[300px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={stats.crimes_by_category} layout="vertical" margin={{ left: -20 }}>
                <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#E5E7EB" />
                <XAxis type="number" axisLine={false} tickLine={false} tick={{fill: '#6B7280', fontSize: 12}} />
                <YAxis dataKey="category" type="category" axisLine={false} tickLine={false} tick={{fill: '#374151', fontSize: 13, fontWeight: 500}} width={100} />
                <Tooltip 
                  cursor={{fill: '#F3F4F6'}}
                  contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 4px 20px rgba(0,0,0,0.08)' }}
                />
                <Bar dataKey="count" fill="#145338" radius={[0, 8, 8, 0]} barSize={24} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Recent Alerts */}
        <div className="premium-card p-8 lg:col-span-3">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-lg font-bold text-gray-900 flex items-center gap-2">
              <AlertTriangle className="text-orange-500" size={20} />
              Recent AI Intelligence Alerts
            </h3>
            <button className="text-brand-800 text-sm font-medium hover:text-brand-900">View All →</button>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {[
              { title: 'Series of 2W Thefts', loc: 'Thiruvananthapuram', cases: 14, risk: 'High' },
              { title: 'Financial Fraud Link', loc: 'Kochi City', cases: 8, risk: 'Critical' },
              { title: 'Highway Robbery Pattern', loc: 'Palakkad', cases: 5, risk: 'Medium' }
            ].map((alert, i) => (
              <div key={i} className="p-5 border border-gray-100 rounded-2xl hover:shadow-soft transition-shadow bg-surface-50/50">
                <div className="flex justify-between items-start mb-3">
                  <span className={`px-2.5 py-1 rounded-full text-xs font-semibold ${alert.risk==='Critical' ? 'bg-red-100 text-red-700' : alert.risk==='High' ? 'bg-orange-100 text-orange-700' : 'bg-amber-100 text-amber-700'}`}>
                    {alert.risk} Risk
                  </span>
                  <span className="text-xs text-gray-500 font-medium">{alert.cases} Cases</span>
                </div>
                <h4 className="font-bold text-gray-900 text-base">{alert.title}</h4>
                <p className="text-sm text-gray-500 mt-1 flex items-center gap-1.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-gray-300"></span> {alert.loc}
                </p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
