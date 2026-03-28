import { useState, useEffect } from 'react'
import { firsAPI, analysisAPI } from '../api'
import toast from 'react-hot-toast'
import { Search, RefreshCw, Scale, Link2, FileText, ChevronRight, AlertTriangle } from 'lucide-react'

const RISK_CONFIG = {
  critical: { cls: 'risk-critical', label: 'Critical' },
  high: { cls: 'risk-high', label: 'High' },
  medium: { cls: 'risk-medium', label: 'Medium' },
  low: { cls: 'risk-low', label: 'Low' },
}

const STATUS_CONFIG = {
  pending: { cls: 'bg-gray-100 text-gray-600 border-gray-200', label: 'Pending' },
  indexed: { cls: 'bg-blue-50 text-brand-700 border-blue-100', label: 'Indexed' },
  analysed: { cls: 'bg-emerald-50 text-emerald-700 border-emerald-100', label: 'Analysed' },
  closed: { cls: 'bg-gray-50 text-gray-500 border-gray-200', label: 'Closed' },
}

export default function CaseIntelligence() {
  const [firs, setFirs] = useState([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState('all')
  const [search, setSearch] = useState('')
  const [selected, setSelected] = useState(null)
  const [similar, setSimilar] = useState([])
  const [loadingSimilar, setLoadingSimilar] = useState(false)

  const loadFIRs = async () => {
    try {
      const params = {}
      if (filter === 'high') params.risk_level = 'high'
      if (filter === 'critical') params.risk_level = 'critical'
      if (filter === 'indexed') params.status = 'indexed'
      const res = await firsAPI.list(params)
      setFirs(res.data)
    } catch (e) { toast.error('Failed to load cases') }
    finally { setLoading(false) }
  }

  useEffect(() => { loadFIRs() }, [filter])

  const selectFIR = async (fir) => {
    setSelected(fir)
    setSimilar([])
    if (fir.status === 'indexed') {
      setLoadingSimilar(true)
      try {
        const res = await analysisAPI.getSimilar(fir.id)
        setSimilar(res.data)
      } catch {}
      finally { setLoadingSimilar(false) }
    }
  }

  const handleRetrain = async (fir) => {
    toast.loading('Indexing to vector database...', { id: 'retrain' })
    try {
      await firsAPI.train(fir.id)
      toast.success('Training complete', { id: 'retrain' })
      setTimeout(loadFIRs, 1500)
    } catch { toast.error('Indexing failed', { id: 'retrain' }) }
  }

  const filtered = firs.filter(f =>
    !search || f.case_number.toLowerCase().includes(search.toLowerCase()) || f.district?.toLowerCase().includes(search.toLowerCase())
  )

  return (
    <div className="flex gap-8 h-full animate-fade-in max-w-[1400px] mx-auto" style={{ minHeight: 'calc(100vh - 120px)' }}>
      {/* Case List Sidebar */}
      <div className="w-[340px] flex-shrink-0 flex flex-col h-full premium-card overflow-hidden bg-white">
        <div className="p-5 border-b border-gray-100 bg-white z-10">
          <div className="relative mb-4">
            <Search size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-400" />
            <input
              value={search}
              onChange={e => setSearch(e.target.value)}
              placeholder="Search case number or district..."
              className="w-full bg-surface-50 border border-transparent rounded-xl pl-10 pr-4 py-2.5 text-sm text-gray-800 placeholder-gray-400 focus:bg-white focus:outline-none focus:ring-2 focus:ring-brand-800/10 focus:border-brand-800/30 transition-all"
            />
          </div>
          <div className="flex gap-2 p-1 bg-surface-50 rounded-lg overflow-x-auto scroll-none">
            {['all', 'high', 'critical', 'indexed'].map(f => (
              <button 
                key={f} 
                onClick={() => setFilter(f)} 
                className={`text-xs font-medium px-4 py-1.5 rounded-md capitalize whitespace-nowrap transition-all ${filter === f ? 'bg-white text-brand-800 shadow-sm' : 'text-gray-500 hover:text-gray-700'}`}>
                {f}
              </button>
            ))}
          </div>
        </div>

        <div className="flex-1 overflow-y-auto scroll-y p-3 space-y-2 bg-surface-50">
          {loading ? [...Array(6)].map((_, i) => <div key={i} className="h-24 bg-white rounded-2xl border border-gray-100 animate-pulse"></div>) :
          filtered.length === 0 ? (
            <div className="py-12 text-center">
              <div className="w-12 h-12 bg-white rounded-full flex items-center justify-center mx-auto mb-3 shadow-sm text-gray-300">
                <Search size={20} />
              </div>
              <p className="text-sm font-bold text-gray-900">No cases found</p>
              <p className="text-xs text-gray-500 mt-1">Adjust filters or search parameters</p>
            </div>
          ) : filtered.map(fir => (
            <button
              key={fir.id}
              onClick={() => selectFIR(fir)}
              className={`w-full text-left p-4 rounded-2xl transition-all outline-none border ${selected?.id === fir.id ? 'bg-brand-800 text-white border-brand-800 shadow-float ring-4 ring-brand-800/10' : 'bg-white border-gray-100 hover:border-brand-200 hover:shadow-sm'}`}
            >
              <div className="flex items-start justify-between gap-3 mb-2">
                <p className={`text-sm font-bold truncate ${selected?.id === fir.id ? 'text-white' : 'text-gray-900'}`}>{fir.case_number}</p>
                <span className={`status-badge ${selected?.id === fir.id ? 'bg-white/20 border-white/20 text-white' : RISK_CONFIG[fir.risk_level]?.cls}`}>
                  {RISK_CONFIG[fir.risk_level]?.label || fir.risk_level}
                </span>
              </div>
              <p className={`text-xs font-medium truncate mb-3 ${selected?.id === fir.id ? 'text-brand-100' : 'text-gray-500'}`}>
                {fir.district} • {fir.police_station}
              </p>
              <div className={`flex items-center justify-between pt-3 border-t ${selected?.id === fir.id ? 'border-brand-700/50' : 'border-gray-50'}`}>
                <span className={`status-badge ${selected?.id === fir.id ? 'bg-white/10 border-white/10 text-white' : STATUS_CONFIG[fir.status]?.cls}`}>
                  {STATUS_CONFIG[fir.status]?.label || fir.status}
                </span>
                <span className={`text-xs font-medium ${selected?.id === fir.id ? 'text-brand-200' : 'text-gray-400'}`}>
                  {new Date(fir.date_registered).toLocaleDateString('en-IN', {day:'2-digit',month:'short',year:'numeric'})}
                </span>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Detail Panel */}
      <div className="flex-1 h-full overflow-y-auto scroll-y pr-2">
        {!selected ? (
          <div className="h-full flex items-center justify-center text-center">
            <div className="premium-card p-12 max-w-sm w-full mx-auto shadow-float">
              <div className="w-20 h-20 bg-brand-50 rounded-full flex items-center justify-center mx-auto mb-6 text-brand-800">
                <FileText size={32} />
              </div>
              <h3 className="text-xl font-bold text-gray-900">No Case Selected</h3>
              <p className="text-gray-500 mt-2 text-sm leading-relaxed">Select a case from the intelligence sidebar to view the full investigative payload, extraction graphs, and associated IPCs.</p>
            </div>
          </div>
        ) : (
          <div className="space-y-6 animate-fade-in pb-10">
            {/* Header Card */}
            <div className="premium-card p-8 relative overflow-hidden">
              <div className="absolute top-0 left-0 w-2 h-full bg-brand-800"></div>
              <div className="flex items-start justify-between gap-6">
                <div>
                  <div className="flex items-center gap-3 mb-2">
                    <span className={`status-badge ${RISK_CONFIG[selected.risk_level]?.cls}`}>
                      {RISK_CONFIG[selected.risk_level]?.label} Risk
                    </span>
                    <span className="text-sm font-medium text-gray-500">{selected.crime_category}</span>
                  </div>
                  <h2 className="text-2xl font-bold text-gray-900">{selected.case_number}</h2>
                  <p className="text-brand-800 font-medium text-sm mt-1 flex items-center gap-2">
                    {selected.police_station}, {selected.district}
                  </p>
                </div>
                <div className="flex flex-col items-end gap-3">
                  <span className={`status-badge py-1.5 px-4 text-xs ${STATUS_CONFIG[selected.status]?.cls}`}>
                    {STATUS_CONFIG[selected.status]?.label}
                  </span>
                  <button onClick={() => handleRetrain(selected)} className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-200 rounded-xl text-sm font-medium text-gray-700 hover:bg-surface-50 transition-colors shadow-sm">
                    <RefreshCw size={14} className="text-gray-500" /> Force Re-index
                  </button>
                </div>
              </div>

              {selected.ai_summary && (
                <div className="mt-8 pt-6 border-t border-gray-100">
                  <h3 className="text-xs font-bold text-gray-400 uppercase tracking-widest mb-3">AI Intelligence Summary</h3>
                  <p className="text-gray-700 text-sm leading-relaxed bg-surface-50 p-5 rounded-2xl border border-gray-100">{selected.ai_summary}</p>
                </div>
              )}
            </div>

            {/* Entities */}
            {selected.extracted_entities && Object.keys(selected.extracted_entities).length > 0 && (
              <div className="premium-card p-8">
                <h3 className="text-xs font-bold text-gray-400 uppercase tracking-widest mb-6">Extracted Entities</h3>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                  {Object.entries(selected.extracted_entities)
                    .filter(([, v]) => v && (Array.isArray(v) ? v.length : true))
                    .map(([k, v]) => (
                    <div key={k} className="bg-surface-50 border border-gray-100 rounded-2xl p-4 transition-colors hover:border-brand-200 hover:bg-white">
                      <p className="text-[10px] font-bold text-gray-400 uppercase tracking-wider mb-1">{k.replace(/_/g, ' ')}</p>
                      <p className="text-sm font-semibold text-gray-900">{Array.isArray(v) ? v.join(' • ') : v}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* IPC Sections */}
            {selected.ipc_sections?.length > 0 && (
              <div className="premium-card p-8">
                <div className="flex items-center justify-between mb-6">
                  <h3 className="text-xs font-bold text-gray-400 uppercase tracking-widest flex items-center gap-2">
                    <Scale size={16} /> IPC Sections Cited
                  </h3>
                </div>
                <div className="space-y-3">
                  {selected.ipc_sections.map((s, i) => (
                    <div key={i} className="flex items-start gap-4 bg-white border border-gray-100 p-5 rounded-2xl shadow-sm hover:border-brand-200 transition-colors group">
                      <span className="font-bold text-sm text-brand-800 bg-brand-50 px-3 py-1.5 rounded-xl border border-brand-100 group-hover:bg-brand-100">§ {s.section}</span>
                      <div className="flex-1">
                        <p className="text-sm font-bold text-gray-900">{s.title}</p>
                        <p className="text-xs font-medium text-gray-500 mt-1">{s.punishment}</p>
                      </div>
                      <span className="text-xs font-bold text-brand-600 bg-white border border-gray-100 shadow-sm px-3 py-1.5 rounded-lg flex-shrink-0">
                        {Math.round(s.confidence * 100)}% Match
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Similar Cases */}
            <div className="premium-card p-8">
              <h3 className="text-xs font-bold text-gray-400 uppercase tracking-widest mb-6 flex items-center gap-2">
                <Link2 size={16} /> Similar Cases (Vector Semantics)
              </h3>
              {selected.status !== 'indexed' ? (
                <div className="bg-orange-50 text-orange-700 p-4 rounded-xl text-sm font-medium border border-orange-100 flex items-center gap-2">
                  <AlertTriangle size={16} />
                  Document must be indexed. Click "Force Re-index" to generate embeddings.
                </div>
              ) : loadingSimilar ? (
                <div className="flex items-center gap-3 text-brand-700 text-sm font-medium bg-brand-50 p-4 rounded-xl border border-brand-100">
                  <span className="w-4 h-4 border-2 border-brand-200 border-t-brand-700 rounded-full animate-spin"></span>
                  Querying Vector Database (Chroma)...
                </div>
              ) : similar.length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {similar.map((s, i) => (
                    <div key={i} className="flex flex-col bg-surface-50 p-5 rounded-2xl border border-gray-100 hover:border-brand-200 hover:bg-white transition-all cursor-pointer group">
                      <div className="flex items-center justify-between mb-2">
                        <p className="text-sm font-bold text-gray-900 group-hover:text-brand-800 transition-colors">{s.metadata?.case_number || s.id}</p>
                        <span className="text-[10px] font-bold text-brand-700 bg-white shadow-sm px-2 py-1 rounded-md border border-gray-100">
                          {(s.similarity * 100).toFixed(0)}%
                        </span>
                      </div>
                      <p className="text-xs font-medium text-gray-500 flex items-center justify-between mt-auto pt-2 border-t border-gray-100">
                        <span>{s.metadata?.district}</span>
                        <ChevronRight size={14} className="text-gray-300 group-hover:text-brand-800" />
                      </p>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-gray-500 font-medium bg-surface-50 p-4 rounded-xl border border-gray-100 text-center">
                  No semantic matches found in current cluster.
                </p>
              )}
            </div>

            {/* Raw text preview */}
            <div className="premium-card p-8 bg-surface-50 border-none relative overflow-hidden">
              <h3 className="text-xs font-bold text-gray-400 uppercase tracking-widest mb-6 flex items-center gap-2 relative z-10">
                <FileText size={16} /> Raw Payload Preview
              </h3>
              <div className="bg-white border border-gray-200 p-6 rounded-2xl relative z-10 shadow-sm">
                <p className="text-sm text-gray-600 leading-relaxed font-mono whitespace-pre-wrap">{selected.raw_text?.slice(0, 800)}{selected.raw_text?.length > 800 ? '...' : ''}</p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
