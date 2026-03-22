import { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import toast from 'react-hot-toast'
import { analysisAPI, firsAPI } from '../api'
import { Paperclip, UploadCloud, BrainCircuit, Microscope, Scale, Search, ClipboardList, Link2 } from 'lucide-react'

const RiskBadge = ({ level }) => {
  const cls = level === 'critical' ? 'bg-red-50 text-red-700 border-red-200' : 
              level === 'high' ? 'bg-orange-50 text-orange-700 border-orange-200' : 
              level === 'medium' ? 'bg-amber-50 text-amber-700 border-amber-200' : 
              'bg-emerald-50 text-emerald-700 border-emerald-200'
  return <span className={`text-xs px-3 py-1 border rounded-full font-bold uppercase tracking-wider ${cls}`}>{level} Risk</span>
}

const ConfidenceBar = ({ value }) => (
  <div className="flex items-center gap-3">
    <div className="flex-1 bg-gray-100 h-2 rounded-full overflow-hidden">
      <div className="h-full bg-brand-500 rounded-full" style={{ width: `${Math.round(value * 100)}%` }}></div>
    </div>
    <span className="text-xs text-gray-500 font-medium w-10 text-right">{Math.round(value * 100)}%</span>
  </div>
)

export default function FIRAnalysis() {
  const [text, setText] = useState('')
  const [caseNumber, setCaseNumber] = useState('')
  const [district, setDistrict] = useState('')
  const [station, setStation] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [uploadMode, setUploadMode] = useState('text') 
  const [file, setFile] = useState(null)
  const [saveAndIndex, setSaveAndIndex] = useState(false)

  const onDrop = useCallback((accepted) => {
    if (accepted[0]) { setFile(accepted[0]); setUploadMode('file') }
  }, [])
  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop, accept: { 'text/plain': ['.txt'], 'application/pdf': ['.pdf'] }, maxFiles: 1
  })

  const loadSample = () => {
    setText(`FIR No: 247/2024\nPolice Station: Thiruvananthapuram East\nDistrict: Thiruvananthapuram\n\nOn 15/03/2024 at approximately 22:30 hrs, complainant Rajesh Kumar (Age 34) reported that two unknown accused persons arrived on a motorcycle wearing helmets. One accused person held him at knifepoint and threatened him. The second accused stole mobile phones worth Rs. 3,50,000/-, cash of Rs. 85,000/-, and a gold chain worth Rs. 95,000/-. Total stolen property: Rs. 5,30,000/-. Both accused fled on the motorcycle towards Statue Road. Witnesses: Mohan Lal and Sreeraj K.`)
    setCaseNumber('KER/TVM/247/2024')
    setDistrict('Thiruvananthapuram')
    setStation('Thiruvananthapuram East')
    setUploadMode('text')
    toast.success('Sample Data Loaded')
  }

  const handleAnalyze = async () => {
    const firText = uploadMode === 'text' ? text : (file ? await file.text() : '')
    if (!firText.trim() || firText.length < 20) { toast.error('Document text too short'); return }
    setLoading(true)
    setResult(null)
    try {
      if (saveAndIndex && caseNumber && district && station) {
        const fd = new FormData()
        fd.append('case_number', caseNumber)
        fd.append('district', district)
        fd.append('police_station', station)
        fd.append('text', firText)
        const uploadRes = await firsAPI.upload(fd)
        toast.success(`FIR indexed to database (${uploadRes.data.case_number})`)
      }
      const res = await analysisAPI.analyzeFIR(firText)
      setResult(res.data)
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Analysis failed — check connection')
    } finally { setLoading(false) }
  }

  return (
    <div className="grid grid-cols-1 xl:grid-cols-2 gap-8 max-w-7xl mx-auto">
      {/* INPUT PANEL */}
      <div className="space-y-6">
        <div className="premium-card p-8">
          <div className="flex items-center justify-between mb-6 pb-4 border-b border-gray-100">
            <h2 className="text-lg font-bold text-gray-900">Data Ingestion</h2>
            <div className="flex gap-2 bg-surface-50 p-1 rounded-xl border border-gray-100">
              <button 
                onClick={() => setUploadMode('text')} 
                className={`px-4 py-1.5 rounded-lg text-sm font-medium transition-all ${uploadMode==='text' ? 'bg-white shadow-sm text-brand-800' : 'text-gray-500 hover:text-gray-700'}`}>Text</button>
              <button 
                onClick={() => setUploadMode('file')} 
                className={`px-4 py-1.5 rounded-lg text-sm font-medium transition-all ${uploadMode==='file' ? 'bg-white shadow-sm text-brand-800' : 'text-gray-500 hover:text-gray-700'}`}>File</button>
            </div>
          </div>

          {uploadMode === 'file' ? (
            <div {...getRootProps()} className={`border-2 border-dashed rounded-2xl p-12 flex flex-col items-center justify-center cursor-pointer transition-all ${isDragActive ? 'border-brand-500 bg-brand-50' : 'border-gray-200 bg-surface-50 hover:bg-gray-50'}`}>
              <input {...getInputProps()} />
              {file ? (
                <div className="text-center">
                  <div className="w-16 h-16 bg-white rounded-full shadow-sm flex items-center justify-center mx-auto mb-4 text-brand-500">
                    <Paperclip size={28} />
                  </div>
                  <p className="font-semibold text-gray-900">{file.name}</p>
                  <p className="text-gray-500 text-sm mt-1">{(file.size / 1024).toFixed(1)} KB</p>
                </div>
              ) : (
                <div className="text-center">
                  <div className="w-16 h-16 bg-white rounded-full shadow-sm flex items-center justify-center mx-auto mb-4 text-gray-400">
                    <UploadCloud size={28} />
                  </div>
                  <p className="font-medium text-gray-700">{isDragActive ? 'Drop document here' : 'Click or drop PDF/TXT file'}</p>
                  <p className="text-sm text-gray-400 mt-1">Maximum file size 5MB</p>
                </div>
              )}
            </div>
          ) : (
            <textarea
              value={text}
              onChange={e => setText(e.target.value)}
              rows={12}
              placeholder="Paste FIR data here (English or Malayalam)..."
              className="w-full bg-surface-50 border border-gray-200 rounded-2xl p-5 text-gray-800 text-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-brand-800/20 focus:border-brand-800 transition-all resize-none leading-relaxed"
            />
          )}

          <div className="flex items-center justify-between mt-4">
            <span className="text-xs font-semibold text-gray-400 uppercase tracking-widest">{text.length} characters</span>
            <button onClick={loadSample} className="text-sm font-medium text-brand-600 hover:text-brand-800 transition-colors">Inject Sample Data</button>
          </div>
        </div>

        {/* Configuration */}
        <div className="premium-card p-6">
          <label className="flex items-center gap-3 cursor-pointer group">
            <div className={`w-5 h-5 rounded border flex items-center justify-center transition-colors ${saveAndIndex ? 'bg-brand-800 border-brand-800 text-white' : 'border-gray-300 bg-white group-hover:border-brand-800'}`}>
              {saveAndIndex && <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" /></svg>}
            </div>
            <span className="text-sm font-medium text-gray-700">Save and index to Vector Database (ChromaDB)</span>
          </label>
          
          {saveAndIndex && (
            <div className="grid grid-cols-3 gap-4 animate-fade-in mt-5 pt-5 border-t border-gray-100">
              <input value={caseNumber} onChange={e => setCaseNumber(e.target.value)} placeholder="Case No." className="premium-input" />
              <input value={district} onChange={e => setDistrict(e.target.value)} placeholder="District" className="premium-input" />
              <input value={station} onChange={e => setStation(e.target.value)} placeholder="Station" className="premium-input" />
            </div>
          )}
        </div>

        <button
          onClick={handleAnalyze}
          disabled={loading}
          className="w-full py-4 bg-brand-800 text-white hover:bg-brand-900 rounded-2xl font-bold text-sm transition-all disabled:opacity-50 flex items-center justify-center gap-3 shadow-sm"
        >
          {loading ? (
            <><span className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></span> Processing NLP Pipeline...</>
          ) : <><BrainCircuit size={20} /> Run AI Analysis</>}
        </button>
      </div>

      {/* RESULTS PANEL */}
      <div className="space-y-6">
        {!result && !loading && (
          <div className="premium-card p-12 flex flex-col items-center justify-center text-center h-[500px]">
            <div className="w-20 h-20 bg-surface-50 rounded-full flex items-center justify-center mb-6 text-gray-300">
              <Microscope size={40} />
            </div>
            <h3 className="text-xl font-bold text-gray-900 mb-2">Awaiting Document</h3>
            <p className="text-gray-500 max-w-xs mx-auto">Upload an FIR or enter text to run extraction, IPC classification, and vector similarity search.</p>
          </div>
        )}

        {loading && (
          <div className="premium-card p-12 flex flex-col items-center justify-center text-center h-[500px]">
            <div className="w-16 h-16 border-4 border-surface-100 border-t-brand-600 rounded-full animate-spin mb-6"></div>
            <h3 className="text-lg font-bold text-gray-900 mb-2">Analyzing Document</h3>
            <p className="text-gray-500 mx-auto">Extracting entities and running semantic comparisons...</p>
          </div>
        )}

        {result && (
          <div className="space-y-6 animate-fade-in pb-10">
            {/* Summary + Risk */}
            <div className="premium-card p-8 border-l-4 border-l-brand-600">
              <div className="flex items-start justify-between gap-4 mb-4">
                <h3 className="text-xs font-bold text-gray-400 uppercase tracking-widest">Intelligence Summary</h3>
                <RiskBadge level={result.risk_level} />
              </div>
              <p className="text-base text-gray-800 leading-relaxed">{result.ai_summary}</p>
              {result.mo_pattern && (
                <div className="mt-5 inline-flex items-center gap-2 text-sm text-orange-700 bg-orange-50 px-4 py-2 rounded-xl font-medium border border-orange-100">
                  <Link2 size={16} /> Linked MO Pattern: <span className="font-bold">{result.mo_pattern}</span>
                </div>
              )}
            </div>

            {/* Entities */}
            <div className="premium-card p-8">
              <h3 className="text-xs font-bold text-gray-400 uppercase tracking-widest mb-6">Extracted Entities</h3>
              <div className="grid grid-cols-2 gap-4">
                {Object.entries(result.entities).filter(([, v]) => v && (Array.isArray(v) ? v.length : true)).map(([k, v]) => (
                  <div key={k} className="bg-surface-50 rounded-2xl p-4 border border-gray-100">
                    <p className="text-xs text-gray-500 font-semibold uppercase tracking-wider mb-1">{k.replace(/_/g, ' ')}</p>
                    <p className="text-sm font-medium text-gray-900">{Array.isArray(v) ? v.join(' • ') : v}</p>
                  </div>
                ))}
              </div>
            </div>

            {/* IPC Sections */}
            <div className="premium-card p-8">
              <h3 className="text-xs font-bold text-gray-400 uppercase tracking-widest mb-6 flex items-center gap-2">
                <Scale size={16} /> Suggested IPC Charges
              </h3>
              <div className="space-y-4">
                {result.ipc_sections.map((s, i) => (
                  <div key={i} className="border border-gray-100 rounded-2xl p-5 hover:border-brand-200 hover:shadow-sm transition-all bg-white">
                    <div className="flex flex-wrap items-start justify-between gap-3 mb-3">
                      <div className="flex items-center gap-3">
                        <span className="text-xs font-bold text-brand-700 bg-brand-50 px-3 py-1 rounded-lg">§ {s.section}</span>
                        <span className="text-base font-bold text-gray-900">{s.title}</span>
                      </div>
                      <span className={`text-xs px-3 py-1 font-bold rounded-lg uppercase ${s.bailable ? 'text-emerald-700 bg-emerald-50' : 'text-rose-700 bg-rose-50'}`}>
                        {s.bailable ? 'Bailable' : 'Non-Bailable'}
                      </span>
                    </div>
                    <p className="text-sm text-gray-600 mb-5 leading-relaxed">{s.description}</p>
                    <ConfidenceBar value={s.confidence} />
                    <div className="mt-4 pt-4 border-t border-gray-100 flex items-start gap-2 text-sm text-gray-500 font-medium">
                      <Scale size={16} className="flex-shrink-0 mt-0.5 text-brand-600" /> <span>{s.punishment}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Similar FIRs */}
            {result.similar_firs.length > 0 && (
              <div className="premium-card p-8">
                <h3 className="text-xs font-bold text-gray-400 uppercase tracking-widest mb-6 flex items-center gap-2">
                  <Search size={16} /> Vector Search Matches
                </h3>
                <div className="space-y-3">
                  {result.similar_firs.map((sf, i) => (
                    <div key={i} className="flex items-center gap-4 p-4 border border-gray-100 rounded-xl bg-surface-50 hover:bg-gray-50 transition-colors">
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-bold text-gray-900 mb-1">{sf.case_number}</p>
                        <p className="text-sm text-gray-500 truncate">{sf.snippet}</p>
                      </div>
                      <span className="text-xs font-bold text-brand-700 bg-white shadow-sm px-3 py-1.5 rounded-lg border border-gray-100 flex-shrink-0">
                        {(sf.similarity_score * 100).toFixed(0)}% Match
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Next Steps */}
            <div className="premium-card p-8 bg-brand-50 border-none">
              <h3 className="text-xs font-bold text-brand-800 uppercase tracking-widest mb-6 flex items-center gap-2">
                <ClipboardList size={16} /> Recommended Action Plan
              </h3>
              <ol className="space-y-4">
                {result.next_steps.map((step, i) => (
                  <li key={i} className="flex items-start gap-4 text-sm text-gray-800 font-medium">
                    <span className="w-6 h-6 rounded-full bg-white text-brand-800 shadow-sm flex items-center justify-center text-xs font-bold flex-shrink-0 mt-0.5">{i+1}</span>
                    <span className="leading-relaxed pt-0.5">{step}</span>
                  </li>
                ))}
              </ol>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
