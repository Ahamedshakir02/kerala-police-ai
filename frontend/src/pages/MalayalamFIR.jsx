import { useState } from 'react'
import { bhashiniAPI } from '../api'
import toast from 'react-hot-toast'
import { Globe, Copy, Printer, CheckCircle2, Languages } from 'lucide-react'

export default function MalayalamFIR() {
  const [form, setForm] = useState({
    complainant: '', accused: '', date: '', time: '', location: '',
    offence: '', ipc: '', value: '', witness: '',
  })
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [copied, setCopied] = useState(false)

  const set = (k, v) => setForm(f => ({ ...f, [k]: v }))

  const loadSample = () => {
    setForm({
      complainant: 'Rajesh Kumar, Age 34, Pattom, Thiruvananthapuram',
      accused: 'Unknown (2 persons, arrived on black motorcycle)',
      date: '2024-03-15',
      time: '22:30',
      location: 'MG Road, Thiruvananthapuram, near Statue Junction',
      offence: 'Two unknown accused persons arrived on a motorcycle, one held complainant at knifepoint and threatened him while the other stole mobile phones worth Rs.3,50,000, cash of Rs.85,000 and a gold chain worth Rs.95,000. Both accused fled on the motorcycle towards Statue Road.',
      ipc: '379, 392, 506',
      value: '530000',
      witness: 'Mohan Lal (adjacent shop owner), Sreeraj K. (passerby)',
    })
    toast.success('Sample Data Loaded')
  }

  const buildEnglishText = () =>
    `FIRST INFORMATION REPORT\n\nComplainant: ${form.complainant}\nAccused: ${form.accused}\nDate of Incident: ${form.date} at ${form.time} hrs\nLocation: ${form.location}\nOffence Details: ${form.offence}\nApplicable IPC Sections: ${form.ipc}\nValue of Property Involved: Rs.${form.value}\nWitnesses: ${form.witness}`

  const handleTranslate = async () => {
    if (!form.offence.trim()) { toast.error('Please enter offence details'); return }
    setLoading(true)
    setResult(null)
    setCopied(false)
    try {
      const englishText = buildEnglishText()
      const res = await bhashiniAPI.translate(englishText, 'en', 'ml')
      setResult(res.data)
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Translation failed')
    } finally { setLoading(false) }
  }

  const copy = () => {
    if (result) { 
      navigator.clipboard.writeText(result.translated_text)
      setCopied(true)
      toast.success('Copied to clipboard')
      setTimeout(() => setCopied(false), 2000)
    }
  }

  const InputField = ({ label, field, type = 'text', placeholder, className = '' }) => (
    <div className={`space-y-1.5 ${className}`}>
      <label className="block text-xs font-bold text-gray-500 tracking-wide uppercase ml-1">{label}</label>
      <input
        type={type}
        value={form[field]}
        onChange={e => set(field, e.target.value)}
        placeholder={placeholder}
        className="premium-input bg-surface-50 border-transparent shadow-inner focus:bg-white"
      />
    </div>
  )

  return (
    <div className="grid grid-cols-1 xl:grid-cols-2 gap-8 max-w-7xl mx-auto animate-fade-in">
      
      {/* English Input Form */}
      <div className="premium-card p-8 space-y-8 flex flex-col">
        <div className="flex items-center justify-between pb-4 border-b border-gray-100">
          <div>
            <h2 className="text-xl font-bold text-gray-900 tracking-tight">FIR Metadata (EN)</h2>
            <p className="text-sm font-medium text-gray-500 flex items-center gap-2 mt-1">
              <Globe size={14} className="text-brand-600" /> Bhashini NLP Translation Engine
            </p>
          </div>
          <button onClick={loadSample} className="text-sm font-bold text-brand-600 bg-brand-50 hover:bg-brand-100 px-4 py-2 rounded-xl transition-colors">
            Inject Sample
          </button>
        </div>

        <div className="grid grid-cols-2 gap-5 flex-1 p-2">
          <InputField label="Complainant / Address" field="complainant" placeholder="Name, Age, Address..." className="col-span-2" />
          <InputField label="Accused Description" field="accused" placeholder="Name or visual traits..." className="col-span-2" />
          <InputField label="Date of Incident" field="date" type="date" />
          <InputField label="Time" field="time" type="time" />
          <InputField label="Location / Jurisdiction" field="location" placeholder="Sector, Street, District..." className="col-span-2" />
          
          <div className="col-span-2 space-y-1.5">
            <label className="block text-xs font-bold text-gray-500 tracking-wide uppercase ml-1">Incident Report (Statement)</label>
            <textarea
              value={form.offence}
              onChange={e => set('offence', e.target.value)}
              rows={5}
              placeholder="Enter the full English statement here..."
              className="premium-input bg-surface-50 border-transparent shadow-inner focus:bg-white resize-none h-32 leading-relaxed"
            />
          </div>

          <InputField label="IPC Charges" field="ipc" placeholder="e.g. 302, 420" />
          <InputField label="Property Value (INR)" field="value" type="number" placeholder="530000" />
          <InputField label="Witnesses" field="witness" placeholder="Names and addresses..." className="col-span-2" />
        </div>

        <button
          onClick={handleTranslate}
          disabled={loading}
          className="w-full premium-button py-4 text-base mt-4 shadow-float flex items-center justify-center gap-3"
        >
          {loading ? (
            <><span className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></span> Processing Translation...</>
          ) : <><Languages size={20} /> Compile Malayalam FIR</>}
        </button>
      </div>

      {/* Output Document */}
      <div className="premium-card p-0 flex flex-col bg-surface-50">
        <div className="flex items-center justify-between p-8 pb-6 border-b border-gray-200 bg-white">
          <div>
            <h2 className="text-xl font-bold text-gray-900 tracking-tight">Native Translation (ML)</h2>
            <p className="text-base text-gray-500 mt-1 font-malayalam font-medium">ഒന്നാം വിവര റിപ്പോർട്ട് (FIR)</p>
          </div>
          <div className="flex gap-3">
            {result && (
              <>
                <button 
                  onClick={copy} 
                  className={`flex items-center gap-2 text-sm font-bold px-4 py-2 rounded-xl transition-all shadow-sm ${copied ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' : 'bg-white text-gray-700 border border-gray-200 hover:bg-surface-50'}`}
                >
                  {copied ? <CheckCircle2 size={16} /> : <Copy size={16} />} 
                  {copied ? 'Copied' : 'Copy'}
                </button>
                <button 
                  onClick={() => window.print()} 
                  className="flex items-center gap-2 text-sm font-bold bg-white text-gray-700 border border-gray-200 px-4 py-2 rounded-xl hover:bg-surface-50 transition-all shadow-sm"
                >
                  <Printer size={16}/> Print
                </button>
              </>
            )}
          </div>
        </div>

        <div className="flex-1 overflow-y-auto scroll-y p-8">
          {!result && !loading && (
            <div className="h-full flex flex-col items-center justify-center text-center p-12">
              <div className="w-24 h-24 bg-white rounded-full shadow-sm flex items-center justify-center mb-6 text-brand-800/30">
                <Languages size={48} strokeWidth={1} />
              </div>
              <p className="text-2xl font-malayalam font-medium text-gray-900 mb-3" style={{ lineHeight: 1.8 }}>ഈ പേജിൽ ഡാറ്റ ദർശിക്കും</p>
              <p className="text-sm font-medium text-gray-500 max-w-xs mx-auto">Fill the English form metadata and compile to view the translated Malayalam document.</p>
            </div>
          )}

          {loading && (
            <div className="h-full flex flex-col items-center justify-center">
              <div className="w-16 h-16 border-4 border-white shadow-soft border-t-brand-600 rounded-full animate-spin mx-auto mb-6"></div>
              <p className="text-lg font-bold text-gray-900">Translation in Progress</p>
              <p className="text-sm font-medium text-gray-500 mt-1">Connecting to Bhashini Neural Engines...</p>
            </div>
          )}

          {result && (
            <div className="animate-fade-in h-full flex flex-col">
              <div className="mb-4 flex items-center justify-between">
                <span className="text-xs font-bold text-gray-400 uppercase tracking-widest bg-gray-100 px-3 py-1 rounded-lg">Language: ml-IN</span>
                <span className="text-xs font-bold text-brand-700 uppercase tracking-widest bg-brand-50 border border-brand-100 px-3 py-1 rounded-lg">
                  Model: {result.model_used}
                </span>
              </div>
              <div className="flex-1 bg-white p-10 rounded-2xl shadow-soft border border-gray-100 overflow-y-auto scroll-y">
                <div className="max-w-prose mx-auto">
                  <pre 
                    className="font-malayalam text-[17px] text-gray-800 whitespace-pre-wrap" 
                    style={{ fontFamily: '"Noto Sans Malayalam", sans-serif', lineHeight: 2.2 }}
                  >
                    {result.translated_text}
                  </pre>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
