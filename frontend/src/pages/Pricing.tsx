import { useState } from 'react'
import { AnimatePresence, motion, useReducedMotion } from 'motion/react'
import { Check, ChevronDown } from 'lucide-react'
import { toast } from 'sonner'
import { useAuth } from '@/components/AuthProvider'
import { Header } from '@/components/Header'
import { SiteFooter } from '@/components/SiteFooter'

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000'

/** Originkit ease — features-01 / process-01 */
const easeOutCubic = [0.215, 0.61, 0.355, 1] as const

const cardReveal = {
  hidden: { opacity: 0, y: 28 },
  show: { opacity: 1, y: 0 },
}

const cardStagger = {
  hidden: {},
  show: {
    transition: { staggerChildren: 0.08, delayChildren: 0.06 },
  },
}

const packages = [
  {
    id: 'basic',
    name: 'Básico',
    price: 5,
    credits: 50,
    description: 'Ideal para uso ocasional',
    features: [
      '50 MB de créditos',
      'Válido por 90 dias',
      'OCR completo',
      'Até 200 páginas por arquivo',
      "Sem marca d'água",
    ],
  },
  {
    id: 'plus',
    name: 'Plus',
    price: 15,
    credits: 200,
    description: 'Bônus de 33%',
    popular: true,
    features: [
      '200 MB de créditos',
      'Válido por 90 dias',
      'OCR completo',
      'Até 200 páginas por arquivo',
      "Sem marca d'água",
      'Suporte prioritário',
    ],
  },
  {
    id: 'pro',
    name: 'Pro',
    price: 30,
    credits: 500,
    description: 'Bônus de 67%',
    features: [
      '500 MB de créditos',
      'Válido por 90 dias',
      'OCR completo',
      'Até 200 páginas por arquivo',
      "Sem marca d'água",
      'Suporte prioritário',
      'Acesso antecipado a novos recursos',
    ],
  },
  {
    id: 'premium',
    name: 'Premium',
    price: 50,
    credits: 1000,
    description: 'Bônus de 100%',
    features: [
      '1 GB de créditos',
      'Válido por 90 dias',
      'OCR completo',
      'Até 200 páginas por arquivo',
      "Sem marca d'água",
      'Suporte prioritário',
      'Acesso antecipado a novos recursos',
      'API disponível',
    ],
  },
]

const FAQS = [
  {
    q: 'Como funcionam os créditos?',
    a: 'Cada arquivo processado desconta o tamanho em MB do seu saldo. Um PDF de 5 MB consome 5 MB de créditos.',
  },
  {
    q: 'Os créditos expiram?',
    a: 'Sim, após 90 dias da compra. Você receberá avisos antes de expirar.',
  },
  {
    q: 'Posso usar sem pagar?',
    a: 'Sim! Você tem 3 uploads gratuitos por dia (máx. 2 MB cada, 10 páginas), com login.',
  },
  {
    q: 'Quais formas de pagamento?',
    a: 'PIX (instantâneo), cartão de crédito/débito e boleto via Mercado Pago.',
  },
]

