import { useState, useRef, useEffect } from 'react'
import { legalAPI } from '../api'
import toast from 'react-hot-toast'
import { BookOpen, Sparkles, Send, Scale, FileText, ChevronRight, AlertTriangle, Bot, Zap } from 'lucide-react'

const QUICK_QUERIES = [
  { label: 'Bail — Sec 167 CrPC', q: 'What are the bail provisions under Section 167 CrPC? When does default bail apply?' },
  { label: 'FIR Registration Mandatory', q: 'Is it mandatory to register FIR for every cognizable offence? What does Lalita Kumari say?' },
  { label: 'Cybercrime — IPC & IT Act', q: 'What are the IPC and IT Act sections for online fraud, OTP fraud, and phishing?' },
  { label: 'Motor Accident Death', q: 'What sections apply when someone dies in a road accident due to rash driving?' },
  { label: 'Drunk Driving — MVA', q: 'What is the punishment for drunk driving under the Motor Vehicles Act?' },
  { label: 'BNS vs IPC — New Laws', q: 'What is the Bharatiya Nyaya Sanhita? How does it replace IPC? What changed?' },
  { label: 'POCSO — Child Abuse', q: 'What are POCSO Act sections for sexual assault on children? What is the reporting obligation?' },
  { label: 'Dowry & 498A Guidelines', q: 'What are the arrest guidelines for Section 498A IPC dowry cases? Arnesh Kumar judgment?' },
  { label: 'Arrest Protocol — D.K. Basu', q: 'What are the arrest guidelines from D.K. Basu case? What are rights of arrested person?' },
  { label: 'NDPS Act — Narcotics', q: 'What are NDPS Act sections for cannabis and psychotropic substances? What are the penalties?' },
]

function SourceBadge({ source, isFallback }) {
  if (isFallback) {
    return (
      <span className="inline-flex items-center gap-1.5 text-xs font-bold px-3 py-1 rounded-lg bg-amber-50 text-amber-700 border border-amber-200">
        <Zap size={12} /> Keyword Search
      </span>
    )
  }
  return (
    <span className="inline-flex items-center gap-1.5 text-xs font-bold px-3 py-1 rounded-lg bg-emerald-50 text-emerald-700 border border-emerald-200">
      <Bot size={12} /> Gemini AI
    </span>
  )
}

function FallbackWarning() {
  return (
    <div className="flex items-start gap-3 px-5 py-3.5 bg-amber-50 border border-amber-200 rounded-2xl text-sm text-amber-800 animate-fade-in mb-4">
      <AlertTriangle size={18} className="flex-shrink-0 mt-0.5 text-amber-600" />
      <div>
        <p className="font-bold">AI model unavailable — showing keyword search results</p>
        <p className="text-amber-600 text-xs mt-0.5">Set <code className="bg-amber-100 px-1 rounded">GEMINI_API_KEY</code> in backend .env for AI-powered responses</p>
      </div>
    </div>
  )
}

function MessageBubble({ msg }) {
  const isUser = msg.role === 'user'
  return (
    <div className={`flex gap-4 animate-fade-in mb-8 ${isUser ? 'flex-row-reverse' : ''}`}>
      <div className={`w-10 h-10 rounded-2xl flex items-center justify-center font-bold flex-shrink-0 shadow-sm ${
        isUser ? 'bg-brand-800 text-white' : 'bg-white border border-gray-100 text-brand-800'
      }`}>
        {isUser ? 'SI' : <Scale size={20} />}
      </div>
      
      <div className={`max-w-2xl ${isUser ? 'text-right' : ''}`}>
        {/* Fallback warning — only for assistant messages */}
        {!isUser && msg.is_fallback && <FallbackWarning />}
        
        <div className={`px-6 py-4 rounded-3xl text-[15px] leading-relaxed relative ${
          isUser
            ? 'bg-brand-800 text-white rounded-tr-sm shadow-sm'
            : 'bg-white text-gray-800 border border-gray-100 shadow-soft rounded-tl-sm'
        }`}>
          {msg.content.split('\n').map((line, i) => {
            if (line.startsWith('**') && line.endsWith('**')) {
              return <p key={i} className={`font-bold mt-4 mb-2 pb-2 border-b ${isUser ? 'text-white border-white/20' : 'text-gray-900 border-gray-100'}`}>{line.slice(2, -2)}</p>
            }
            if (line.startsWith('• ') || line.startsWith('- ')) {
              return <div key={i} className="flex gap-3 my-2">
                <span className={isUser ? 'text-brand-200' : 'text-brand-500'}>•</span>
                <p className={isUser ? 'text-brand-50' : 'text-gray-700'}>{line.slice(2)}</p>
              </div>
            }
            return <p key={i} className={line === '' ? 'h-4' : 'mb-3 last:mb-0'}>{line}</p>
          })}
        </div>
        
        {/* Source badge + sections */}
        <div className={`mt-3 flex flex-wrap items-center gap-2 ${isUser ? 'justify-end' : 'justify-start'}`}>
          {!isUser && msg.source && <SourceBadge source={msg.source} isFallback={msg.is_fallback} />}
          {msg.sections?.length > 0 && msg.sections.slice(0, 4).map((s, i) => (
            <span key={i} className="text-xs font-bold px-3 py-1.5 rounded-lg border border-brand-100 bg-brand-50 text-brand-800 flex items-center gap-1.5 shadow-sm">
              <Scale size={12} /> § {s.section}
            </span>
          ))}
        </div>
        
        {msg.citations?.length > 0 && (
          <div className={`mt-3 text-xs font-medium flex items-center gap-2 ${isUser ? 'justify-end text-brand-200' : 'justify-start text-gray-400'}`}>
            <FileText size={14} /> Ref: {msg.citations[0]}
          </div>
        )}
      </div>
    </div>
  )
}

