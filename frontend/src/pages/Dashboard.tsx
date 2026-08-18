import { useEffect, useState } from 'react'
import { useAuth } from '@/components/AuthProvider'
import { Header } from '@/components/Header'
import { supabase, type Job } from '@/lib/supabase'
import { CreditCard, FileText, Clock, AlertCircle } from 'lucide-react'
import { toast } from 'sonner'

export function Dashboard() {
  const { profile, refreshProfile } = useAuth()
  const [jobs, setJobs] = useState<Job[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadJobs()
  }, [])

  const loadJobs = async () => {
    const { data, error } = await supabase
      .from('jobs')
      .select('*')
      .order('created_at', { ascending: false })
      .limit(10)

    if (error) {
      toast.error('Erro ao carregar histórico')
      console.error(error)
    } else {
      setJobs(data || [])
    }
    setLoading(false)
  }

  const availableCredits = profile
    ? Math.max(0, (profile.total_credits_mb || 0) - (profile.used_credits_mb || 0))
    : 0

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      <div className="max-w-6xl mx-auto p-6">
        <h1 className="text-3xl font-bold mb-6">Painel de Controle</h1>

      {/* Cards de Estatísticas */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        <div className="bg-white rounded-lg shadow p-6 border border-gray-200">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-sm font-medium text-gray-600">Créditos Disponíveis</h3>
            <CreditCard className="h-5 w-5 text-blue-500" />
          </div>
          <p className="text-3xl font-bold">{availableCredits} MB</p>
          <p className="text-sm text-gray-500 mt-1">
            {profile?.total_credits_mb || 0} MB comprados
          </p>
        </div>

        <div className="bg-white rounded-lg shadow p-6 border border-gray-200">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-sm font-medium text-gray-600">Arquivos Processados</h3>
            <FileText className="h-5 w-5 text-green-500" />
          </div>
          <p className="text-3xl font-bold">{jobs.filter(j => j.status === 'completed').length}</p>
          <p className="text-sm text-gray-500 mt-1">
            {jobs.length} total
          </p>
        </div>

        <div className="bg-white rounded-lg shadow p-6 border border-gray-200">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-sm font-medium text-gray-600">Usos Gratuitos Hoje</h3>
            <Clock className="h-5 w-5 text-orange-500" />
          </div>
          <p className="text-3xl font-bold">{profile?.free_uses_today || 0}/3</p>
          <p className="text-sm text-gray-500 mt-1">
            Renova à meia-noite
          </p>
        </div>
      </div>

      {/* Botão Adicionar Créditos */}
      {availableCredits < 10 && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-6 flex items-start gap-3">
          <AlertCircle className="h-5 w-5 text-yellow-600 flex-shrink-0 mt-0.5" />
          <div className="flex-1">
            <h3 className="font-medium text-yellow-900">Créditos baixos</h3>
            <p className="text-sm text-yellow-700 mt-1">
              Você tem apenas {availableCredits} MB disponíveis. Adicione mais créditos para continuar processando arquivos grandes.
            </p>
            <button
              onClick={() => window.location.href = '/pricing'}
              className="mt-3 bg-yellow-600 text-white px-4 py-2 rounded-lg hover:bg-yellow-700 transition text-sm font-medium"
            >
              Adicionar Créditos
            </button>
          </div>
        </div>
      )}

      {/* Histórico */}
      <div className="bg-white rounded-lg shadow border border-gray-200">
        <div className="p-6 border-b border-gray-200">
          <h2 className="text-xl font-semibold">Histórico de Processamentos</h2>
        </div>
        <div className="divide-y divide-gray-200">
          {loading ? (
            <div className="p-8 text-center text-gray-500">Carregando...</div>
          ) : jobs.length === 0 ? (
            <div className="p-8 text-center text-gray-500">
              Nenhum arquivo processado ainda.
              <br />
              <a href="/upload" className="text-blue-600 hover:underline mt-2 inline-block">
                Enviar seu primeiro PDF
              </a>
            </div>
          ) : (
            jobs.map((job) => (
              <div key={job.id} className="p-4 hover:bg-gray-50 transition">
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <h3 className="font-medium text-gray-900">{job.filename}</h3>
                    <div className="flex items-center gap-4 mt-1 text-sm text-gray-500">
                      <span>{job.file_size_mb.toFixed(2)} MB</span>
                      {job.pages_count && <span>{job.pages_count} páginas</span>}
                      {job.documents_count && <span>{job.documents_count} docs</span>}
                      <span>{new Date(job.created_at).toLocaleDateString('pt-BR')}</span>
                    </div>
                  </div>
                  <div className="ml-4">
                    <span className={`
                      px-3 py-1 rounded-full text-xs font-medium
                      ${job.status === 'completed' ? 'bg-green-100 text-green-800' : ''}
                      ${job.status === 'processing' ? 'bg-blue-100 text-blue-800' : ''}
                      ${job.status === 'failed' ? 'bg-red-100 text-red-800' : ''}
                    `}>
                      {job.status === 'completed' && 'Concluído'}
                      {job.status === 'processing' && 'Processando'}
                      {job.status === 'failed' && 'Falhou'}
                    </span>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
      </div>
    </div>
  )
}
