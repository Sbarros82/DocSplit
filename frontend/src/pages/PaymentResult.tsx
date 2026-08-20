import { useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { motion, useReducedMotion } from 'motion/react'
import { ArrowRight, CheckCircle, Clock, XCircle } from 'lucide-react'
import { Header } from '@/components/Header'
import { useAuth } from '@/components/AuthProvider'

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000'

type ResultType = 'success' | 'failure' | 'pending'

const easeOutCubic = [0.215, 0.61, 0.355, 1] as const

const CONFIG: Record<
  ResultType,
  {
    icon: typeof CheckCircle
    title: string
    description: string
    iconWrap: string
    iconColor: string
  }
> = {
  success: {
    icon: CheckCircle,
    title: 'Pagamento aprovado!',
    description: 'Seus créditos foram adicionados à sua conta. Você já pode usar o DocSplit.',
    iconWrap: 'bg-[#b7ff33]',
    iconColor: 'text-[#0c0c0c]',
  },
  failure: {
    icon: XCircle,
    title: 'Pagamento não aprovado',
    description: 'O pagamento não foi concluído. Tente novamente ou escolha outro método de pagamento.',
    iconWrap: 'bg-[#0c0c0c]',
    iconColor: 'text-[#b7ff33]',
  },
  pending: {
    icon: Clock,
    title: 'Pagamento pendente',
    description: 'Estamos aguardando a confirmação do pagamento. Seus créditos serão liberados assim que aprovado.',
    iconWrap: 'bg-[#f4f5f7]',
    iconColor: 'text-[#0c0c0c]',
  },
}

export function PaymentResult({ type }: { type: ResultType }) {
  const [searchParams] = useSearchParams()
  const { refreshProfile, getAccessToken } = useAuth()
  const reduceMotion = useReducedMotion()
  const paymentId = searchParams.get('payment_id')
  const status = searchParams.get('status')
  const [resolvedType, setResolvedType] = useState<ResultType>(type)
  const [syncNote, setSyncNote] = useState<string | null>(null)
  const { icon: Icon, title, description, iconWrap, iconColor } = CONFIG[resolvedType]

  useEffect(() => {
    let cancelled = false

    const syncPayment = async () => {
      if (!paymentId || paymentId === 'null' || type === 'failure') {
        if (type === 'success' || type === 'pending') {
          await refreshProfile()
        }
        return
      }

      try {
        const token = await getAccessToken().catch(() => null)
        if (!token) {
          await refreshProfile()
          return
        }

        const response = await fetch(`${BACKEND_URL}/api/payment/confirm/${paymentId}`, {
          method: 'POST',
          headers: { Authorization: `Bearer ${token}` },
        })
        const data = await response.json().catch(() => ({}))
        if (cancelled) return

        if (response.ok && data.status === 'approved') {
          setResolvedType('success')
          setSyncNote(
            data.already_credited
              ? 'Créditos já estavam liberados nesta conta.'
              : data.credited
                ? `${data.credits_mb} MB liberados na sua conta.`
                : 'Pagamento aprovado.',
          )
        } else if (response.ok && (data.status === 'pending' || data.status === 'in_process')) {
          setResolvedType('pending')
        }
      } catch {
        // Mantém a tela original; o webhook ainda pode liberar depois.
      } finally {
        if (!cancelled) {
          await refreshProfile()
        }
      }
    }

    void syncPayment()
    return () => {
      cancelled = true
    }
  }, [paymentId, type, refreshProfile, getAccessToken])

  return (
    <div className="min-h-screen bg-white text-[#0c0c0c]">
      <Header />

      <section className="relative overflow-hidden px-6 py-20 md:py-28">
        <div className="pointer-events-none absolute inset-0" aria-hidden>
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_right,rgba(183,255,51,0.22),transparent_42%)]" />
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_bottom_left,rgba(183,255,51,0.1),transparent_40%)]" />
          {!reduceMotion && (
            <>
              <motion.div
                className="absolute -right-16 top-10 h-72 w-72 rounded-full bg-[#b7ff33]/25 blur-3xl"
                animate={{ x: [0, -30, 15, 0], y: [0, 20, -10, 0] }}
                transition={{ duration: 14, repeat: Infinity, ease: 'easeInOut' }}
              />
              <motion.div
                className="absolute -left-20 bottom-0 h-64 w-64 rounded-full bg-[#d4ff7a]/20 blur-3xl"
                animate={{ x: [0, 40, -20, 0], y: [0, -25, 10, 0] }}
                transition={{ duration: 16, repeat: Infinity, ease: 'easeInOut' }}
              />
            </>
          )}
        </div>

        <motion.div
          className="relative mx-auto max-w-lg text-center"
          initial={reduceMotion ? false : { opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, ease: easeOutCubic }}
        >
          <motion.div
            className={`mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-full ${iconWrap}`}
            initial={reduceMotion ? false : { scale: 0.7, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ duration: 0.45, ease: easeOutCubic, delay: 0.08 }}
          >
            <Icon className={`h-8 w-8 ${iconColor}`} />
          </motion.div>

          <h1 className="text-3xl font-semibold tracking-tight md:text-4xl">{title}</h1>
          <p className="mx-auto mt-4 max-w-md text-[#727272]">{description}</p>
          {syncNote ? <p className="mx-auto mt-3 max-w-md text-sm font-medium text-[#0c0c0c]">{syncNote}</p> : null}

          {(paymentId && paymentId !== 'null') || (status && status !== 'null') ? (
            <div className="mt-6 space-y-1 text-sm text-[#9b9b9b]">
              {paymentId && paymentId !== 'null' && <p>ID do pagamento: {paymentId}</p>}
              <p>Status: {resolvedType === 'success' ? 'approved' : status && status !== 'null' ? status : resolvedType}</p>
            </div>
          ) : null}

          <div className="mt-10 flex flex-col items-center justify-center gap-3 sm:flex-row">
            <Link
              to="/dashboard"
              className="inline-flex items-center gap-2 rounded-full bg-[#b7ff33] px-7 py-3.5 text-base font-semibold text-[#0c0c0c] shadow-[0_8px_24px_rgba(183,255,51,0.35)] transition-colors hover:bg-[#c8ff66]"
            >
              Ir para o Painel
              <ArrowRight className="h-4 w-4" />
            </Link>
            {resolvedType === 'failure' && (
              <Link
                to="/pricing"
                className="inline-flex items-center gap-2 rounded-full border border-black/15 bg-white/80 px-7 py-3.5 text-base font-semibold text-[#0c0c0c] backdrop-blur-sm hover:bg-[#f4f5f7]"
              >
                Tentar novamente
              </Link>
            )}
            {resolvedType === 'success' && (
              <Link
                to="/upload"
                className="inline-flex items-center gap-2 rounded-full border border-black/15 bg-white/80 px-7 py-3.5 text-base font-semibold text-[#0c0c0c] backdrop-blur-sm hover:bg-[#f4f5f7]"
              >
                Separar PDF
              </Link>
            )}
          </div>
        </motion.div>
      </section>
    </div>
  )
}
