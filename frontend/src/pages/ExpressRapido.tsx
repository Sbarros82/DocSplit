import { FormEvent, useCallback, useEffect, useState } from 'react'
import { Link, useParams, useSearchParams } from 'react-router-dom'
import { motion, useReducedMotion } from 'motion/react'
import { CheckCircle, Download, MessageCircle, Upload } from 'lucide-react'
import { toast } from 'sonner'
import { Header } from '@/components/Header'
import { SiteFooter } from '@/components/SiteFooter'
import { Seo } from '@/components/Seo'

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000'
const easeOutCubic = [0.215, 0.61, 0.355, 1] as const

type JobStatus = {
  token: string
  status: string
  pages_count?: number
  amount_brl?: number
  price_per_page_brl?: number
  file_size_mb?: number
  original_filename?: string
  download_ready?: boolean
  download_url?: string | null
  whatsapp_share_url?: string | null
  error_message?: string | null
  pricing?: { min_brl: number; le_50: number; gt_50: number; max_file_mb: number }
}

function money(v?: number) {
  return (v ?? 0).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
}

function statusLabel(status: string) {
  const map: Record<string, string> = {
    awaiting_payment: 'Aguardando pagamento',
    paid: 'Pago — preparando arquivo',
    processing: 'Separando PDF…',
    completed: 'Pronto para baixar',
    error: 'Erro no processamento',
  }
  return map[status] || status
}

