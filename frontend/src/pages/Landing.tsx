import { Link } from 'react-router-dom'
import {
  ArrowRight,
  Check,
  FileText,
  FolderKanban,
  Lock,
  ScanText,
  Shield,
  Sparkles,
  Zap,
} from 'lucide-react'
import { Header } from '@/components/Header'

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
]

export function Landing() {
  return (
    <div className="min-h-screen bg-white text-[#0c0c0c]">
      <Header />

      <section className="relative overflow-hidden px-6 pb-20 pt-16 md:pt-24">
        <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_top_right,rgba(183,255,51,0.28),transparent_42%)]" />
        <div className="relative mx-auto max-w-5xl text-center">
          <p className="mb-6 inline-flex items-center gap-2 rounded-full border border-black/10 bg-white px-4 py-1.5 text-sm text-[#727272]">
            <span className="h-2 w-2 rounded-full bg-[#b7ff33]" />
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
            <Link
              to="/upload"
              className="inline-flex items-center gap-2 rounded-full bg-[#0c0c0c] px-7 py-3.5 text-base font-semibold text-white hover:bg-black"
            >
              Começar agora
              <ArrowRight className="h-4 w-4" />
            </Link>
            <Link
              to="/pricing"
              className="inline-flex items-center gap-2 rounded-full border border-black/15 bg-white px-7 py-3.5 text-base font-semibold text-[#0c0c0c] hover:bg-[#f4f5f7]"
            >
              Ver preços
            </Link>
          </div>
          <p className="mt-5 text-sm text-[#9b9b9b]">Template visual inspirado no SAP da Originkit · produto 100% DocSplit</p>
        </div>
      </section>

      <section className="border-t border-black/5 px-6 py-20">
        <div className="mx-auto max-w-6xl">
          <p className="text-sm font-medium text-[#727272]">Recursos</p>
          <h2 className="mt-2 max-w-xl text-3xl font-semibold tracking-tight md:text-4xl">
            Tudo que um lote de documentos precisa
          </h2>
          <div className="mt-12 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {FEATURES.map((item) => (
              <article key={item.title} className="rounded-2xl border border-black/8 bg-[#f7f8fa] p-6">
                <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-full bg-[#b7ff33]">
                  <Sparkles className="h-5 w-5 text-[#0c0c0c]" />
                </div>
                <h3 className="text-lg font-semibold">{item.title}</h3>
                <p className="mt-2 text-sm leading-6 text-[#727272]">{item.desc}</p>
              </article>
            ))}
          </div>
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
          <div className="mt-12 grid gap-8 sm:grid-cols-2 lg:grid-cols-3">
            {BENEFITS.map((item) => (
              <article key={item.title}>
                <h3 className="text-lg font-semibold">{item.title}</h3>
                <p className="mt-2 text-sm leading-6 text-[#727272]">{item.desc}</p>
              </article>
            ))}
          </div>
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

      <section className="border-t border-black/5 px-6 py-20">
        <div className="mx-auto max-w-3xl">
          <h2 className="text-center text-3xl font-semibold tracking-tight">Perguntas frequentes</h2>
          <div className="mt-10 divide-y divide-black/10">
            {FAQS.map((item) => (
              <details key={item.q} className="group py-5">
                <summary className="cursor-pointer list-none text-lg font-medium">
                  {item.q}
                </summary>
                <p className="mt-2 text-[#727272]">{item.a}</p>
              </details>
            ))}
          </div>
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

      <footer className="border-t border-black/10 px-6 py-10 text-center text-sm text-[#727272]">
        <p className="flex items-center justify-center gap-2">
          <Lock className="h-4 w-4" />
          © 2026 DocSplit. Arquivos processados e removidos em seguida.
        </p>
        <p className="mt-2">
          <Link to="/privacy" className="hover:text-[#0c0c0c]">Privacidade</Link>
          {' · '}
          <Link to="/terms" className="hover:text-[#0c0c0c]">Termos de Uso</Link>
        </p>
      </footer>
    </div>
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