export default function LegalAssistant() {
  const [messages, setMessages] = useState([{
    role: 'assistant',
    content: `Hello. I am the AI Legal Assistant for Kerala Police.\n\nI have access to the latest IPC Sections, CrPC provisions, Supreme Court precedents, BNS/BNSS updates, and POCSO guidelines.\n\nHow can I assist you with your investigation today?`,
    sections: [],
    citations: [],
    source: null,
    is_fallback: false,
  }])
  const [query, setQuery] = useState('')
  const [loading, setLoading] = useState(false)
  const messagesEnd = useRef(null)

  useEffect(() => { messagesEnd.current?.scrollIntoView({ behavior: 'smooth' }) }, [messages])

  const clearChat = () => {
    setMessages([{
      role: 'assistant',
      content: `Chat cleared. How can I help you?`,
      sections: [],
      citations: [],
      source: null,
      is_fallback: false,
    }])
  }

  const sendQuery = async (q) => {
    const text = q || query.trim()
    if (!text) return
    setQuery('')
    setMessages(prev => [...prev, { role: 'user', content: text }])
    setLoading(true)
    try {
      const res = await legalAPI.chat(text)
      const data = res.data
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: data.answer,
        sections: data.sections,
        citations: data.citations,
        confidence: data.confidence,
        is_fallback: data.is_fallback,
        source: data.source,
      }])
    } catch {
      toast.error('Legal search failed')
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Connection timeout. Unable to reach the legal knowledge base.',
        sections: [],
        citations: [],
        is_fallback: true,
        source: 'error',
      }])
    } finally { setLoading(false) }
  }

  return (
    <div className="flex gap-8 h-full animate-fade-in max-w-[1400px] mx-auto" style={{ minHeight: 'calc(100vh - 120px)' }}>
      
      {/* Sidebar Knowledge Library */}
      <div className="w-[340px] flex-shrink-0 flex flex-col gap-6 h-full">
        {/* Quick actions */}
        <div className="premium-card p-6 bg-white overflow-hidden">
          <h3 className="text-xs font-bold text-gray-400 uppercase tracking-widest mb-4 flex items-center gap-2">
            <Sparkles size={16} className="text-brand-500" /> Suggested Queries
          </h3>
          <div className="space-y-2">
            {QUICK_QUERIES.map((q, i) => (
              <button
                key={i}
                onClick={() => sendQuery(q.q)}
                className="w-full text-left font-medium text-sm text-gray-700 p-4 rounded-xl border border-gray-100 hover:border-brand-200 hover:bg-surface-50 hover:text-brand-800 transition-all group flex items-center justify-between shadow-sm"
              >
                {q.label}
                <ChevronRight size={16} className="text-gray-300 group-hover:text-brand-500 transition-colors" />
              </button>
            ))}
          </div>
        </div>

        {/* DB Info */}
        <div className="premium-card p-6 bg-surface-50 border-none">
          <p className="text-sm font-bold text-gray-900 mb-4 flex items-center gap-2">
            <BookOpen size={18} className="text-brand-800" /> Active Knowledge Nodes
          </p>
          <div className="space-y-3 text-sm font-medium text-gray-500">
            <div className="flex items-center justify-between">
              <span className="flex items-center gap-2"><div className="w-1.5 h-1.5 rounded-full bg-brand-500" /> IPC & BNS Codes</span>
              <span className="bg-white border border-gray-100 px-2 py-0.5 rounded-md text-xs font-bold">Updated</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="flex items-center gap-2"><div className="w-1.5 h-1.5 rounded-full bg-brand-500" /> CrPC Procedures</span>
              <span className="bg-white border border-gray-100 px-2 py-0.5 rounded-md text-xs font-bold">Updated</span>
            </div>
            <div className="flex items-center gap-2"><div className="w-1.5 h-1.5 rounded-full bg-brand-500" /> SC Precedent Library</div>
            <div className="flex items-center gap-2"><div className="w-1.5 h-1.5 rounded-full bg-brand-500" /> POCSO & DV Act</div>
            <div className="flex items-center gap-2"><div className="w-1.5 h-1.5 rounded-full bg-brand-500" /> Motor Vehicles Act</div>
          </div>
        </div>
      </div>

      {/* Main Chat Interface */}
      <div className="flex-1 flex flex-col premium-card overflow-hidden bg-surface-50/50">
        
        {/* Chat Header */}
        <div className="px-8 py-5 border-b border-gray-100 bg-white flex items-center justify-between z-10">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 bg-surface-100 rounded-full flex items-center justify-center text-brand-800 border border-gray-200">
              <Scale size={20} strokeWidth={2.5} />
            </div>
            <div>
              <p className="text-lg font-bold text-gray-900 tracking-tight">Legal Intelligence</p>
              <p className="text-xs font-medium text-brand-700 flex items-center gap-1.5 mt-0.5">
                <span className="w-1.5 h-1.5 bg-brand-500 rounded-full animate-pulse"></span>
                Gemini AI + Knowledge Base Active
              </p>
            </div>
          </div>
          <button 
            onClick={clearChat}
            className="text-sm font-bold text-gray-500 bg-surface-50 px-4 py-2 rounded-xl hover:bg-gray-100 transition-colors border border-transparent hover:border-gray-200"
          >
            Clear Chat
          </button>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto scroll-y p-8">
          {messages.map((msg, i) => <MessageBubble key={i} msg={msg} />)}
          
          {loading && (
            <div className="flex gap-4 animate-fade-in mt-6">
              <div className="w-10 h-10 rounded-2xl bg-white border border-gray-100 text-brand-800 flex items-center justify-center shadow-sm">
                <Scale size={20} />
              </div>
              <div className="bg-white border border-gray-100 shadow-soft px-6 py-5 rounded-3xl rounded-tl-sm flex items-center gap-2.5">
                <span className="w-2.5 h-2.5 bg-brand-300 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></span>
                <span className="w-2.5 h-2.5 bg-brand-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></span>
                <span className="w-2.5 h-2.5 bg-brand-800 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></span>
              </div>
            </div>
          )}
          <div ref={messagesEnd} className="h-4" />
        </div>

        {/* Input Bar */}
        <div className="p-6 bg-white border-t border-gray-100 z-10">
          <div className="max-w-4xl mx-auto relative flex items-end gap-3 transition-opacity">
            <textarea
              value={query}
              onChange={e => setQuery(e.target.value)}
              onKeyDown={e => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault()
                  sendQuery()
                }
              }}
              placeholder="Ask a legal question or cite a scenario..."
              className="flex-1 bg-surface-50 border border-gray-200 rounded-2xl px-6 py-4 text-[15px] text-gray-800 placeholder-gray-400 focus:outline-none focus:ring-4 focus:ring-brand-800/10 focus:border-brand-800/30 transition-all resize-none shadow-inner"
              rows={1}
              style={{ minHeight: '60px', maxHeight: '120px' }}
            />
            <button
              onClick={() => sendQuery()}
              disabled={loading || !query.trim()}
              className="h-[60px] w-[60px] bg-brand-800 hover:bg-brand-900 text-white rounded-2xl flex items-center justify-center transition-all disabled:opacity-50 disabled:hover:bg-brand-800 shadow-sm flex-shrink-0"
            >
              <Send size={22} className={query.trim() ? "translate-x-[2px] -translate-y-[2px]" : ""} />
            </button>
          </div>
          <p className="text-center text-[11px] font-medium text-gray-400 mt-4">
            Powered by Google Gemini AI with RAG • Verify legal citations with official manuals before taking action.
          </p>
        </div>

      </div>
    </div>
  )
}