export function ExpressRapido() {
  const { token } = useParams()
  const [search] = useSearchParams()
  const reduceMotion = useReducedMotion()
  const [file, setFile] = useState<File | null>(null)
  const [whatsapp, setWhatsapp] = useState('')
  const [email, setEmail] = useState('')
  const [busy, setBusy] = useState(false)
  const [job, setJob] = useState<JobStatus | null>(null)

  const loadJob = useCallback(async (t: string) => {
    const r = await fetch(`${BACKEND_URL}/api/express/${encodeURIComponent(t)}`)
    const data = await r.json().catch(() => ({}))
    if (!r.ok) throw new Error(typeof data.detail === 'string' ? data.detail : 'Pedido não encontrado')
    setJob(data)
    return data as JobStatus
  }, [])

  useEffect(() => {
    if (!token) return
    let cancelled = false
    const tick = async () => {
      try {
        const data = await loadJob(token)
        if (cancelled) return
        const paid = search.get('paid')
        const paymentId = search.get('payment_id')
        if (
          paid === '1' &&
          paymentId &&
          data.status !== 'completed' &&
          data.status !== 'processing'
        ) {
          await fetch(
            `${BACKEND_URL}/api/express/${encodeURIComponent(token)}/sync?payment_id=${encodeURIComponent(paymentId)}`,
            { method: 'POST' },
          )
          if (!cancelled) await loadJob(token)
        }
      } catch (e) {
        if (!cancelled) toast.error(e instanceof Error ? e.message : 'Erro ao carregar pedido')
      }
    }
    tick()
    const id = window.setInterval(() => {
      if (!token) return
      loadJob(token).catch(() => {})
    }, 4000)
    return () => {
      cancelled = true
      window.clearInterval(id)
    }
  }, [token, search, loadJob])

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault()
    if (!file) {
      toast.error('Selecione um PDF.')
      return
    }
    if (!whatsapp.trim()) {
      toast.error('Informe o WhatsApp com DDD.')
      return
    }
    setBusy(true)
    try {
      const fd = new FormData()
      fd.append('file', file)
      fd.append('whatsapp', whatsapp.trim())
      if (email.trim()) fd.append('email', email.trim())
      const r = await fetch(`${BACKEND_URL}/api/express/create`, { method: 'POST', body: fd })
      const data = await r.json().catch(() => ({}))
      if (!r.ok) throw new Error(typeof data.detail === 'string' ? data.detail : 'Falha ao criar pedido')
      if (data.checkout_url) {
        window.location.href = data.checkout_url
        return
      }
      throw new Error('Checkout indisponível')
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Erro')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="min-h-screen bg-[#f7f8fa] text-[#0c0c0c]">
      <Seo
        title="DocSplit Rápido — Pague por página e receba no WhatsApp"
        description="Separe PDF misturado agora: até 50 páginas R$ 0,50/página, acima R$ 0,25/página, mínimo R$ 2. Pague com Pix e baixe ou abra no WhatsApp."
        path="/rapido"
      />
      <Header />
      <main className="mx-auto max-w-3xl px-6 py-12">
        <motion.div
          initial={reduceMotion ? false : { opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.45, ease: easeOutCubic }}
          className="rounded-3xl border border-black/8 bg-white p-6 shadow-sm md:p-10"
        >
          <p className="mb-3 text-sm font-medium text-[#727272]">DocSplit Rápido</p>
          <h1 className="text-3xl font-semibold tracking-tight md:text-4xl">
            Separe o PDF, pague e receba no WhatsApp
          </h1>
          <p className="mt-3 text-[#727272]">
            Até 50 páginas: <strong>R$ 0,50</strong>/página · acima de 50: <strong>R$ 0,25</strong>/página ·
            mínimo <strong>R$ 2,00</strong> · arquivo até <strong>25 MB</strong>.
          </p>

          {!token && (
            <form className="mt-8 space-y-4" onSubmit={onSubmit}>
              <label className="block">
                <span className="text-sm text-[#727272]">PDF misturado</span>
                <div className="mt-2 flex items-center gap-3 rounded-2xl border border-dashed border-black/15 bg-[#f7f8fa] px-4 py-5">
                  <Upload className="h-5 w-5 shrink-0" />
                  <div className="min-w-0 flex-1">
                    <input
                      type="file"
                      accept=".pdf,application/pdf"
                      onChange={(ev) => setFile(ev.target.files?.[0] || null)}
                      className="w-full text-sm"
                    />
                    {file && (
                      <p className="mt-1 truncate text-xs text-[#727272]">
                        {file.name} · {(file.size / (1024 * 1024)).toFixed(2)} MB
                      </p>
                    )}
                  </div>
                </div>
              </label>
              <label className="block">
                <span className="text-sm text-[#727272]">WhatsApp (com DDD)</span>
                <input
                  value={whatsapp}
                  onChange={(ev) => setWhatsapp(ev.target.value)}
                  placeholder="82999999999"
                  className="mt-2 w-full rounded-2xl border border-black/10 px-4 py-3 text-sm outline-none focus:border-[#0c0c0c]"
                />
              </label>
              <label className="block">
                <span className="text-sm text-[#727272]">E-mail (opcional, para o Pix)</span>
                <input
                  type="email"
                  value={email}
                  onChange={(ev) => setEmail(ev.target.value)}
                  placeholder="voce@empresa.com"
                  className="mt-2 w-full rounded-2xl border border-black/10 px-4 py-3 text-sm outline-none focus:border-[#0c0c0c]"
                />
              </label>
              <button
                type="submit"
                disabled={busy}
                className="w-full rounded-full bg-[#0c0c0c] px-6 py-3.5 text-sm font-semibold text-white disabled:opacity-60"
              >
                {busy ? 'Gerando pagamento…' : 'Calcular e pagar com Pix'}
              </button>
              <p className="text-center text-xs text-[#9b9b9b]">
                Exemplos: 10 pág = R$ 5 · 50 pág = R$ 25 · 80 pág = R$ 20
              </p>
            </form>
          )}

          {token && job && (
            <div className="mt-8 space-y-4">
              <div className="rounded-2xl bg-[#f7f8fa] p-4">
                <p className="text-sm text-[#727272]">{statusLabel(job.status)}</p>
                <p className="mt-1 font-medium">{job.original_filename || 'documento.pdf'}</p>
                <p className="mt-2 text-sm text-[#727272]">
                  {job.pages_count} página(s) · {money(job.amount_brl)}
                  {job.price_per_page_brl ? ` · ${money(job.price_per_page_brl)}/pág` : ''}
                </p>
              </div>

              {job.status === 'completed' && job.download_url && (
                <div className="flex flex-col gap-3 sm:flex-row">
                  <a
                    href={job.download_url}
                    className="inline-flex flex-1 items-center justify-center gap-2 rounded-full bg-[#0c0c0c] px-5 py-3 text-sm font-semibold text-white"
                  >
                    <Download className="h-4 w-4" /> Baixar ZIP separado
                  </a>
                  {job.whatsapp_share_url && (
                    <a
                      href={job.whatsapp_share_url}
                      target="_blank"
                      rel="noreferrer"
                      className="inline-flex flex-1 items-center justify-center gap-2 rounded-full border border-black/10 bg-[#b7ff33] px-5 py-3 text-sm font-semibold text-[#0c0c0c]"
                    >
                      <MessageCircle className="h-4 w-4" /> Abrir no WhatsApp
                    </a>
                  )}
                </div>
              )}

              {job.status === 'completed' && (
                <p className="flex items-center gap-2 text-sm text-[#167447]">
                  <CheckCircle className="h-4 w-4" /> Arquivo pronto. Guarde o link do WhatsApp.
                </p>
              )}

              {(job.status === 'paid' || job.status === 'processing') && (
                <p className="text-sm text-[#727272]">Aguarde alguns segundos — estamos separando o PDF…</p>
              )}

              {job.status === 'error' && (
                <p className="text-sm text-[#b42318]">{job.error_message || 'Falha ao processar.'}</p>
              )}

              {job.status === 'awaiting_payment' && (
                <p className="text-sm text-[#727272]">
                  Se já pagou, aguarde a confirmação do Pix. Esta página atualiza sozinha.
                </p>
              )}

              <Link to="/rapido" className="inline-block text-sm text-[#727272] underline">
                Novo PDF
              </Link>
            </div>
          )}
        </motion.div>
      </main>
      <SiteFooter />
    </div>
  )
}
