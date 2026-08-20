import { useState } from 'react'
import { Link } from 'react-router-dom'
import {
  ArrowRight,
  Check,
  ChevronDown,
  FileText,
  FolderKanban,
  ScanText,
  Shield,
  Sparkles,
  Zap,
} from 'lucide-react'
import { AnimatePresence, motion, useReducedMotion } from 'motion/react'
import { Header } from '@/components/Header'
import { SiteFooter } from '@/components/SiteFooter'

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

const FEATURES = [
  { title: 'Separação automática', desc: 'Um PDF misturado vira arquivos individuais, nomeados e prontos para arquivar.' },
  { title: 'OCR em português', desc: 'Lê boletos, PIX, NF-e e DARF mesmo quando o documento veio do scanner.' },
  { title: 'Central de PDF', desc: 'Junte, comprima, gire, proteja e numere páginas no navegador.' },
  { title: 'Correção pontual', desc: 'Ajuste um trecho do PDF sem redesenhar a página inteira.' },
  { title: 'Índice Excel', desc: 'Cada lote gera um índice com o que foi encontrado. Nada some.' },
  { title: 'Privacidade', desc: 'O arquivo é processado e apagado. Sem fila infinita no servidor.' },
]

const HIGHLIGHTS = [
  { title: 'Fluxo ágil', desc: 'Do upload ao ZIP em segundos, sem instalar programa.' },
  { title: 'Colaboração real', desc: 'Contador e empresa usam o mesmo padrão de nomes e pastas.' },
  { title: 'Painel de créditos', desc: 'Veja usos do dia, histórico de jobs e pacotes quando precisar.' },
  { title: 'Encaixa no que você já usa', desc: 'Baixe, envie ao cliente ou jogue no Drive. Sem troca de ferramenta.' },
]

const BENEFITS = [
  { title: 'Mais rapidez', desc: 'Horas de separação manual viram um clique.' },
  { title: 'Menos erro', desc: 'A IA classifica o tipo do documento; você só revisa o que marcar dúvida.' },
  { title: 'Visão na hora', desc: 'Pré-visualize páginas antes de juntar, comprimir ou girar.' },
  { title: 'Entrega mais cedo', desc: 'Lote do cliente sai organizado no mesmo expediente.' },
  { title: 'Rastro claro', desc: 'ZIP + Excel mostram o que entrou e o que saiu.' },
  { title: 'Cresce com você', desc: 'Comece grátis. Créditos quando o volume subir.' },
]

const FAQS = [
  { q: 'Preciso de cartão para testar?', a: 'Não. São 3 arquivos por dia no plano gratuito, sem cadastro de cartão.' },
  { q: 'Funciona com PDF escaneado?', a: 'Sim. O OCR lê português e classifica boleto, PIX, NF-e, DARF e outros tipos comuns.' },
  { q: 'Os arquivos ficam guardados?', a: 'Não. O processamento é temporário: o arquivo entra, sai organizado e é removido.' },
  { q: 'Qual a diferença da Central de PDF?', a: 'A home separa documentos misturados. A Central junta, comprime, gira, protege e corrige texto.' },
  { q: 'Posso pagar faturado (empresa)?', a: 'Sim. Escritórios e empresas podem pedir créditos com nota/boleto. Fale no WhatsApp e liberamos na sua conta após a confirmação.' },
]

const WHATSAPP_FATURADO =
  'https://wa.me/5582982218199?text=' +
  encodeURIComponent('Olá! Quero créditos DocSplit no modelo faturado (empresa).')

const WHATSAPP_URL =
  'https://wa.me/5582982218199?text=' +
  encodeURIComponent('Olá! Quero saber mais sobre o DocSplit.')

