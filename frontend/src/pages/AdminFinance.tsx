import { FormEvent, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { motion, useReducedMotion } from 'motion/react'
import {
  ArrowLeft,
  Building2,
  CreditCard,
  RefreshCw,
  Shield,
  Undo2,
  Wallet,
} from 'lucide-react'
import { toast } from 'sonner'
import { Header } from '@/components/Header'
import { SiteFooter } from '@/components/SiteFooter'
import { useAuth } from '@/components/AuthProvider'
import { APP_VERSION } from '@/lib/version'

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000'
const easeOutCubic = [0.215, 0.61, 0.355, 1] as const

type Summary = {
  gross_paid_brl: number
  fees_brl: number
  net_paid_brl: number
  refunded_brl: number
  invoice_credits_mb: number
  paid_credits_mb: number
  invoiced_accounts: number
  paid_accounts: number
  active_paid_accounts: number
  low_balance_invoiced: number
  credits_in_circulation_mb: number
}

type InvoiceAccount = {
  user_id: string
  email: string
  credits_granted_mb: number
  amount_contracted_brl: number
  purchases: number
  available_mb: number
  used_credits_mb: number
  total_credits_mb: number
  low_balance: boolean
  jobs_recent: number
  mb_processed_recent: number
  last_at: string | null
  notes: string[]
}

type PaidAccount = {
  user_id: string
  email: string
  credits_bought_mb: number
  amount_paid_brl: number
  fee_brl: number
  purchases: number
  available_mb: number
  used_credits_mb: number
  active_paid: boolean
  methods: string[]
  jobs_recent: number
  mb_processed_recent: number
  last_at: string | null
}

type TxRow = {
  id: string
  user_email: string
  amount_brl: number
  credits_mb: number
  payment_method: string
  payment_id: string
  payment_status: string
  created_at: string
  fee_brl?: number
  refunded_amount_brl?: number
  refunded_credits_mb?: number
  package_id?: string | null
  is_invoice?: boolean
}

type Grant = {
  id: string
  user_email: string
  granted_by_email: string
  credits_mb: number
  amount_brl: number
  note: string | null
  created_at: string
}

type RefundRow = {
  id: string
  user_email: string
  amount_brl: number
  fee_brl: number
  credits_mb: number
  note: string | null
  created_at: string
  mp_refund_id: string | null
}

function money(v: number | undefined) {
  return `R$ ${Number(v || 0).toFixed(2)}`
}

function StatCard({
  label,
  value,
  hint,
}: {
  label: string
  value: string
  hint?: string
}) {
  return (
    <div className="rounded-2xl border border-black/8 bg-white p-4">
      <p className="text-xs font-medium uppercase tracking-wide text-[#727272]">{label}</p>
      <p className="mt-2 text-2xl font-semibold tracking-tight text-[#0c0c0c]">{value}</p>
      {hint ? <p className="mt-1 text-xs text-[#9b9b9b]">{hint}</p> : null}
    </div>
  )
}

export function AdminFinance() {
  const { user, loading: authLoading, getAccessToken } = useAuth()
  const reduceMotion = useReducedMotion()
  const [allowed, setAllowed] = useState(false)
  const [checking, setChecking] = useState(true)
  const [appVersion, setAppVersion] = useState(APP_VERSION)
  const [loading, setLoading] = useState(false)

  const [summary, setSummary] = useState<Summary | null>(null)
  const [invoiced, setInvoiced] = useState<InvoiceAccount[]>([])
  const [paid, setPaid] = useState<PaidAccount[]>([])
  const [transactions, setTransactions] = useState<TxRow[]>([])
  const [grants, setGrants] = useState<Grant[]>([])
  const [refunds, setRefunds] = useState<RefundRow[]>([])
  const [txBusy, setTxBusy] = useState<string | null>(null)

  const [grantEmail, setGrantEmail] = useState('')
  const [creditsMb, setCreditsMb] = useState('200')
  const [amountBrl, setAmountBrl] = useState('0')
  const [note, setNote] = useState('Venda faturada')
  const [granting, setGranting] = useState(false)

  const authHeaders = async () => {
    const token = await getAccessToken()
    if (!token) throw new Error('Sessão expirada. Faça login novamente.')
    return {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
    }
  }

  const loadFinance = async () => {
    setLoading(true)
    try {
      const headers = await authHeaders()
      const r = await fetch(`${BACKEND_URL}/api/admin/finance?limit=100`, { headers })
      const data = await r.json().catch(() => ({}))
      if (!r.ok) throw new Error(typeof data.detail === 'string' ? data.detail : 'Falha ao carregar financeiro')
      if (data.version) setAppVersion(data.version)
      setSummary(data.summary || null)
      setInvoiced(data.invoiced_accounts || [])
      setPaid(data.paid_accounts || [])
      setTransactions(data.transactions || [])
      setGrants(data.grants || [])
      setRefunds(data.refunds || [])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (authLoading) return
    if (!user) {
      window.location.href = '/login?next=' + encodeURIComponent('/admin/finance')
      return
    }
    ;(async () => {
      try {
        const headers = await authHeaders()
        const me = await fetch(`${BACKEND_URL}/api/admin/me`, { headers })
        if (!me.ok) {
          setAllowed(false)
          return
        }
        setAllowed(true)
        await loadFinance()
      } catch {
        setAllowed(false)
      } finally {
        setChecking(false)
      }
    })()
  }, [user, authLoading])

  const onGrant = async (event: FormEvent) => {
    event.preventDefault()
    setGranting(true)
    try {
      const headers = await authHeaders()
      const r = await fetch(`${BACKEND_URL}/api/admin/grant-credits`, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          email: grantEmail.trim(),
          credits_mb: Number(creditsMb),
          amount_brl: Number(amountBrl || 0),
          note: note.trim() || null,
          days_valid: 90,
        }),
      })
      const data = await r.json().catch(() => ({}))
      if (!r.ok) {
        throw new Error(typeof data.detail === 'string' ? data.detail : 'Falha ao liberar créditos')
      }
      toast.success(`Créditos liberados para ${data.user?.email}`)
      setGrantEmail('')
      await loadFinance()
    } catch (error) {
      toast.error(error instanceof Error ? error.message : 'Erro ao liberar créditos')
    } finally {
      setGranting(false)
    }
  }

  const refundTransaction = async (tx: TxRow) => {
    setTxBusy(tx.id)
    try {
      const headers = await authHeaders()
      const previewRes = await fetch(`${BACKEND_URL}/api/admin/transactions/${tx.id}/refund-preview`, {
        headers,
      })
      const preview = await previewRes.json().catch(() => ({}))
      if (!previewRes.ok) {
        throw new Error(typeof preview.detail === 'string' ? preview.detail : 'Falha na prévia')
      }
      if (!preview.can_refund) {
        throw new Error((preview.block_reasons || []).join(' ') || 'Reembolso não permitido')
      }

      const moneyLabel = Number(preview.refund_amount_brl || 0).toFixed(2)
      const credits = preview.credits_to_claw_mb
      const fee = Number(preview.fee_brl || 0).toFixed(2)
      const msg = preview.is_invoice
        ? `Estornar ${credits} MB desta venda faturada? (dinheiro fora do Mercado Pago)`
        : `Reembolsar R$ ${moneyLabel} e estornar ${credits} MB?\nTaxa operadora: R$ ${fee}${
            preview.deduct_fee ? ' (descontada do valor)' : ' (PIX: não desconta na política)'
          }`
      if (!window.confirm(msg)) return

      const refundNote = window.prompt('Observação do reembolso (opcional):', 'Solicitação do cliente') || null
      const r = await fetch(`${BACKEND_URL}/api/admin/transactions/${tx.id}/refund`, {
        method: 'POST',
        headers,
        body: JSON.stringify({ note: refundNote }),
      })
      const data = await r.json().catch(() => ({}))
      if (!r.ok) {
        throw new Error(typeof data.detail === 'string' ? data.detail : 'Falha no reembolso')
      }
      toast.success(
        data.invoice_manual_money
          ? `${data.credits_clawed_mb} MB estornados (faturado)`
          : `Reembolso de R$ ${Number(data.refund_amount_brl).toFixed(2)} + ${data.credits_clawed_mb} MB`,
      )
      await loadFinance()
    } catch (error) {
      toast.error(error instanceof Error ? error.message : 'Erro no reembolso')
    } finally {
      setTxBusy(null)
    }
  }

  if (checking || authLoading) {
    return (
      <div className="min-h-screen bg-white">
        <Header />
        <p className="p-10 text-center text-[#727272]">Carregando financeiro...</p>
      </div>
    )
  }

  if (!allowed) {
    return (
      <div className="min-h-screen bg-white">
        <Header />
        <div className="mx-auto max-w-lg px-6 py-20 text-center">
          <Shield className="mx-auto h-10 w-10 text-[#0c0c0c]" />
          <h1 className="mt-4 text-2xl font-semibold">Acesso negado</h1>
          <Link to="/admin" className="mt-6 inline-block rounded-full bg-[#0c0c0c] px-5 py-2.5 text-sm font-semibold text-white">
            Voltar ao admin
          </Link>
        </div>
      </div>
    )
  }

  const activePaid = paid.filter((p) => p.active_paid)

  return (
    <div className="min-h-screen bg-white text-[#0c0c0c]">
      <Header />
      <section className="relative overflow-hidden px-6 pb-8 pt-12">
        <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_top_right,rgba(183,255,51,0.2),transparent_42%)]" />
        <div className="relative mx-auto max-w-6xl">
          <Link to="/admin" className="inline-flex items-center gap-1 text-sm text-[#727272] hover:text-[#0c0c0c]">
            <ArrowLeft className="h-4 w-4" />
            Admin
          </Link>
          <div className="mt-2 flex flex-wrap items-end justify-between gap-3">
            <div>
              <p className="text-sm font-medium text-[#727272]">Financeiro</p>
              <h1 className="text-3xl font-semibold tracking-tight md:text-4xl">Dashboard financeiro</h1>
              <p className="mt-2 text-[#727272]">
                Compras, faturado, saldos e reembolsos em um só lugar.
              </p>
            </div>
            <div className="flex items-center gap-2">
              <span className="rounded-full border border-black/10 bg-white px-3 py-1 text-sm">v{appVersion}</span>
              <button
                type="button"
                onClick={() => loadFinance().catch((e) => toast.error(e instanceof Error ? e.message : 'Erro'))}
                className="inline-flex items-center gap-2 rounded-full bg-[#0c0c0c] px-4 py-2 text-sm font-semibold text-white"
              >
                <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
                Atualizar
              </button>
            </div>
          </div>
        </div>
      </section>

      <div className="mx-auto max-w-6xl space-y-6 px-6 pb-16">
        <motion.div
          className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4"
          initial={reduceMotion ? false : { opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, ease: easeOutCubic }}
        >
          <StatCard label="Receita bruta (pago)" value={money(summary?.gross_paid_brl)} hint={`Líquido ${money(summary?.net_paid_brl)}`} />
          <StatCard label="Taxas operadora" value={money(summary?.fees_brl)} hint={`Reembolsado ${money(summary?.refunded_brl)}`} />
          <StatCard
            label="Empresas faturadas"
            value={String(summary?.invoiced_accounts ?? 0)}
            hint={`${summary?.invoice_credits_mb ?? 0} MB liberados · ${summary?.low_balance_invoiced ?? 0} saldo baixo`}
          />
          <StatCard
            label="Contas pagas ativas"
            value={String(summary?.active_paid_accounts ?? 0)}
            hint={`${summary?.credits_in_circulation_mb ?? 0} MB em circulação`}
          />
        </motion.div>

        <div className="grid gap-6 lg:grid-cols-2">
          <motion.form
            onSubmit={onGrant}
            className="rounded-2xl border border-black/8 bg-[#f7f8fa] p-6"
            initial={reduceMotion ? false : { opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.45, ease: easeOutCubic }}
          >
            <div className="mb-4 flex items-center gap-2">
              <Wallet className="h-5 w-5" />
              <h2 className="text-lg font-semibold">Liberar créditos (faturado)</h2>
            </div>
            <label className="mb-3 block text-sm">
              E-mail do cliente
              <input
                required
                type="email"
                value={grantEmail}
                onChange={(e) => setGrantEmail(e.target.value)}
                className="mt-1 w-full rounded-xl border border-black/10 bg-white px-3 py-2.5"
                placeholder="cliente@empresa.com"
              />
            </label>
            <div className="mb-3 grid grid-cols-2 gap-3">
              <label className="block text-sm">
                Créditos (MB)
                <input
                  required
                  type="number"
                  min={1}
                  value={creditsMb}
                  onChange={(e) => setCreditsMb(e.target.value)}
                  className="mt-1 w-full rounded-xl border border-black/10 bg-white px-3 py-2.5"
                />
              </label>
              <label className="block text-sm">
                Valor faturado (R$)
                <input
                  type="number"
                  min={0}
                  step="0.01"
                  value={amountBrl}
                  onChange={(e) => setAmountBrl(e.target.value)}
                  className="mt-1 w-full rounded-xl border border-black/10 bg-white px-3 py-2.5"
                />
              </label>
            </div>
            <label className="mb-4 block text-sm">
              Observação
              <input
                value={note}
                onChange={(e) => setNote(e.target.value)}
                className="mt-1 w-full rounded-xl border border-black/10 bg-white px-3 py-2.5"
                placeholder="NF 123 / contrato"
              />
            </label>
            <button
              type="submit"
              disabled={granting}
              className="w-full rounded-full bg-[#b7ff33] py-3 text-sm font-semibold text-[#0c0c0c] hover:bg-[#c8ff66] disabled:opacity-50"
            >
              {granting ? 'Liberando...' : 'Liberar créditos'}
            </button>
          </motion.form>

          <motion.div
            className="rounded-2xl border border-black/8 bg-white p-6"
            initial={reduceMotion ? false : { opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.45, ease: easeOutCubic, delay: 0.05 }}
          >
            <h2 className="mb-3 text-lg font-semibold">Resumo rápido</h2>
            <ul className="space-y-2 text-sm text-[#3a3a3a]">
              <li>Créditos pagos liberados: <strong>{summary?.paid_credits_mb ?? 0} MB</strong></li>
              <li>Créditos faturados liberados: <strong>{summary?.invoice_credits_mb ?? 0} MB</strong></li>
              <li>Contas com compra online: <strong>{summary?.paid_accounts ?? 0}</strong></li>
              <li>Contas faturadas com saldo baixo (≤20%): <strong>{summary?.low_balance_invoiced ?? 0}</strong></li>
            </ul>
            <p className="mt-4 text-xs text-[#9b9b9b]">
              Política: cartão/débito/boleto devolvem valor − taxa; PIX devolve valor pago; faturado só estorna MB.
            </p>
          </motion.div>
        </div>

        <motion.div
          className="rounded-2xl border border-black/8 bg-white p-6"
          initial={reduceMotion ? false : { opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.45, ease: easeOutCubic, delay: 0.08 }}
        >
          <div className="mb-4 flex items-center gap-2">
            <Building2 className="h-5 w-5" />
            <h2 className="text-lg font-semibold">Empresas faturadas — saldos</h2>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full min-w-[720px] text-left text-sm">
              <thead className="text-[#727272]">
                <tr className="border-b border-black/8">
                  <th className="py-2 pr-3 font-medium">Empresa</th>
                  <th className="py-2 pr-3 font-medium">Liberado</th>
                  <th className="py-2 pr-3 font-medium">Usado</th>
                  <th className="py-2 pr-3 font-medium">Disponível</th>
                  <th className="py-2 pr-3 font-medium">Contrato</th>
                  <th className="py-2 font-medium">Status</th>
                </tr>
              </thead>
              <tbody>
                {invoiced.map((a) => (
                  <tr key={a.user_id} className="border-b border-black/5">
                    <td className="py-3 pr-3">
                      <p className="font-medium">{a.email}</p>
                      <p className="text-xs text-[#9b9b9b]">
                        {a.purchases} liberação(ões)
                        {a.last_at ? ` · ${new Date(a.last_at).toLocaleDateString('pt-BR')}` : ''}
                      </p>
                    </td>
                    <td className="py-3 pr-3">{a.credits_granted_mb} MB</td>
                    <td className="py-3 pr-3">{a.used_credits_mb} MB</td>
                    <td className="py-3 pr-3 font-semibold">{a.available_mb} MB</td>
                    <td className="py-3 pr-3">{money(a.amount_contracted_brl)}</td>
                    <td className="py-3">
                      {a.low_balance ? (
                        <span className="rounded-full bg-[#0c0c0c] px-2.5 py-1 text-xs font-semibold text-[#b7ff33]">
                          Saldo baixo
                        </span>
                      ) : (
                        <span className="text-xs text-[#727272]">OK · {a.jobs_recent} jobs recentes</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {invoiced.length === 0 && (
              <p className="py-6 text-center text-[#727272]">Nenhuma empresa faturada ainda.</p>
            )}
          </div>
        </motion.div>

        <motion.div
          className="rounded-2xl border border-black/8 bg-white p-6"
          initial={reduceMotion ? false : { opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.45, ease: easeOutCubic, delay: 0.1 }}
        >
          <div className="mb-4 flex items-center gap-2">
            <CreditCard className="h-5 w-5" />
            <h2 className="text-lg font-semibold">Contas pagas (Mercado Pago)</h2>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full min-w-[720px] text-left text-sm">
              <thead className="text-[#727272]">
                <tr className="border-b border-black/8">
                  <th className="py-2 pr-3 font-medium">Cliente</th>
                  <th className="py-2 pr-3 font-medium">Pago</th>
                  <th className="py-2 pr-3 font-medium">Taxa</th>
                  <th className="py-2 pr-3 font-medium">MB comprados</th>
                  <th className="py-2 pr-3 font-medium">Disponível</th>
                  <th className="py-2 font-medium">Uso</th>
                </tr>
              </thead>
              <tbody>
                {paid.map((a) => (
                  <tr key={a.user_id} className="border-b border-black/5">
                    <td className="py-3 pr-3">
                      <p className="font-medium">{a.email}</p>
                      <p className="text-xs text-[#9b9b9b]">{(a.methods || []).join(', ') || '—'}</p>
                    </td>
                    <td className="py-3 pr-3">{money(a.amount_paid_brl)}</td>
                    <td className="py-3 pr-3">{money(a.fee_brl)}</td>
                    <td className="py-3 pr-3">{a.credits_bought_mb} MB</td>
                    <td className="py-3 pr-3 font-semibold">
                      {a.available_mb} MB
                      {!a.active_paid ? <span className="ml-2 text-xs font-normal text-[#9b9b9b]">esgotado</span> : null}
                    </td>
                    <td className="py-3 text-[#727272]">
                      {a.used_credits_mb} MB usados · {a.jobs_recent} jobs
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {paid.length === 0 && (
              <p className="py-6 text-center text-[#727272]">Nenhuma compra online ainda.</p>
            )}
            {activePaid.length > 0 && (
              <p className="mt-3 text-sm text-[#727272]">
                {activePaid.length} conta(s) com saldo pago ativo agora.
              </p>
            )}
          </div>
        </motion.div>

        <motion.div
          className="rounded-2xl border border-black/8 bg-white p-6"
          initial={reduceMotion ? false : { opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.45, ease: easeOutCubic, delay: 0.12 }}
        >
          <div className="mb-4 flex items-center gap-2">
            <Undo2 className="h-5 w-5" />
            <h2 className="text-lg font-semibold">Movimentações e reembolsos</h2>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full min-w-[760px] text-left text-sm">
              <thead className="text-[#727272]">
                <tr className="border-b border-black/8">
                  <th className="py-2 pr-3 font-medium">Cliente</th>
                  <th className="py-2 pr-3 font-medium">Valor</th>
                  <th className="py-2 pr-3 font-medium">Taxa</th>
                  <th className="py-2 pr-3 font-medium">MB</th>
                  <th className="py-2 pr-3 font-medium">Método</th>
                  <th className="py-2 pr-3 font-medium">Status</th>
                  <th className="py-2 font-medium">Ação</th>
                </tr>
              </thead>
              <tbody>
                {transactions.map((tx) => {
                  const refundable =
                    tx.payment_status === 'approved' || tx.payment_status === 'partially_refunded'
                  return (
                    <tr key={tx.id} className="border-b border-black/5 align-top">
                      <td className="py-3 pr-3">
                        <p className="font-medium">{tx.user_email || '—'}</p>
                        <p className="text-xs text-[#9b9b9b]">
                          {new Date(tx.created_at).toLocaleString('pt-BR')}
                          {tx.package_id ? ` · ${tx.package_id}` : ''}
                          {tx.is_invoice ? ' · faturado' : ''}
                        </p>
                        <p className="text-xs text-[#9b9b9b]">{tx.payment_id}</p>
                      </td>
                      <td className="py-3 pr-3">{money(tx.amount_brl)}</td>
                      <td className="py-3 pr-3">{money(tx.fee_brl)}</td>
                      <td className="py-3 pr-3">
                        {tx.credits_mb}
                        {tx.refunded_credits_mb ? ` (−${tx.refunded_credits_mb})` : ''}
                      </td>
                      <td className="py-3 pr-3">{tx.payment_method}</td>
                      <td className="py-3 pr-3">{tx.payment_status}</td>
                      <td className="py-3">
                        {refundable ? (
                          <button
                            type="button"
                            disabled={txBusy === tx.id}
                            onClick={() => refundTransaction(tx)}
                            className="rounded-full bg-[#0c0c0c] px-3 py-1.5 text-xs font-semibold text-white disabled:opacity-50"
                          >
                            {txBusy === tx.id ? '...' : 'Reembolsar'}
                          </button>
                        ) : (
                          <span className="text-xs text-[#9b9b9b]">—</span>
                        )}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
            {transactions.length === 0 && (
              <p className="py-6 text-center text-[#727272]">Nenhuma movimentação.</p>
            )}
          </div>
        </motion.div>

        <div className="grid gap-6 lg:grid-cols-2">
          <div className="rounded-2xl border border-black/8 bg-white p-6">
            <h2 className="mb-4 text-lg font-semibold">Liberações faturadas</h2>
            <div className="divide-y divide-black/8">
              {grants.map((g) => (
                <div key={g.id} className="flex flex-col gap-1 py-3 text-sm">
                  <p className="font-medium">{g.user_email}</p>
                  <p className="text-[#727272]">
                    {g.credits_mb} MB · {money(g.amount_brl)}
                    {g.note ? ` · ${g.note}` : ''}
                  </p>
                  <p className="text-xs text-[#9b9b9b]">
                    {new Date(g.created_at).toLocaleString('pt-BR')} · {g.granted_by_email || 'admin'}
                  </p>
                </div>
              ))}
              {grants.length === 0 && <p className="py-6 text-center text-[#727272]">Nenhuma liberação.</p>}
            </div>
          </div>
          <div className="rounded-2xl border border-black/8 bg-white p-6">
            <h2 className="mb-4 text-lg font-semibold">Reembolsos feitos</h2>
            <div className="divide-y divide-black/8">
              {refunds.map((r) => (
                <div key={r.id} className="flex flex-col gap-1 py-3 text-sm">
                  <p className="font-medium">{r.user_email}</p>
                  <p className="text-[#727272]">
                    {money(r.amount_brl)} · {r.credits_mb} MB · taxa {money(r.fee_brl)}
                  </p>
                  <p className="text-xs text-[#9b9b9b]">
                    {new Date(r.created_at).toLocaleString('pt-BR')}
                    {r.mp_refund_id ? ` · MP ${r.mp_refund_id}` : ''}
                    {r.note ? ` · ${r.note}` : ''}
                  </p>
                </div>
              ))}
              {refunds.length === 0 && <p className="py-6 text-center text-[#727272]">Nenhum reembolso ainda.</p>}
            </div>
          </div>
        </div>
      </div>
      <SiteFooter />
    </div>
  )
}
