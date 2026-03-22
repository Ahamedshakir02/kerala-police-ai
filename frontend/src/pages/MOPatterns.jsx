import { useState, useEffect } from 'react'
import { patternsAPI } from '../api'
import toast from 'react-hot-toast'
import { AlertTriangle, Hash, Building2, MapPin, Target, Link2, Map } from 'lucide-react'

// Map risks to index.css badge classes
const RISK_STYLES = {
  critical: { badge: 'risk-critical', icon: 'text-red-600 bg-red-100' },
  high: { badge: 'risk-high', icon: 'text-orange-600 bg-orange-100' },
  medium: { badge: 'risk-medium', icon: 'text-amber-600 bg-amber-100' },
  low: { badge: 'risk-low', icon: 'text-emerald-600 bg-emerald-100' },
}

export default function MOPatterns() {
  const [patterns, setPatterns] = useState([])
  const [loading, setLoading] = useState(true)
  const [selected, setSelected] = useState(null)

  useEffect(() => {
    patternsAPI.getMOAlerts()
      .then(res => { setPatterns(res.data); if (res.data.length) setSelected(res.data[0]) })
      .catch(() => toast.error('Failed to load MO patterns'))
      .finally(() => setLoading(false))
  }, [])

  return (
    <div className="space-y-6 animate-fade-in max-w-7xl mx-auto">
      
      {/* Alert Banner */}
      {patterns.some(p => p.risk_level === 'critical') && (
        <div className="premium-card p-6 border-red-200 bg-gradient-to-r from-red-50 to-white flex items-center gap-6 shadow-sm">
          <div className="w-14 h-14 bg-red-100 rounded-2xl flex items-center justify-center flex-shrink-0 animate-pulse">
            <AlertTriangle size={28} strokeWidth={2.5} className="text-red-700" />
          </div>
          <div>
            <p className="text-lg font-bold text-red-800 tracking-tight">Critical Patterns Detected</p>
            <p className="text-sm font-medium text-red-600 mt-1">
              {patterns.filter(p => p.risk_level === 'critical').length} critical pattern(s) require immediate review and district-wide alert broadcast
            </p>
          </div>
          <button className="ml-auto bg-red-700 text-white px-5 py-2.5 font-bold text-sm rounded-xl hover:bg-red-800 transition-colors shadow-sm">
            Review Alerts
          </button>
        </div>
      )}

      <div className="flex gap-8" style={{ minHeight: 'calc(100vh - 200px)' }}>
        
        {/* Pattern List */}
        <div className="w-96 flex-shrink-0 flex flex-col h-full space-y-4">
          <div className="flex items-center justify-between pb-2 border-b border-gray-200">
            <h3 className="text-sm font-bold text-gray-900 flex items-center gap-2">
              <Map size={16} className="text-brand-800"/> Tracked Clusters
            </h3>
            <span className="text-xs font-bold text-gray-500 bg-gray-100 px-3 py-1 rounded-full">{patterns.length}</span>
          </div>
          
          <div className="flex-1 overflow-y-auto scroll-y space-y-3 pb-8 pr-1">
            {loading ? [...Array(6)].map((_, i) => <div key={i} className="h-28 bg-white border border-gray-100 rounded-2xl animate-pulse"></div>) :
            patterns.map(p => {
              const styles = RISK_STYLES[p.risk_level] || RISK_STYLES.low
              return (
                <button
                  key={p.cluster_id}
                  onClick={() => setSelected(p)}
                  className={`w-full text-left p-5 rounded-2xl transition-all outline-none border block ${selected?.cluster_id === p.cluster_id ? 'bg-white border-brand-800 shadow-float ring-4 ring-brand-800/5 z-10 relative' : 'bg-surface-50 border-transparent hover:bg-white hover:border-gray-200 hover:shadow-sm'}`}
                >
                  <div className="flex items-start justify-between gap-3 mb-3">
                    <div className="flex items-center gap-3">
                      <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${styles.icon}`}>
                        <Target size={20} strokeWidth={2.5}/>
                      </div>
                      <div>
                        <p className="text-sm font-bold text-gray-900 mb-0.5">{p.pattern_name}</p>
                        <p className="text-xs font-medium text-gray-500 truncate max-w-[160px]">{p.crime_type}</p>
                      </div>
                    </div>
                  </div>
                  
                  <div className="flex items-center justify-between mt-4">
                    <span className={`status-badge px-2 py-0.5 text-[10px] ${styles.badge}`}>
                      {p.risk_level} Base
                    </span>
                    <div className="flex items-center gap-3 text-xs font-bold text-gray-600">
                      <span className="flex items-center gap-1.5"><Hash size={12} className="text-gray-400"/> {p.occurrences} Cases</span>
                    </div>
                  </div>
                </button>
              )
            })}
          </div>
        </div>

        {/* Detail Panel */}
        <div className="flex-1 overflow-y-auto scroll-y pr-2">
          {!selected ? (
            <div className="h-full flex items-center justify-center text-center pb-20">
              <div className="premium-card p-12 max-w-sm w-full shadow-float">
                <div className="w-20 h-20 bg-surface-50 rounded-full flex items-center justify-center mx-auto mb-6 text-brand-800">
                  <Target size={32} />
                </div>
                <h3 className="text-xl font-bold text-gray-900">Pattern Insight</h3>
                <p className="text-gray-500 mt-2 text-sm leading-relaxed">Select an active Modus Operandi (MO) pattern from the sidebar to inspect geographic clusters and tactical response data.</p>
              </div>
            </div>
          ) : (
            <div className="space-y-6 animate-fade-in pb-10">
              
              {/* Header Card */}
              <div className="premium-card p-10 relative overflow-hidden bg-white">
                <div className="absolute top-0 right-0 p-8 opacity-5 text-brand-800 pointer-events-none">
                  <Target size={180}/>
                </div>
                
                <div className="flex items-start justify-between gap-6 relative z-10">
                  <div className="max-w-xl">
                    <div className="flex items-center gap-3 mb-4">
                      <span className="text-xs font-bold text-brand-800 bg-brand-50 border border-brand-100 px-3 py-1 rounded-lg">ID: {selected.cluster_id}</span>
                      <span className={`status-badge px-3 py-1 ${RISK_STYLES[selected.risk_level]?.badge}`}>
                        {selected.risk_level} Risk
                      </span>
                    </div>
                    <h2 className="text-3xl font-bold tracking-tight text-gray-900 mb-2">{selected.pattern_name}</h2>
                    <p className="text-gray-500 font-medium">{selected.crime_type}</p>
                    
                    <p className="text-base text-gray-700 leading-relaxed mt-6">{selected.description}</p>
                  </div>
                  
                  <div className="text-right bg-surface-50 border border-gray-100 p-6 rounded-3xl min-w-[140px] shadow-sm">
                    <p className="text-4xl font-bold text-brand-800 leading-none">{selected.occurrences}</p>
                    <p className="text-sm font-semibold text-gray-500 mt-2.5">Total Detections</p>
                  </div>
                </div>
              </div>

              {/* Districts */}
              <div className="premium-card p-8">
                <h3 className="text-xs font-bold text-gray-400 uppercase tracking-widest mb-6 flex items-center gap-2">
                  <MapPin size={16} /> Identified Hot Zones
                </h3>
                <div className="flex flex-wrap gap-3">
                  {selected.districts.map(d => (
                    <span key={d} className="text-sm font-bold px-5 py-2.5 rounded-xl border border-gray-200 bg-surface-50 text-gray-800 shadow-sm flex items-center gap-2">
                      <span className="w-2 h-2 rounded-full bg-brand-500"></span> {d}
                    </span>
                  ))}
                </div>
              </div>

              {/* Recommended Action */}
              <div className="premium-card p-8 border-l-4 border-l-brand-600 bg-brand-50/30">
                <h3 className="text-xs font-bold text-brand-800 uppercase tracking-widest mb-4 flex items-center gap-2">
                  <Target size={16} /> Tactical Response Protocol
                </h3>
                <p className="text-gray-900 text-base font-medium leading-relaxed">{selected.recommended_action}</p>
              </div>

              {/* Linked FIRs */}
              {selected.fir_ids?.length > 0 && (
                <div className="premium-card p-8">
                  <h3 className="text-xs font-bold text-gray-400 uppercase tracking-widest mb-6 flex items-center gap-2">
                    <Link2 size={16} /> Linked Case Files ({selected.fir_ids.length})
                  </h3>
                  <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                    {selected.fir_ids.slice(0, 12).map(id => (
                      <div key={id} className="text-sm font-bold text-gray-800 bg-surface-50 px-4 py-3 border border-gray-100 rounded-xl flex items-center justify-between hover:bg-white hover:border-brand-200 hover:shadow-sm transition-all cursor-pointer">
                        {id}
                        <Link2 size={14} className="text-gray-400" />
                      </div>
                    ))}
                    {selected.fir_ids.length > 12 && (
                      <div className="text-sm font-bold text-brand-800 bg-brand-50 border border-brand-100 px-4 py-3 rounded-xl flex items-center justify-center cursor-pointer hover:bg-brand-100 transition-colors">
                        + {selected.fir_ids.length - 12} More Cases
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
