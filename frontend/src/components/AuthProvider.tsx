import { createContext, useContext, useEffect, useState, ReactNode } from 'react'
import { supabase, SUPABASE_ENABLED, type User } from '@/lib/supabase'
import { User as SupabaseUser } from '@supabase/supabase-js'

type AuthContextType = {
  user: SupabaseUser | null
  profile: User | null
  loading: boolean
  signIn: (email: string, password: string) => Promise<void>
  signUp: (email: string, password: string) => Promise<void>
  signOut: () => Promise<void>
  signInWithGoogle: (redirectTo?: string) => Promise<void>
  refreshProfile: () => Promise<void>
  getAccessToken: () => Promise<string | null>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<SupabaseUser | null>(null)
  const [profile, setProfile] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!SUPABASE_ENABLED) {
      setLoading(false)
      return
    }

    // Verificar sessão inicial
    supabase.auth.getSession().then(({ data: { session } }) => {
      setUser(session?.user ?? null)
      if (session?.user) {
        fetchProfile(session.user.id)
      }
      setLoading(false)
    }).catch((error) => {
      console.error('Erro ao verificar sessão:', error)
      setLoading(false)
    })

    // Escutar mudanças de auth
    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      setUser(session?.user ?? null)
      if (session?.user) {
        fetchProfile(session.user.id)
      } else {
        setProfile(null)
      }
    })

    return () => subscription.unsubscribe()
  }, [])

  const fetchProfile = async (userId: string) => {
    const { data, error } = await supabase
      .from('users')
      .select('*')
      .eq('id', userId)
      .single()

    if (error) {
      console.error('Erro ao buscar perfil:', error)
      return
    }

    setProfile(data)
  }

  const refreshProfile = async () => {
    if (user) {
      await fetchProfile(user.id)
    }
  }

  const getAccessToken = async () => {
    if (!SUPABASE_ENABLED) return null
    const { data } = await supabase.auth.getSession()
    if (data.session?.access_token) {
      return data.session.access_token
    }
    const refreshed = await supabase.auth.refreshSession()
    return refreshed.data.session?.access_token ?? null
  }

  const signIn = async (email: string, password: string) => {
    if (!SUPABASE_ENABLED) {
      throw new Error('Autenticação não disponível. Configure as variáveis de ambiente.')
    }
    const { error } = await supabase.auth.signInWithPassword({ email, password })
    if (error) throw error
  }

  const signUp = async (email: string, password: string) => {
    if (!SUPABASE_ENABLED) {
      throw new Error('Cadastro não disponível. Configure as variáveis de ambiente.')
    }
    const { error } = await supabase.auth.signUp({ email, password })
    if (error) throw error
  }

  const signOut = async () => {
    if (!SUPABASE_ENABLED) return
    const { error } = await supabase.auth.signOut()
    if (error) throw error
  }

  const signInWithGoogle = async (redirectTo?: string) => {
    if (!SUPABASE_ENABLED) {
      throw new Error('Login com Google não disponível. Configure as variáveis de ambiente.')
    }
    // Sempre volta para /login (React) para o AuthProvider gravar a sessão.
    const callback =
      redirectTo ||
      `${window.location.origin}/login?next=${encodeURIComponent('/dashboard')}`
    const { error } = await supabase.auth.signInWithOAuth({
      provider: 'google',
      options: {
        redirectTo: callback,
      },
    })
    if (error) throw error
  }

  return (
    <AuthContext.Provider value={{
      user,
      profile,
      loading,
      signIn,
      signUp,
      signOut,
      signInWithGoogle,
      refreshProfile,
      getAccessToken,
    }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth deve ser usado dentro de AuthProvider')
  }
  return context
}
