import { createContext, useContext, useState, useEffect } from 'react'
import { authAPI } from '../api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [officer, setOfficer] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem('kpai_officer'))
    } catch { return null }
  })
  const [loading, setLoading] = useState(false)

  const login = async (badge_number, password) => {
    setLoading(true)
    try {
      const res = await authAPI.login(badge_number, password)
      const { access_token, officer: off } = res.data
      localStorage.setItem('kpai_token', access_token)
      localStorage.setItem('kpai_officer', JSON.stringify(off))
      setOfficer(off)
      return { success: true }
    } catch (err) {
      return { success: false, error: err.response?.data?.detail || 'Login failed' }
    } finally {
      setLoading(false)
    }
  }

  const logout = () => {
    localStorage.removeItem('kpai_token')
    localStorage.removeItem('kpai_officer')
    setOfficer(null)
  }

  return (
    <AuthContext.Provider value={{ officer, login, logout, loading }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)
