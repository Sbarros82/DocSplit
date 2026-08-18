import { createClient } from '@supabase/supabase-js'

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL || ''
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY || ''

if (!supabaseUrl || !supabaseAnonKey) {
  console.warn('⚠️ Supabase não configurado. Auth desabilitado.')
}

export const supabase = createClient(supabaseUrl, supabaseAnonKey)

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
