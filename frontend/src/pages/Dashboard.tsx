import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { motion, useReducedMotion } from 'motion/react'
import { AlertCircle, ArrowRight, Clock, CreditCard, FileText } from 'lucide-react'
import { toast } from 'sonner'
import { useAuth } from '@/components/AuthProvider'
import { Header } from '@/components/Header'
import { SiteFooter } from '@/components/SiteFooter'
import { supabase, type Job } from '@/lib/supabase'

const easeOutCubic = [0.215, 0.61, 0.355, 1] as const

const cardReveal = {
  hidden: { opacity: 0, y: 24 },
  show: { opacity: 1, y: 0 },
}

const cardStagger = {
  hidden: {},
  show: {
    transition: { staggerChildren: 0.08, delayChildren: 0.05 },
  },
}

export function Dashboard() {
  const { user, profile, loading: authLoading, refreshProfile } = useAuth()
  const [jobs, setJobs] = useState<Job[]>([])
  const [loading, setLoading] = useState(true)
  const reduceMotion = useReducedMotion()

  useEffect(() => {
    if (authLoading) return
    if (!user) {
      window.location.href = '/login?next=' + encodeURIComponent('/dashboard')
      return
    }
    refreshProfile()
    loadJobs()
  }, [user, authLoading])

  const loadJobs = async () => {
    if (!user) return
    const { data, error } = await supabase
      .from('jobs')
      .select('*')
      .eq('user_id', user.id)
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

  const completedJobs = jobs.filter((j) => j.status === 'completed').length

  const stats = [
    {
      title: 'Créditos disponíveis',
      value: `${availableCredits} MB`,
      hint: `${profile?.total_credits_mb || 0} MB comprados`,
      icon: CreditCard,
    },
    {
      title: 'Arquivos processados',
      value: String(completedJobs),
      hint: `${jobs.length} total`,
      icon: FileText,
    },
    {
      title: 'Usos gratuitos hoje',
      value: `${profile?.free_uses_today || 0}/3`,
      hint: 'Renova à meia-noite',
      icon: Clock,
    },
  ]

  return (
    <div className="min-h-screen bg-white text-[#0c0c0c]">
      <Header />

      <section className="relative overflow-hidden px-6 pb-8 pt-12 md:pt-14">
        <div className="pointer-events-none absolute inset-0" aria-hidden>
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_right,rgba(183,255,51,0.2),transparent_42%)]" />
          {!reduceMotion && (
            <motion.div
              className="absolute -right-16 top-0 h-64 w-64 rounded-full bg-[#b7ff33]/25 blur-3xl"
              animate={{ x: [0, -25, 12, 0], y: [0, 18, -8, 0] }}
              transition={{ duration: 14, repeat: Infinity, ease: 'easeInOut' }}
            />
          )}
        </div>

        <div className="relative mx-auto max-w-6xl">
          <motion.p
            className="text-sm font-medium text-[#727272]"
            initial={reduceMotion ? false : { opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, ease: easeOutCubic }}
          >
            Conta
          </motion.p>
          <motion.h1
            className="mt-1 text-3xl font-semibold tracking-tight md:text-4xl"
            initial={reduceMotion ? false : { opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.45, ease: easeOutCubic, delay: 0.05 }}
          >
            Painel de controle
          </motion.h1>
        </div>
      </section>

      <div className="relative mx-auto max-w-6xl px-6 pb-16">
        <motion.div
          className="grid gap-4 md:grid-cols-3"
          variants={cardStagger}
          initial={reduceMotion ? false : 'hidden'}
          animate="show"
        >
          {stats.map((stat) => {
            const Icon = stat.icon
            return (
              <motion.article
                key={stat.title}
                variants={cardReveal}
                transition={{ duration: 0.45, ease: easeOutCubic }}
                whileHover={
                  reduceMotion
                    ? undefined
                    : { y: -4, transition: { duration: 0.25, ease: easeOutCubic } }
                }
                className="rounded-2xl border border-black/8 bg-[#f7f8fa] p-6 will-change-transform"
              >
                <div className="mb-3 flex items-center justify-between">
                  <h3 className="text-sm font-medium text-[#727272]">{stat.title}</h3>
                  <span className="flex h-9 w-9 items-center justify-center rounded-full bg-[#b7ff33]">
                    <Icon className="h-4 w-4 text-[#0c0c0c]" />
                  </span>
                </div>
                <p className="text-3xl font-semibold tracking-tight">{stat.value}</p>
                <p className="mt-1 text-sm text-[#9b9b9b]">{stat.hint}</p>
              </motion.article>
            )
          })}
        </motion.div>

        {availableCredits < 10 && (
          <motion.div
            className="mt-6 flex flex-col gap-4 rounded-2xl border border-black/10 bg-[#0c0c0c] p-5 text-white sm:flex-row sm:items-center sm:justify-between"
            initial={reduceMotion ? false : { opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.45, ease: easeOutCubic, delay: 0.15 }}
          >
            <div className="flex items-start gap-3">
              <span className="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-[#b7ff33]">
                <AlertCircle className="h-4 w-4 text-[#0c0c0c]" />
              </span>
              <div>
                <h3 className="font-semibold">Créditos baixos</h3>
                <p className="mt-1 text-sm text-[#b8b8b8]">
                  Você tem apenas {availableCredits} MB disponíveis. Adicione mais créditos para
                  continuar processando arquivos grandes.
                </p>
              </div>
            </div>
            <Link
              to="/pricing"
              className="inline-flex shrink-0 items-center justify-center gap-2 rounded-full bg-[#b7ff33] px-5 py-2.5 text-sm font-semibold text-[#0c0c0c] hover:bg-[#c8ff66]"
            >
              Adicionar créditos
              <ArrowRight className="h-4 w-4" />
            </Link>
          </motion.div>
        )}

        <motion.section
          className="mt-8 overflow-hidden rounded-2xl border border-black/8 bg-white"
          initial={reduceMotion ? false : { opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, ease: easeOutCubic, delay: 0.2 }}
        >
          <div className="border-b border-black/8 px-6 py-5">
            <h2 className="text-xl font-semibold tracking-tight">Histórico de processamentos</h2>
          </div>

          <div className="divide-y divide-black/8">
            {loading ? (
              <div className="p-10 text-center text-[#727272]">Carregando...</div>
            ) : jobs.length === 0 ? (
              <div className="p-10 text-center">
                <p className="text-[#727272]">Nenhum arquivo processado ainda.</p>
                <Link
                  to="/upload"
                  className="mt-4 inline-flex items-center gap-2 rounded-full bg-[#0c0c0c] px-5 py-2.5 text-sm font-semibold text-white hover:bg-black"
                >
                  Enviar seu primeiro PDF
                  <ArrowRight className="h-4 w-4" />
                </Link>
              </div>
            ) : (
              jobs.map((job, index) => (
                <motion.div
                  key={job.id}
                  className="px-6 py-4 transition-colors hover:bg-[#f7f8fa]"
                  initial={reduceMotion ? false : { opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.35, ease: easeOutCubic, delay: 0.04 * index }}
                >
                  <div className="flex items-center justify-between gap-4">
                    <div className="min-w-0 flex-1">
                      <h3 className="truncate font-medium">{job.filename}</h3>
                      <div className="mt-1 flex flex-wrap items-center gap-x-4 gap-y-1 text-sm text-[#727272]">
                        <span>{job.file_size_mb.toFixed(2)} MB</span>
                        {job.pages_count ? <span>{job.pages_count} páginas</span> : null}
                        {job.documents_count ? <span>{job.documents_count} docs</span> : null}
                        <span>{new Date(job.created_at).toLocaleDateString('pt-BR')}</span>
                      </div>
                    </div>
                    <StatusBadge status={job.status} />
                  </div>
                </motion.div>
              ))
            )}
          </div>
        </motion.section>
      </div>

      <SiteFooter />
    </div>
  )
}

function StatusBadge({ status }: { status: string }) {
  const styles =
    status === 'completed'
      ? 'bg-[#b7ff33] text-[#0c0c0c]'
      : status === 'processing'
        ? 'bg-[#f4f5f7] text-[#0c0c0c]'
        : status === 'failed'
          ? 'bg-[#0c0c0c] text-white'
          : 'bg-[#f4f5f7] text-[#727272]'

  const label =
    status === 'completed'
      ? 'Concluído'
      : status === 'processing'
        ? 'Processando'
        : status === 'failed'
          ? 'Falhou'
          : status

  return (
    <span className={`shrink-0 rounded-full px-3 py-1 text-xs font-semibold ${styles}`}>
      {label}
    </span>
  )
}
