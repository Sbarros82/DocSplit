import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { AuthProvider } from './components/AuthProvider'
import { Toaster } from 'sonner'
import { Landing } from './pages/Landing'
import { Pricing } from './pages/Pricing'
import { Dashboard } from './pages/Dashboard'
import { Login } from './pages/Login'
import { Upload } from './pages/Upload'
import { PaymentResult } from './pages/PaymentResult'
import './index.css'

const queryClient = new QueryClient()

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<Landing />} />
            <Route path="/login" element={<Login />} />
            <Route path="/upload" element={<Upload />} />
            <Route path="/pricing" element={<Pricing />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/payment/success" element={<PaymentResult type="success" />} />
            <Route path="/payment/failure" element={<PaymentResult type="failure" />} />
            <Route path="/payment/pending" element={<PaymentResult type="pending" />} />
          </Routes>
          <Toaster position="top-right" />
        </BrowserRouter>
      </AuthProvider>
    </QueryClientProvider>
  </React.StrictMode>
)
