import axios from 'axios'

const API_BASE = '/api'

const api = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
})

// Attach JWT to every request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('kpai_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// Handle 401 globally — redirect to login
api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401 && !err.config.url.includes('/auth/login')) {
      localStorage.removeItem('kpai_token')
      localStorage.removeItem('kpai_officer')
      window.location.href = '/login'
    }
    return Promise.reject(err)
  },
)

// ── Auth ──────────────────────────────────────────────────────────
export const authAPI = {
  login: (badge_number, password) =>
    api.post('/auth/login', { badge_number, password }),
  me: () => api.get('/auth/me'),
  seedDemo: () => api.post('/auth/seed-demo'),
}

// ── FIRs ──────────────────────────────────────────────────────────
export const firsAPI = {
  list: (params) => api.get('/firs', { params }),
  get: (id) => api.get(`/firs/${id}`),
  upload: (formData) =>
    api.post('/firs/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),
  train: (id) => api.post(`/firs/${id}/train`),
}

// ── Analysis ──────────────────────────────────────────────────────
export const analysisAPI = {
  analyzeFIR: (text, language = 'en') =>
    api.post('/analysis/analyze-fir', { text, language }),
  getSimilar: (firId, k = 5) =>
    api.get(`/analysis/similar/${firId}`, { params: { k } }),
}

// ── Legal ─────────────────────────────────────────────────────────
export const legalAPI = {
  search: (query, category) =>
    api.post('/legal/search', { query, category }),
  chat: (query) =>
    api.post('/legal/chat', { query }),
}

// ── Patterns ──────────────────────────────────────────────────────
export const patternsAPI = {
  getMOAlerts: () => api.get('/patterns/mo-alerts'),
}

// ── Dashboard ─────────────────────────────────────────────────────
export const dashboardAPI = {
  getStats: () => api.get('/dashboard/stats'),
  getChromaStats: () => api.get('/dashboard/chroma-stats'),
}

// ── Bhashini ──────────────────────────────────────────────────────
export const bhashiniAPI = {
  translate: (text, source_language = 'en', target_language = 'ml') =>
    api.post('/bhashini/translate', { text, source_language, target_language }),
}

export default api
