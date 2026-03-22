import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import './styles/index.css'
import { Toaster } from 'react-hot-toast'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
    <Toaster
      position="top-right"
      toastOptions={{
        style: {
          background: '#0d1f3c',
          color: '#e2e8f0',
          border: '1px solid rgba(24,53,104,0.8)',
          borderRadius: '10px',
          fontSize: '14px',
        },
        success: { iconTheme: { primary: '#22c55e', secondary: '#0d1f3c' } },
        error:   { iconTheme: { primary: '#ef4444', secondary: '#0d1f3c' } },
      }}
    />
  </React.StrictMode>,
)
