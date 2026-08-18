import { createClient } from '@supabase/supabase-js'

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL || 'https://placeholder.supabase.co'
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY || 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBsYWNlaG9sZGVyIiwicm9sZSI6ImFub24iLCJpYXQiOjE2NDUxOTIwMDAsImV4cCI6MTk2MDU1MjAwMH0.placeholder'

const isConfigured = import.meta.env.VITE_SUPABASE_URL && import.meta.env.VITE_SUPABASE_ANON_KEY

if (!isConfigured) {
  console.warn('⚠️ Supabase não configurado. Funcionando em modo demonstração.')
}

export const supabase = createClient(supabaseUrl, supabaseAnonKey)
export const SUPABASE_ENABLED = isConfigured

// Tipos do banco
export type User = {
  id: string
  email: string
  created_at: string
  total_credits_mb: number
  used_credits_mb: number
  last_free_use: string | null
  free_uses_today: number
  display_name: string | null
  avatar_url: string | null
}

export type Transaction = {
  id: string
  user_id: string
  amount_brl: number
  credits_mb: number
  payment_method: string
  payment_id: string
  payment_status: 'pending' | 'approved' | 'rejected' | 'cancelled'
  created_at: string
  expires_at: string | null
  approved_at: string | null
}

export type Job = {
  id: string
  user_id: string | null
  filename: string
  file_size_mb: number
  pages_count: number | null
  documents_count: number | null
  status: 'processing' | 'completed' | 'failed'
  error_message: string | null
  processing_time_seconds: number | null
  used_ocr: boolean
  created_at: string
  completed_at: string | null
}
