import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { ArrowLeft, ScrollText } from 'lucide-react'
import { toast } from 'sonner'
import { Header } from '@/components/Header'
import { SiteFooter } from '@/components/SiteFooter'
import { useAuth } from '@/components/AuthProvider'
import { APP_VERSION } from '@/lib/version'

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000'

type JobLog = {
  id: string
  user_email?: string
  filename: string
  file_size_mb: number
  pages_count: number | null
  documents_count: number | null
  status: string
  error_message: string | null
  created_at: string
  ip_address: string | null
  processing_time_seconds: number | null
}

type GrantLog = {
  id: string
  user_email: string
  granted_by_email: string
  credits_mb: number
  amount_brl: number
  note: string | null
  created_at: string
}

type IpLog = {
  ip: string
  free_process_count: number
  tool_use_count: number
  last_email: string | null
  updated_at: string
}

export function AdminLogs() {
  const { user, loading: authLoading, getAccessToken } = useAuth()
  const [checking, setChecking] = useState(true)
  const [allowed, setAllowed] = useState(false)
  const [version, setVersion] = useState(APP_VERSION)
  const [jobs, setJobs] = useState<JobLog[]>([])
  const [failed, setFailed] = useState<JobLog[]>([])
  const [grants, setGrants] = useState<GrantLog[]>([])
  const [ipUsage, setIpUsage] = useState<IpLog[]>([])

  useEffect(() => {
    if (authLoading) return
    if (!user) {
      window.location.href = '/login?next=' + encodeURIComponent('/admin/logs')
      return
    }
    ;(async () => {
      try {
        const token = await getAccessToken()
        if (!token) throw new Error('Sessão expirada')
        const headers = { Authorization: `Bearer ${token}` }
        const me = await fetch(`${BACKEND_URL}/api/admin/me`, { headers })
        if (!me.ok) {
          setAllowed(false)
          return
        }
        const meData = await me.json()
        if (meData.version) setVersion(meData.version)
        setAllowed(true)
        const r = await fetch(`${BACKEND_URL}/api/admin/logs?limit=50`, { headers })
        if (!r.ok) throw new Error('Falha ao carregar logs')
        const data = await r.json()
        setJobs(data.jobs || [])
        setFailed(data.failed_jobs || [])
        setGrants(data.grants || [])
        setIpUsage(data.ip_usage || [])
        if (data.version) setVersion(data.version)
      } catch (error) {
        toast.error(error instanceof Error ? error.message : 'Erro ao carregar logs')
        setAllowed(false)
      } finally {
        setChecking(false)
      }
    })()
  }, [user, authLoading])

  if (checking || authLoading) {
    return (
      <div className="min-h-screen bg-white">
        <Header />
        <p className="p-10 text-center text-[#727272]">Carregando logs...</p>
      </div>
    )
  }

  if (!allowed) {
    return (
      <div className="min-h-screen bg-white">
        <Header />
        <div className="mx-auto max-w-lg px-6 py-20 text-center">
          <h1 className="text-2xl font-semibold">Acesso negado</h1>
          <Link to="/dashboard" className="mt-6 inline-block rounded-full bg-[#0c0c0c] px-5 py-2.5 text-sm font-semibold text-white">
            Voltar
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-white text-[#0c0c0c]">
      <Header />
      <section className="relative overflow-hidden px-6 pb-6 pt-12">
        <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_top_right,rgba(183,255,51,0.18),transparent_42%)]" />
        <div className="relative mx-auto max-w-6xl">
          <Link to="/admin" className="inline-flex items-center gap-1 text-sm text-[#727272] hover:text-[#0c0c0c]">
            <ArrowLeft className="h-4 w-4" />
            Voltar ao admin
          </Link>
          <div className="mt-3 flex flex-wrap items-end justify-between gap-3">
            <div>
              <p className="text-sm font-medium text-[#727272]">Operação</p>
              <h1 className="mt-1 flex items-center gap-2 text-3xl font-semibold tracking-tight">
                <ScrollText className="h-7 w-7" />
                Logs do sistema
              </h1>
            </div>
            <p className="rounded-full border border-black/10 bg-[#f7f8fa] px-3 py-1 text-sm">
              DocSplit v{version}
            </p>
          </div>
        </div>
      </section>

      <div className="mx-auto grid max-w-6xl gap-6 px-6 pb-16">
        <section className="rounded-2xl border border-black/8 bg-white p-6">
          <h2 className="text-lg font-semibold">Falhas recentes</h2>
          <div className="mt-4 divide-y divide-black/8">
            {failed.map((job) => (
              <div key={job.id} className="py-3 text-sm">
                <p className="font-medium">{job.filename}</p>
                <p className="text-[#727272]">
                  {job.user_email || '—'} · {job.ip_address || 'sem IP'} ·{' '}
                  {new Date(job.created_at).toLocaleString('pt-BR')}
                </p>
                <p className="mt-1 text-[#0c0c0c]">{job.error_message || 'Erro sem detalhes'}</p>
              </div>
            ))}
            {failed.length === 0 && <p className="py-6 text-center text-[#727272]">Nenhuma falha recente.</p>}
          </div>
        </section>

        <section className="rounded-2xl border border-black/8 bg-white p-6">
          <h2 className="text-lg font-semibold">Processamentos</h2>
          <div className="mt-4 overflow-x-auto">
            <table className="w-full min-w-[720px] text-left text-sm">
              <thead className="text-[#727272]">
                <tr>
                  <th className="pb-2 font-medium">Arquivo</th>
                  <th className="pb-2 font-medium">Usuário</th>
                  <th className="pb-2 font-medium">Status</th>
                  <th className="pb-2 font-medium">IP</th>
                  <th className="pb-2 font-medium">Quando</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-black/8">
                {jobs.map((job) => (
                  <tr key={job.id}>
                    <td className="py-3">
                      <p className="font-medium">{job.filename}</p>
                      <p className="text-[#9b9b9b]">
                        {Number(job.file_size_mb || 0).toFixed(2)} MB
                        {job.pages_count ? ` · ${job.pages_count} pág.` : ''}
                      </p>
                    </td>
                    <td className="py-3">{job.user_email || '—'}</td>
                    <td className="py-3">
                      <span
                        className={`rounded-full px-2.5 py-0.5 text-xs font-semibold ${
                          job.status === 'completed'
                            ? 'bg-[#b7ff33] text-[#0c0c0c]'
                            : job.status === 'failed'
                              ? 'bg-[#0c0c0c] text-white'
                              : 'bg-[#f4f5f7] text-[#0c0c0c]'
                        }`}
                      >
                        {job.status}
                      </span>
                    </td>
                    <td className="py-3">{job.ip_address || '—'}</td>
                    <td className="py-3">{new Date(job.created_at).toLocaleString('pt-BR')}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            {jobs.length === 0 && <p className="py-6 text-center text-[#727272]">Nenhum job ainda.</p>}
          </div>
        </section>

        <section className="grid gap-6 lg:grid-cols-2">
          <div className="rounded-2xl border border-black/8 bg-white p-6">
            <h2 className="text-lg font-semibold">Créditos faturados</h2>
            <div className="mt-4 divide-y divide-black/8">
              {grants.map((g) => (
                <div key={g.id} className="py-3 text-sm">
                  <p className="font-medium">{g.user_email}</p>
                  <p className="text-[#727272]">
                    {g.credits_mb} MB · R$ {Number(g.amount_brl).toFixed(2)}
                    {g.note ? ` · ${g.note}` : ''}
                  </p>
                  <p className="text-[#9b9b9b]">
                    {new Date(g.created_at).toLocaleString('pt-BR')} · por {g.granted_by_email || 'admin'}
                  </p>
                </div>
              ))}
              {grants.length === 0 && <p className="py-6 text-center text-[#727272]">Sem liberações.</p>}
            </div>
          </div>

          <div className="rounded-2xl border border-black/8 bg-white p-6">
            <h2 className="text-lg font-semibold">Uso por IP (hoje)</h2>
            <div className="mt-4 divide-y divide-black/8">
              {ipUsage.map((item) => (
                <div key={item.ip} className="py-3 text-sm">
                  <p className="font-medium">{item.ip}</p>
                  <p className="text-[#727272]">
                    Free {item.free_process_count}/1 · Ferramentas {item.tool_use_count}/2
                    {item.last_email ? ` · ${item.last_email}` : ''}
                  </p>
                </div>
              ))}
              {ipUsage.length === 0 && <p className="py-6 text-center text-[#727272]">Sem uso por IP hoje.</p>}
            </div>
          </div>
        </section>
      </div>
      <SiteFooter />
    </div>
  )
}