export function Pricing() {
  const { user, getAccessToken } = useAuth()
  const [loading, setLoading] = useState<string | null>(null)
  const reduceMotion = useReducedMotion()

  const handleCheckout = async (packageId: string) => {
    if (!user) {
      toast.error('Faça login para continuar')
      window.location.href = '/login?next=' + encodeURIComponent('/pricing')
      return
    }

    setLoading(packageId)

    try {
      const token = await getAccessToken().catch(() => null)
      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
      }
      if (token) {
        headers.Authorization = `Bearer ${token}`
      }

      const response = await fetch(`${BACKEND_URL}/api/payment/create-checkout`, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          user_id: user.id,
          user_email: user.email,
          package_id: packageId,
        }),
      })

      if (!response.ok) {
        const error = await response.json().catch(() => ({}))
        const detail = typeof error.detail === 'string' ? error.detail : 'Erro ao criar checkout'
        throw new Error(detail)
      }

      const data = await response.json()
      window.location.href = data.checkout_url
    } catch (error) {
      console.error(error)
      toast.error(error instanceof Error ? error.message : 'Erro ao processar pagamento. Tente novamente.')
      setLoading(null)
    }
  }

  return (
    <div className="min-h-screen bg-white text-[#0c0c0c]">
      <Header />

      <section className="relative overflow-hidden px-6 pb-10 pt-14 md:pt-16">
        <div className="pointer-events-none absolute inset-0" aria-hidden>
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_right,rgba(183,255,51,0.22),transparent_42%)]" />
          {!reduceMotion && (
            <>
              <motion.div
                className="absolute -right-16 top-0 h-72 w-72 rounded-full bg-[#b7ff33]/25 blur-3xl"
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

        <div className="relative mx-auto max-w-3xl text-center">
          <motion.p
            className="mb-4 text-sm font-medium text-[#727272]"
            initial={reduceMotion ? false : { opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.45, ease: easeOutCubic }}
          >
            Preços
          </motion.p>
          <motion.h1
            className="text-4xl font-semibold tracking-tight md:text-5xl"
            initial={reduceMotion ? false : { opacity: 0, y: 18 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, ease: easeOutCubic, delay: 0.05 }}
          >
            Escolha seu pacote
          </motion.h1>
          <motion.p
            className="mt-4 text-lg text-[#727272]"
            initial={reduceMotion ? false : { opacity: 0, y: 18 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, ease: easeOutCubic, delay: 0.1 }}
          >
            Pague apenas pelo que usar. Créditos válidos por 90 dias.
          </motion.p>
        </div>
      </section>

      <section className="px-6 pb-16">
        <motion.div
          className="mx-auto grid max-w-7xl gap-5 md:grid-cols-2 lg:grid-cols-4"
          variants={cardStagger}
          initial={reduceMotion ? false : 'hidden'}
          whileInView="show"
          viewport={{ once: true, amount: 0.15 }}
        >
          {packages.map((pkg) => (
            <motion.article
              key={pkg.id}
              variants={cardReveal}
              transition={{ duration: 0.5, ease: easeOutCubic }}
              whileHover={
                reduceMotion
                  ? undefined
                  : { y: -6, transition: { duration: 0.25, ease: easeOutCubic } }
              }
              className={`relative rounded-2xl border p-6 will-change-transform ${
                pkg.popular
                  ? 'border-[#0c0c0c] bg-[#0c0c0c] text-white shadow-[0_16px_40px_rgba(12,12,12,0.18)]'
                  : 'border-black/8 bg-[#f7f8fa]'
              }`}
            >
              {pkg.popular && (
                <span className="absolute -top-3 left-1/2 -translate-x-1/2 rounded-full bg-[#b7ff33] px-3 py-1 text-xs font-semibold text-[#0c0c0c]">
                  Mais popular
                </span>
              )}

              <h3 className="text-2xl font-semibold">{pkg.name}</h3>
              <p className={`mt-1 text-sm ${pkg.popular ? 'text-[#b8b8b8]' : 'text-[#727272]'}`}>
                {pkg.description}
              </p>

              <div className="mt-5 mb-6">
                <span className="text-4xl font-semibold">R$ {pkg.price}</span>
                <span className={`ml-2 text-sm ${pkg.popular ? 'text-[#b8b8b8]' : 'text-[#727272]'}`}>
                  / {pkg.credits} MB
                </span>
              </div>

              <button
                type="button"
                onClick={() => handleCheckout(pkg.id)}
                disabled={loading !== null}
                className={`mb-6 w-full rounded-full py-3 text-sm font-semibold transition ${
                  pkg.popular
                    ? 'bg-[#b7ff33] text-[#0c0c0c] hover:bg-[#c8ff66]'
                    : 'bg-[#0c0c0c] text-white hover:bg-black'
                } ${loading === pkg.id ? 'cursor-wait opacity-50' : ''} disabled:cursor-not-allowed`}
              >
                {loading === pkg.id ? 'Processando...' : 'Adquirir agora'}
              </button>

              <ul className="space-y-3">
                {pkg.features.map((feature) => (
                  <li key={feature} className="flex items-start gap-2 text-sm">
                    <Check
                      className={`mt-0.5 h-4 w-4 shrink-0 ${
                        pkg.popular ? 'text-[#b7ff33]' : 'text-[#0c0c0c]'
                      }`}
                    />
                    <span className={pkg.popular ? 'text-[#d4d4d4]' : 'text-[#555]'}>{feature}</span>
                  </li>
                ))}
              </ul>
            </motion.article>
          ))}
        </motion.div>
      </section>

      <section className="border-t border-black/5 bg-[#f7f8fa] px-6 py-16">
        <div className="mx-auto max-w-3xl">
          <motion.h2
            className="text-center text-3xl font-semibold tracking-tight"
            initial={reduceMotion ? false : { opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, amount: 0.6 }}
            transition={{ duration: 0.5, ease: easeOutCubic }}
          >
            Perguntas frequentes
          </motion.h2>
          <FaqList reduceMotion={!!reduceMotion} />
        </div>
      </section>

      <SiteFooter />
    </div>
  )
}

function FaqList({ reduceMotion }: { reduceMotion: boolean }) {
  const [openIndex, setOpenIndex] = useState<number | null>(0)

  return (
    <motion.div
      className="mt-10 divide-y divide-black/10"
      variants={cardStagger}
      initial={reduceMotion ? false : 'hidden'}
      whileInView="show"
      viewport={{ once: true, amount: 0.2 }}
    >
      {FAQS.map((item, index) => {
        const isOpen = openIndex === index
        return (
          <motion.div
            key={item.q}
            variants={cardReveal}
            transition={{ duration: 0.45, ease: easeOutCubic }}
            className="py-1"
          >
            <button
              type="button"
              aria-expanded={isOpen}
              onClick={() => setOpenIndex(isOpen ? null : index)}
              className="flex w-full items-center justify-between gap-4 py-4 text-left text-lg font-medium transition-colors hover:text-[#0c0c0c]/80"
            >
              <span>{item.q}</span>
              <motion.span
                animate={{ rotate: isOpen ? 180 : 0 }}
                transition={{ duration: reduceMotion ? 0 : 0.28, ease: easeOutCubic }}
                className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-white"
              >
                <ChevronDown className="h-4 w-4 text-[#0c0c0c]" />
              </motion.span>
            </button>
            <AnimatePresence initial={false}>
              {isOpen && (
                <motion.div
                  key="content"
                  initial={reduceMotion ? false : { height: 0, opacity: 0 }}
                  animate={{ height: 'auto', opacity: 1 }}
                  exit={reduceMotion ? undefined : { height: 0, opacity: 0 }}
                  transition={{ duration: 0.35, ease: easeOutCubic }}
                  className="overflow-hidden"
                >
                  <p className="pb-5 pr-12 text-[#727272]">{item.a}</p>
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>
        )
      })}
    </motion.div>
  )
}
