import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './components/AuthContext'
import Layout from './components/Layout'
import Login from './pages/Login'
import RequestAccess from './pages/RequestAccess'
import Dashboard from './pages/Dashboard'
import FIRAnalysis from './pages/FIRAnalysis'
import CaseIntelligence from './pages/CaseIntelligence'
import MOPatterns from './pages/MOPatterns'
import LegalAssistant from './pages/LegalAssistant'
import MalayalamFIR from './pages/MalayalamFIR'

function PrivateRoute({ children }) {
  const { officer } = useAuth()
  return officer ? children : <Navigate to="/login" replace />
}

function AppRoutes() {
  const { officer } = useAuth()
  if (location.pathname === '/login' && officer) {
    return <Navigate to="/" replace />
  }
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/request-access" element={<RequestAccess />} />
      <Route path="/" element={<PrivateRoute><Layout><Dashboard /></Layout></PrivateRoute>} />
      <Route path="/fir" element={<PrivateRoute><Layout><FIRAnalysis /></Layout></PrivateRoute>} />
      <Route path="/cases" element={<PrivateRoute><Layout><CaseIntelligence /></Layout></PrivateRoute>} />
      <Route path="/patterns" element={<PrivateRoute><Layout><MOPatterns /></Layout></PrivateRoute>} />
      <Route path="/legal" element={<PrivateRoute><Layout><LegalAssistant /></Layout></PrivateRoute>} />
      <Route path="/malayalam" element={<PrivateRoute><Layout><MalayalamFIR /></Layout></PrivateRoute>} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </BrowserRouter>
  )
}