export function Landing() {
  const reduceMotion = useReducedMotion()

  return (
    <div className="min-h-screen bg-white text-[#0c0c0c]">
      <Header />

      <section className="relative overflow-hidden px-6 pb-20 pt-16 md:pt-24">
        <HeroMotionBackground reduceMotion={!!reduceMotion} />
        <div className="relative mx-auto max-w-5xl text-center">
          <p className="mb-6 inline-flex items-center gap-2 rounded-full border border-black/10 bg-white/80 px-4 py-1.5 text-sm text-[#727272] backdrop-blur-sm">
            <span className="relative flex h-2 w-2">
              {!reduceMotion && (
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-[#b7ff33] opacity-70" />
              )}
              <span className="relative inline-flex h-2 w-2 rounded-full bg-[#b7ff33]" />
            </span>
            3 arquivos grátis por dia · sem cartão
          </p>
          <h1 className="text-5xl font-semibold tracking-tight md:text-7xl">
            Organize o escritório
            <span className="mt-2 block">com PDFs no lugar certo.</span>
          </h1>
          <p className="mx-auto mt-6 max-w-2xl text-lg text-[#727272] md:text-xl">
            O DocSplit identifica boletos, PIX, NF-e, DARF e guias. Um PDF de 50 páginas vira dezenas de arquivos organizados.
          </p>
          <div className="mt-10 flex flex-col items-center justify-center gap-3 sm:flex-row">
            <motion.div
              className="relative"
              animate={
                reduceMotion
                  ? undefined
                  : {
                      scale: [1, 1.03, 1],
                    }
              }
              transition={{
                duration: 2.2,
                repeat: Infinity,
                ease: 'easeInOut',
              }}
            >
              {!reduceMotion && (
                <span
                  aria-hidden
                  className="pointer-events-none absolute -inset-1 rounded-full bg-[#b7ff33]/50 blur-md"
                  style={{
                    animation: 'docsplit-cta-glow 2.2s ease-in-out infinite',
                  }}
                />
              )}
              <Link
                to="/upload"
                className="relative z-10 inline-flex items-center gap-2 rounded-full bg-[#b7ff33] px-8 py-3.5 text-base font-semibold text-[#0c0c0c] shadow-[0_8px_24px_rgba(183,255,51,0.45)] transition-colors hover:bg-[#c8ff66]"
              >
                Começar agora
                <ArrowRight className="h-4 w-4" />
              </Link>
            </motion.div>
            <Link
              to="/pricing"
              className="inline-flex items-center gap-2 rounded-full border border-black/15 bg-white/80 px-7 py-3.5 text-base font-semibold text-[#0c0c0c] backdrop-blur-sm hover:bg-[#f4f5f7]"
            >
              Ver preços
            </Link>
          </div>
        </div>
      </section>

      <section className="border-t border-black/5 px-6 py-20">
        <div className="mx-auto max-w-6xl">
          <p className="text-sm font-medium text-[#727272]">Recursos</p>
          <h2 className="mt-2 max-w-xl text-3xl font-semibold tracking-tight md:text-4xl">
            Tudo que um lote de documentos precisa
          </h2>
          <motion.div
            className="mt-12 grid gap-4 sm:grid-cols-2 lg:grid-cols-3"
            variants={cardStagger}
            initial={reduceMotion ? false : 'hidden'}
            whileInView="show"
            viewport={{ once: true, amount: 0.2 }}
          >
            {FEATURES.map((item) => (
              <motion.article
                key={item.title}
                variants={cardReveal}
                transition={{ duration: 0.5, ease: easeOutCubic }}
                whileHover={
                  reduceMotion
                    ? undefined
                    : { y: -6, transition: { duration: 0.25, ease: easeOutCubic } }
                }
                className="rounded-2xl border border-black/8 bg-[#f7f8fa] p-6 will-change-transform [@media(hover:hover)_and_(pointer:fine)]:hover:border-black/15 [@media(hover:hover)_and_(pointer:fine)]:hover:bg-white [@media(hover:hover)_and_(pointer:fine)]:hover:shadow-[0_12px_32px_rgba(12,12,12,0.08)]"
              >
                <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-full bg-[#b7ff33]">
                  <Sparkles className="h-5 w-5 text-[#0c0c0c]" />
                </div>
                <h3 className="text-lg font-semibold">{item.title}</h3>
                <p className="mt-2 text-sm leading-6 text-[#727272]">{item.desc}</p>
              </motion.article>
            ))}
          </motion.div>
        </div>
      </section>

      <section className="px-6 py-20">
        <div className="mx-auto max-w-6xl">
          <p className="text-sm font-medium text-[#727272]">Como funciona</p>
          <h2 className="mt-2 text-3xl font-semibold tracking-tight md:text-4xl">Três passos. ZIP pronto.</h2>
          <div className="mt-12 grid gap-8 md:grid-cols-3">
            <Step icon={FileText} n="01" title="Envie o PDF" text="Arraste o arquivo digitalizado ou o lote misturado do cliente." />
            <Step icon={Zap} n="02" title="Classificação" text="A IA separa PIX, boletos, NF-e, DARF, folha e o que não identificar vai para revisão." />
            <Step icon={Shield} n="03" title="Baixe organizado" text="ZIP com PDFs nomeados e índice Excel. Nenhuma página some." />
          </div>
        </div>
      </section>

      <section className="border-y border-black/5 bg-[#0c0c0c] px-6 py-16 text-white">
        <div className="mx-auto grid max-w-5xl gap-10 text-center sm:grid-cols-3">
          <Stat value="PDF → ZIP" label="Do lote ao arquivo certo" />
          <Stat value="3 / dia" label="Uso grátis, sem cartão" />
          <Stat value="4.9" label="Nota média dos usuários" />
        </div>
      </section>

      <section className="px-6 py-20">
        <div className="mx-auto max-w-6xl">
          <p className="text-sm font-medium text-[#727272]">Destaques</p>
          <h2 className="mt-2 max-w-2xl text-3xl font-semibold tracking-tight md:text-4xl">
            Feito para o ritmo de contador e empresa
          </h2>
          <div className="mt-12 grid gap-4 md:grid-cols-2">
            {HIGHLIGHTS.map((item) => (
              <article key={item.title} className="rounded-2xl border border-black/8 p-7">
                <h3 className="text-xl font-semibold">{item.title}</h3>
                <p className="mt-2 text-[#727272]">{item.desc}</p>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section className="bg-[#f7f8fa] px-6 py-20">
        <div className="mx-auto max-w-6xl">
          <p className="text-sm font-medium text-[#727272]">Vantagens</p>
          <h2 className="mt-2 text-3xl font-semibold tracking-tight md:text-4xl">Por que o DocSplit</h2>
          <motion.div
            className="mt-12 grid gap-8 sm:grid-cols-2 lg:grid-cols-3"
            variants={cardStagger}
            initial={reduceMotion ? false : 'hidden'}
            whileInView="show"
            viewport={{ once: true, amount: 0.25 }}
          >
            {BENEFITS.map((item) => (
              <motion.article
                key={item.title}
                variants={cardReveal}
                transition={{ duration: 0.5, ease: easeOutCubic }}
                whileHover={
                  reduceMotion
                    ? undefined
                    : { y: -4, transition: { duration: 0.25, ease: easeOutCubic } }
                }
                className="will-change-transform"
              >
                <h3 className="text-lg font-semibold">{item.title}</h3>
                <p className="mt-2 text-sm leading-6 text-[#727272]">{item.desc}</p>
              </motion.article>
            ))}
          </motion.div>
        </div>
      </section>

      <section className="px-6 py-20">
        <div className="mx-auto max-w-6xl">
          <h2 className="text-center text-3xl font-semibold tracking-tight md:text-4xl">Perfeito para</h2>
          <div className="mt-12 grid gap-6 md:grid-cols-2">
            <Audience
              icon={FolderKanban}
              title="Contadores"
              text="Organize documentos de dezenas de clientes em minutos. NF-e, DARF e folhas saem no padrão certo."
              points={['Horas a menos de trabalho manual', 'Menos erro de arquivamento']}
            />
            <Audience
              icon={ScanText}
              title="Empresas"
              text="Separe boletos, comprovantes PIX e faturas do banco ou do scanner, em lote."
              points={['Até 200 páginas por arquivo no plano pago', 'API quando o volume crescer']}
            />
          </div>
        </div>
      </section>

      <section className="border-y border-black/5 bg-[#f7f8fa] px-6 py-20">
        <div className="mx-auto grid max-w-6xl items-center gap-10 md:grid-cols-2">
          <div>
            <p className="text-sm font-medium text-[#727272]">Para empresas</p>
            <h2 className="mt-2 text-3xl font-semibold tracking-tight md:text-4xl">
              Créditos no modelo faturado
            </h2>
            <p className="mt-4 text-[#727272]">
              Contabilidade e empresas podem comprar volume com nota/boleto. Sem cartão no checkout:
              alinhamos o pacote, emitimos a cobrança e liberamos os créditos na conta.
            </p>
            <ul className="mt-5 space-y-2 text-sm text-[#555]">
              <li className="flex items-start gap-2">
                <Check className="mt-0.5 h-4 w-4 shrink-0" />
                Ideal para escritórios com vários usuários
              </li>
              <li className="flex items-start gap-2">
                <Check className="mt-0.5 h-4 w-4 shrink-0" />
                Liberação manual após confirmação do pedido
              </li>
              <li className="flex items-start gap-2">
                <Check className="mt-0.5 h-4 w-4 shrink-0" />
                Suporte direto pelo WhatsApp
              </li>
            </ul>
          </div>
          <div className="rounded-2xl border border-black/8 bg-white p-8">
            <p className="text-sm font-medium text-[#727272]">Fale com a gente</p>
            <h3 className="mt-2 text-2xl font-semibold">Quero faturado</h3>
            <p className="mt-2 text-sm text-[#727272]">
              Conte o volume aproximado de PDFs/mês e o e-mail da conta DocSplit.
            </p>
            <a
              href={WHATSAPP_FATURADO}
              target="_blank"
              rel="noopener noreferrer"
              className="mt-6 inline-flex items-center gap-2 rounded-full bg-[#0c0c0c] px-6 py-3 text-sm font-semibold text-white hover:bg-black"
            >
              Solicitar no WhatsApp
              <ArrowRight className="h-4 w-4" />
            </a>
            <p className="mt-4 text-xs text-[#9b9b9b]">
              Ou veja os pacotes à vista em{' '}
              <Link to="/pricing" className="underline underline-offset-2 hover:text-[#0c0c0c]">
                Preços
              </Link>
              .
            </p>
          </div>
        </div>
      </section>

      <section className="border-t border-black/5 px-6 py-20">
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

      <section className="px-6 pb-20">
        <div className="mx-auto max-w-5xl rounded-[28px] bg-[#0c0c0c] px-8 py-16 text-center text-white">
          <p className="inline-flex items-center gap-2 rounded-full bg-[#b7ff33] px-3 py-1 text-sm font-semibold text-[#0c0c0c]">
            Comece grátis
          </p>
          <h2 className="mt-5 text-3xl font-semibold tracking-tight md:text-5xl">Separe o primeiro PDF hoje</h2>
          <p className="mx-auto mt-4 max-w-xl text-[#b8b8b8]">
            3 arquivos por dia, sem cartão. Upgrade só quando o volume pedir.
          </p>
          <Link
            to="/upload"
            className="mt-8 inline-flex items-center gap-2 rounded-full bg-[#b7ff33] px-8 py-3.5 text-base font-semibold text-[#0c0c0c] hover:bg-[#c8ff66]"
          >
            Separar PDF
            <ArrowRight className="h-4 w-4" />
          </Link>
        </div>
      </section>

      <SiteFooter />

      <WhatsAppFloat reduceMotion={!!reduceMotion} />
    </div>
  )
}

function HeroMotionBackground({ reduceMotion }: { reduceMotion: boolean }) {
  return (
    <div className="pointer-events-none absolute inset-0 overflow-hidden" aria-hidden>
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_right,rgba(183,255,51,0.22),transparent_42%)]" />
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_bottom_left,rgba(183,255,51,0.12),transparent_40%)]" />

      {reduceMotion ? (
        <>
          <div className="absolute -right-16 top-8 h-72 w-72 rounded-full bg-[#b7ff33]/25 blur-3xl" />
          <div className="absolute -left-20 bottom-0 h-64 w-64 rounded-full bg-[#b7ff33]/15 blur-3xl" />
        </>
      ) : (
        <>
          <motion.div
            className="absolute -right-20 -top-10 h-[28rem] w-[28rem] rounded-full bg-[#b7ff33]/30 blur-3xl"
            animate={{ x: [0, -40, 20, 0], y: [0, 30, -20, 0], scale: [1, 1.12, 0.95, 1] }}
            transition={{ duration: 14, repeat: Infinity, ease: 'easeInOut' }}
          />
          <motion.div
            className="absolute -left-24 bottom-[-4rem] h-80 w-80 rounded-full bg-[#d4ff7a]/35 blur-3xl"
            animate={{ x: [0, 50, -25, 0], y: [0, -35, 15, 0], scale: [1, 0.9, 1.1, 1] }}
            transition={{ duration: 18, repeat: Infinity, ease: 'easeInOut' }}
          />
          <motion.div
            className="absolute left-1/2 top-1/3 h-56 w-56 -translate-x-1/2 rounded-full bg-[#b7ff33]/20 blur-2xl"
            animate={{ x: [0, 60, -40, 0], y: [0, -25, 40, 0], opacity: [0.35, 0.55, 0.3, 0.35] }}
            transition={{ duration: 12, repeat: Infinity, ease: 'easeInOut' }}
          />
          {[
            { left: '18%', top: '22%', delay: 0 },
            { left: '72%', top: '18%', delay: 0.8 },
            { left: '58%', top: '62%', delay: 1.4 },
            { left: '28%', top: '70%', delay: 2.1 },
            { left: '84%', top: '48%', delay: 0.4 },
          ].map((dot) => (
            <motion.span
              key={`${dot.left}-${dot.top}`}
              className="absolute h-1.5 w-1.5 rounded-full bg-[#0c0c0c]/25"
              style={{ left: dot.left, top: dot.top }}
              animate={{ y: [0, -14, 0], opacity: [0.2, 0.55, 0.2] }}
              transition={{
                duration: 4.5,
                repeat: Infinity,
                ease: 'easeInOut',
                delay: dot.delay,
              }}
            />
          ))}
        </>
      )}
    </div>
  )
}

function WhatsAppFloat({ reduceMotion }: { reduceMotion: boolean }) {
  return (
    <a
      href={WHATSAPP_URL}
      target="_blank"
      rel="noopener noreferrer"
      aria-label="Falar no WhatsApp"
      className="fixed bottom-5 right-5 z-50 flex h-14 w-14 items-center justify-center rounded-full bg-[#25D366] text-white shadow-[0_10px_28px_rgba(37,211,102,0.45)] transition-transform hover:scale-105 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#25D366] md:bottom-7 md:right-7"
    >
      {!reduceMotion && (
        <span
          aria-hidden
          className="absolute inset-0 rounded-full bg-[#25D366]/40"
          style={{ animation: 'docsplit-wa-ping 2s ease-out infinite' }}
        />
      )}
      <svg viewBox="0 0 32 32" className="relative z-10 h-7 w-7" fill="currentColor" aria-hidden>
        <path d="M16.004 3.2C9.37 3.2 4 8.57 4 15.204c0 2.206.59 4.27 1.62 6.05L4 28.8l7.74-1.59a11.95 11.95 0 0 0 4.264.78C22.63 27.99 28 22.62 28 15.986 28 9.35 22.63 3.2 16.004 3.2zm6.95 17.11c-.29.82-1.7 1.51-2.37 1.6-.61.09-1.38.12-2.23-.14-.51-.16-1.17-.38-2.02-.74-3.55-1.54-5.86-5.13-6.04-5.37-.18-.24-1.45-1.93-1.45-3.68s.92-2.61 1.25-2.97c.33-.36.72-.45.96-.45h.7c.22 0 .52-.08.81.62.29.71.99 2.44 1.08 2.62.09.18.15.39.03.62-.12.24-.18.39-.36.6-.18.21-.38.47-.54.63-.18.18-.36.37-.15.72.21.36.93 1.53 2 2.48 1.37 1.22 2.53 1.6 2.89 1.78.36.18.57.15.78-.09.21-.24.9-1.05 1.14-1.41.24-.36.48-.3.81-.18.33.12 2.1.99 2.46 1.17.36.18.6.27.69.42.09.15.09.87-.2 1.69z" />
      </svg>
    </a>
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
                className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-[#f4f5f7]"
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

function Step({
  icon: Icon,
  n,
  title,
  text,
}: {
  icon: typeof FileText
  n: string
  title: string
  text: string
}) {
  return (
    <article>
      <p className="inline-flex rounded-full bg-[#b7ff33] px-2.5 py-0.5 text-xs font-semibold text-[#0c0c0c]">{n}</p>
      <div className="mt-3 mb-4 flex h-12 w-12 items-center justify-center rounded-2xl bg-[#0c0c0c] text-white">
        <Icon className="h-5 w-5" />
      </div>
      <h3 className="text-xl font-semibold">{title}</h3>
      <p className="mt-2 text-[#727272]">{text}</p>
    </article>
  )
}

function Stat({ value, label }: { value: string; label: string }) {
  return (
    <div>
      <p className="text-4xl font-semibold text-[#b7ff33]">{value}</p>
      <p className="mt-2 text-sm text-[#b8b8b8]">{label}</p>
    </div>
  )
}

function Audience({
  icon: Icon,
  title,
  text,
  points,
}: {
  icon: typeof FolderKanban
  title: string
  text: string
  points: string[]
}) {
  return (
    <article className="rounded-2xl border border-black/8 p-8">
      <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-full bg-[#b7ff33]">
        <Icon className="h-5 w-5" />
      </div>
      <h3 className="text-xl font-semibold">{title}</h3>
      <p className="mt-3 text-[#727272]">{text}</p>
      <ul className="mt-5 space-y-2">
        {points.map((point) => (
          <li key={point} className="flex items-start gap-2 text-sm">
            <Check className="mt-0.5 h-4 w-4 shrink-0 text-[#0c0c0c]" />
            {point}
          </li>
        ))}
      </ul>
    </article>
  )
}
