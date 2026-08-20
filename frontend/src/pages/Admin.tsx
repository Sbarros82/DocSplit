import { FormEvent, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { motion, useReducedMotion } from 'motion/react'
import { Copy, Globe, KeyRound, ScrollText, Search, Shield, Undo2, Wallet } from 'lucide-react'
import { toast } from 'sonner'
import { Header } from '@/components/Header'
import { SiteFooter } from '@/components/SiteFooter'
import { useAuth } from '@/components/AuthProvider'
import { APP_VERSION } from '@/lib/version'

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000'
const easeOutCubic = [0.215, 0.61, 0.355, 1] as const

type AdminUser = {
  id: string
  email: string
  role?: string
  total_credits_mb: number
  used_credits_mb: number
  available_mb: number
  free_uses_today?: number
  pdf_tools_uses_today?: number
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
  net_amount_brl?: number
  refunded_amount_brl?: number
  refunded_credits_mb?: number
  package_id?: string | null
  source?: string | null
  user_available_mb?: number
}

type IpUsage = {
  ip: string
  usage_date: string
  free_process_count: number
  tool_use_count: number
  last_email: string | null
  updated_at: string
}

export function Admin() {
  const { user, profile, loading: authLoading, getAccessToken } = useAuth()
  const reduceMotion = useReducedMotion()
  const [allowed, setAllowed] = useState(false)
  const [checking, setChecking] = useState(true)
  const [appVersion, setAppVersion] = useState(APP_VERSION)

  const [search, setSearch] = useState('')
  const [users, setUsers] = useState<AdminUser[]>([])
  const [grants, setGrants] = useState<Grant[]>([])
  const [transactions, setTransactions] = useState<TxRow[]>([])
  const [txBusy, setTxBusy] = useState<string | null>(null)
  const [ipUsage, setIpUsage] = useState<IpUsage[]>([])

  const [grantEmail, setGrantEmail] = useState('')
  const [creditsMb, setCreditsMb] = useState('200')
  const [amountBrl, setAmountBrl] = useState('0')
  const [note, setNote] = useState('Venda faturada')
  const [granting, setGranting] = useState(false)

  const [pwdEmail, setPwdEmail] = useState('sbarros1982@gmail.com')
  const [pwdManual, setPwdManual] = useState('')
  const [generatedPwd, setGeneratedPwd] = useState<string | null>(null)
  const [pwdBusy, setPwdBusy] = useState(false)

  const authHeaders = async () => {
    const token = await getAccessToken()
    if (!token) throw new Error('Sessão expirada. Faça login novamente.')
    return {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
    }
  }

  const loadGrants = async () => {
    const headers = await authHeaders()
    const r = await fetch(`${BACKEND_URL}/api/admin/grants`, { headers })
    if (!r.ok) return
    const data = await r.json()
    setGrants(data.grants || [])
  }

  const loadTransactions = async () => {
    const headers = await authHeaders()
    const r = await fetch(`${BACKEND_URL}/api/admin/transactions?limit=50`, { headers })
    if (!r.ok) return
    const data = await r.json()
    setTransactions(data.transactions || [])
  }

  const loadIpUsage = async () => {
    const headers = await authHeaders()
    const r = await fetch(`${BACKEND_URL}/api/admin/ip-usage`, { headers })
    if (!r.ok) return
    const data = await r.json()
    setIpUsage(data.items || [])
  }

  const loadUsers = async (q?: string) => {
    const headers = await authHeaders()
    const qs = q ? `?q=${encodeURIComponent(q)}` : ''
    const r = await fetch(`${BACKEND_URL}/api/admin/users${qs}`, { headers })
    if (!r.ok) throw new Error('Falha ao buscar usuários')
    const data = await r.json()
    setUsers(data.users || [])
  }

  useEffect(() => {
    if (authLoading) return
    if (!user) {
      window.location.href = '/login?next=' + encodeURIComponent('/admin')
      return
    }

    ;(async () => {
      try {
        const headers = await authHeaders()
        const r = await fetch(`${BACKEND_URL}/api/admin/me`, { headers })
        if (!r.ok) {
          setAllowed(false)
          setChecking(false)
          return
        }
        const me = await r.json()
        if (me.version) setAppVersion(me.version)
        setAllowed(true)
        setPwdEmail(user.email || 'sbarros1982@gmail.com')
        await Promise.all([loadUsers(), loadGrants(), loadIpUsage(), loadTransactions()])
      } catch {
        setAllowed(false)
      } finally {
        setChecking(false)
      }
    })()
  }, [user, authLoading])

  const onSearch = async (event: FormEvent) => {
    event.preventDefault()
    try {
      await loadUsers(search.trim())
    } catch (error) {
      toast.error(error instanceof Error ? error.message : 'Erro na busca')
    }
  }

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
      await Promise.all([loadUsers(search.trim() || undefined), loadGrants()])
    } catch (error) {
      toast.error(error instanceof Error ? error.message : 'Erro ao liberar créditos')
    } finally {
      setGranting(false)
    }
  }

  const setPassword = async (generate: boolean) => {
    setPwdBusy(true)
    setGeneratedPwd(null)
    try {
      const headers = await authHeaders()
      const r = await fetch(`${BACKEND_URL}/api/admin/set-password`, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          email: pwdEmail.trim(),
          password: generate ? null : pwdManual,
          generate,
        }),
      })
      const data = await r.json().catch(() => ({}))
      if (!r.ok) {
        throw new Error(typeof data.detail === 'string' ? data.detail : 'Falha ao definir senha')
      }
      setGeneratedPwd(data.password)
      setPwdManual('')
      toast.success('Senha definida. Copie e guarde agora.')
    } catch (error) {
      toast.error(error instanceof Error ? error.message : 'Erro ao definir senha')
    } finally {
      setPwdBusy(false)
    }
  }

  const copyPwd = async () => {
    if (!generatedPwd) return
    await navigator.clipboard.writeText(generatedPwd)
    toast.success('Senha copiada')
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

      const money = Number(preview.refund_amount_brl || 0).toFixed(2)
      const credits = preview.credits_to_claw_mb
      const fee = Number(preview.fee_brl || 0).toFixed(2)
      const msg = preview.is_invoice
        ? `Estornar ${credits} MB desta venda faturada? (dinheiro fora do Mercado Pago)`
        : `Reembolsar R$ ${money} e estornar ${credits} MB?\nTaxa operadora: R$ ${fee}${
            preview.deduct_fee ? ' (descontada do valor)' : ' (PIX: não desconta na política)'
          }`

      if (!preview.can_refund) {
        throw new Error((preview.block_reasons || []).join(' ') || 'Reembolso não permitido')
      }
      if (!window.confirm(msg)) return

      const note = window.prompt('Observação do reembolso (opcional):', 'Solicitação do cliente') || null
      const r = await fetch(`${BACKEND_URL}/api/admin/transactions/${tx.id}/refund`, {
        method: 'POST',
        headers,
        body: JSON.stringify({ note }),
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
      await Promise.all([loadTransactions(), loadUsers(search.trim() || undefined)])
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
        <p className="p-10 text-center text-[#727272]">Verificando acesso...</p>
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
          <p className="mt-2 text-[#727272]">Esta área é exclusiva para administradores.</p>
          <Link to="/dashboard" className="mt-6 inline-block rounded-full bg-[#0c0c0c] px-5 py-2.5 text-sm font-semibold text-white">
            Voltar ao painel
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-white text-[#0c0c0c]">
      <Header />
      <section className="relative overflow-hidden px-6 pb-8 pt-12">
        <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_top_right,rgba(183,255,51,0.2),transparent_42%)]" />
        <div className="relative mx-auto max-w-6xl">
          <p className="text-sm font-medium text-[#727272]">Administração</p>
          <div className="mt-1 flex flex-wrap items-end justify-between gap-3">
            <h1 className="text-3xl font-semibold tracking-tight md:text-4xl">Painel admin</h1>
            <div className="flex items-center gap-2">
              <span className="rounded-full border border-black/10 bg-white px-3 py-1 text-sm">
                v{appVersion}
              </span>
              <Link
                to="/admin/logs"
                className="inline-flex items-center gap-2 rounded-full bg-[#0c0c0c] px-4 py-2 text-sm font-semibold text-white hover:bg-black"
              >
                <ScrollText className="h-4 w-4" />
                Ver logs
              </Link>
              <Link
                to="/admin/blog"
                className="inline-flex items-center gap-2 rounded-full border border-black/15 bg-white px-4 py-2 text-sm font-semibold hover:bg-[#f4f5f7]"
              >
                Blog
              </Link>
            </div>
          </div>
          <p className="mt-2 text-[#727272]">
            Logado como {profile?.email || user?.email}. Uso da ferramenta sem cartão liberado para admin.
          </p>
        </div>
      </section>

      <div className="mx-auto grid max-w-6xl gap-6 px-6 pb-16 lg:grid-cols-2">
        <motion.form
          onSubmit={onGrant}
          className="rounded-2xl border border-black/8 bg-[#f7f8fa] p-6"
          initial={reduceMotion ? false : { opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.45, ease: easeOutCubic }}
        >
          <div className="mb-4 flex items-center gap-2">
            <Wallet className="h-5 w-5" />
            <h2 className="text-lg font-semibold">Liberar créditos (venda faturada)</h2>
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
          className="rounded-2xl border border-black/8 bg-[#f7f8fa] p-6"
          initial={reduceMotion ? false : { opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.45, ease: easeOutCubic, delay: 0.05 }}
        >
          <div className="mb-4 flex items-center gap-2">
            <KeyRound className="h-5 w-5" />
            <h2 className="text-lg font-semibold">Gerar / definir senha</h2>
          </div>
          <p className="mb-3 text-sm text-[#727272]">
            Defina senha de e-mail/senha para você ou para um cliente. A senha gerada aparece só uma vez.
          </p>
          <label className="mb-3 block text-sm">
            E-mail
            <input
              type="email"
              value={pwdEmail}
              onChange={(e) => setPwdEmail(e.target.value)}
              className="mt-1 w-full rounded-xl border border-black/10 bg-white px-3 py-2.5"
            />
          </label>
          <label className="mb-4 block text-sm">
            Senha manual (opcional)
            <input
              type="text"
              value={pwdManual}
              onChange={(e) => setPwdManual(e.target.value)}
              className="mt-1 w-full rounded-xl border border-black/10 bg-white px-3 py-2.5"
              placeholder="Deixe vazio para gerar automática"
            />
          </label>
          <div className="flex flex-col gap-2 sm:flex-row">
            <button
              type="button"
              disabled={pwdBusy}
              onClick={() => setPassword(true)}
              className="flex-1 rounded-full bg-[#0c0c0c] py-3 text-sm font-semibold text-white hover:bg-black disabled:opacity-50"
            >
              Gerar senha
            </button>
            <button
              type="button"
              disabled={pwdBusy || pwdManual.length < 6}
              onClick={() => setPassword(false)}
              className="flex-1 rounded-full border border-black/15 bg-white py-3 text-sm font-semibold disabled:opacity-50"
            >
              Salvar senha manual
            </button>
          </div>
          {generatedPwd && (
            <div className="mt-4 flex items-center justify-between gap-3 rounded-xl border border-black/10 bg-white px-4 py-3">
              <code className="break-all text-sm font-semibold">{generatedPwd}</code>
              <button type="button" onClick={copyPwd} className="shrink-0 rounded-full bg-[#f4f5f7] p-2" aria-label="Copiar">
                <Copy className="h-4 w-4" />
              </button>
            </div>
          )}
        </motion.div>

        <motion.div
          className="rounded-2xl border border-black/8 bg-white p-6 lg:col-span-2"
          initial={reduceMotion ? false : { opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.45, ease: easeOutCubic, delay: 0.1 }}
        >
          <form onSubmit={onSearch} className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <h2 className="flex items-center gap-2 text-lg font-semibold">
              <Search className="h-5 w-5" />
              Usuários
            </h2>
            <div className="flex gap-2">
              <input
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Buscar e-mail"
                className="rounded-xl border border-black/10 px-3 py-2 text-sm"
              />
              <button type="submit" className="rounded-full bg-[#0c0c0c] px-4 py-2 text-sm font-semibold text-white">
                Buscar
              </button>
            </div>
          </form>
          <div className="overflow-x-auto">
            <table className="w-full min-w-[640px] text-left text-sm">
              <thead className="text-[#727272]">
                <tr>
                  <th className="pb-2 font-medium">E-mail</th>
                  <th className="pb-2 font-medium">Papel</th>
                  <th className="pb-2 font-medium">Disponível</th>
                  <th className="pb-2 font-medium">Total</th>
                  <th className="pb-2 font-medium">Ação</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-black/8">
                {users.map((u) => (
                  <tr key={u.id}>
                    <td className="py-3">{u.email}</td>
                    <td className="py-3">{u.role || 'user'}</td>
                    <td className="py-3">{u.available_mb} MB</td>
                    <td className="py-3">{u.total_credits_mb} MB</td>
                    <td className="py-3">
                      <button
                        type="button"
                        className="text-sm font-semibold underline"
                        onClick={() => {
                          setGrantEmail(u.email)
                          setPwdEmail(u.email)
                        }}
                      >
                        Selecionar
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {users.length === 0 && <p className="py-6 text-center text-[#727272]">Nenhum usuário encontrado.</p>}
          </div>
        </motion.div>

        <motion.div
          className="rounded-2xl border border-black/8 bg-white p-6 lg:col-span-2"
          initial={reduceMotion ? false : { opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.45, ease: easeOutCubic, delay: 0.12 }}
        >
          <div className="mb-1 flex flex-wrap items-center justify-between gap-2">
            <h2 className="flex items-center gap-2 text-lg font-semibold">
              <Undo2 className="h-5 w-5" />
              Financeiro — compras e reembolsos
            </h2>
            <button
              type="button"
              onClick={() => loadTransactions().catch(() => toast.error('Falha ao atualizar'))}
              className="rounded-full border border-black/15 px-3 py-1.5 text-sm font-semibold hover:bg-[#f4f5f7]"
            >
              Atualizar
            </button>
          </div>
          <p className="mb-4 text-sm text-[#727272]">
            Cartão/boleto/débito: devolve valor − taxa. PIX: devolve valor pago. Faturado: só estorna créditos.
          </p>
          <div className="overflow-x-auto">
            <table className="w-full min-w-[720px] text-left text-sm">
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
                        </p>
                        <p className="text-xs text-[#9b9b9b]">{tx.payment_id}</p>
                      </td>
                      <td className="py-3 pr-3">R$ {Number(tx.amount_brl).toFixed(2)}</td>
                      <td className="py-3 pr-3">R$ {Number(tx.fee_brl || 0).toFixed(2)}</td>
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
              <p className="py-6 text-center text-[#727272]">Nenhuma compra registrada.</p>
            )}
          </div>
        </motion.div>

        <motion.div
          className="rounded-2xl border border-black/8 bg-white p-6 lg:col-span-2"
          initial={reduceMotion ? false : { opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.45, ease: easeOutCubic, delay: 0.15 }}
        >
          <h2 className="mb-4 text-lg font-semibold">Histórico de liberações</h2>
          <div className="divide-y divide-black/8">
            {grants.map((g) => (
              <div key={g.id} className="flex flex-col gap-1 py-3 text-sm sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <p className="font-medium">{g.user_email}</p>
                  <p className="text-[#727272]">
                    {g.credits_mb} MB · R$ {Number(g.amount_brl).toFixed(2)}
                    {g.note ? ` · ${g.note}` : ''}
                  </p>
                </div>
                <p className="text-[#9b9b9b]">
                  {new Date(g.created_at).toLocaleString('pt-BR')} · por {g.granted_by_email || 'admin'}
                </p>
              </div>
            ))}
            {grants.length === 0 && <p className="py-6 text-center text-[#727272]">Nenhuma liberação ainda.</p>}
          </div>
        </motion.div>

        <motion.div
          className="rounded-2xl border border-black/8 bg-white p-6 lg:col-span-2"
          initial={reduceMotion ? false : { opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.45, ease: easeOutCubic, delay: 0.2 }}
        >
          <h2 className="mb-1 flex items-center gap-2 text-lg font-semibold">
            <Globe className="h-5 w-5" />
            Uso por IP (hoje)
          </h2>
          <p className="mb-4 text-sm text-[#727272]">
            Free: até 1 separação/IP · Ferramentas: até 2 usos/IP. Conta com créditos ou admin não entra nesse limite.
          </p>
          <div className="divide-y divide-black/8">
            {ipUsage.map((item) => (
              <div
                key={`${item.ip}-${item.usage_date}`}
                className="flex flex-col gap-1 py-3 text-sm sm:flex-row sm:items-center sm:justify-between"
              >
                <div>
                  <p className="font-medium">{item.ip}</p>
                  <p className="text-[#727272]">
                    Free {item.free_process_count}/1 · Ferramentas {item.tool_use_count}/2
                    {item.last_email ? ` · último: ${item.last_email}` : ''}
                  </p>
                </div>
                <p className="text-[#9b9b9b]">
                  {item.updated_at ? new Date(item.updated_at).toLocaleString('pt-BR') : item.usage_date}
                </p>
              </div>
            ))}
            {ipUsage.length === 0 && (
              <p className="py-6 text-center text-[#727272]">Nenhum uso gratuito/ferramenta por IP hoje.</p>
            )}
          </div>
        </motion.div>
      </div>
      <SiteFooter />
    </div>
  )
}
