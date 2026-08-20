import { Link } from 'react-router-dom'
import { Header } from '@/components/Header'

export function Privacy() {
  return (
    <div className="min-h-screen bg-white text-[#0c0c0c]">
      <Header />
      <main className="mx-auto max-w-3xl px-6 py-16">
        <p className="text-sm font-medium text-[#727272]">Documento legal</p>
        <h1 className="mt-2 text-4xl font-semibold tracking-tight">Política de Privacidade</h1>
        <p className="mt-3 text-[#727272]">Última atualização: 20 de agosto de 2026</p>

        <div className="mt-10 space-y-8 text-[15px] leading-7 text-[#3a3a3a]">
          <section>
            <h2 className="text-xl font-semibold text-[#0c0c0c]">1. Quem somos</h2>
            <p className="mt-2">
              Esta Política descreve como o DocSplit trata dados pessoais no uso do site e das
              ferramentas de PDF, em alinhamento com a LGPD (Lei nº 13.709/2018).
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-[#0c0c0c]">2. Dados que coletamos</h2>
            <ul className="mt-2 list-disc space-y-1 pl-5">
              <li>dados de conta: e-mail, identificador único e, se houver, nome/avatar do provedor de login;</li>
              <li>dados de uso: histórico de jobs, contadores de cota gratuita e créditos;</li>
              <li>dados de pagamento: processados pelo provedor (ex.: Mercado Pago); não armazenamos número completo de cartão;</li>
              <li>dados técnicos: endereço IP, user-agent e logs necessários à segurança e ao funcionamento.</li>
            </ul>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-[#0c0c0c]">3. Arquivos PDF</h2>
            <p className="mt-2">
              Os arquivos enviados são processados para cumprir a operação solicitada (separar,
              juntar, editar etc.). O tratamento é temporário: após o processamento, os arquivos
              são removidos dos ambientes de trabalho. Não vendemos o conteúdo dos seus documentos
              nem o usamos para publicidade.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-[#0c0c0c]">4. Finalidades e bases legais</h2>
            <p className="mt-2">Usamos dados para:</p>
            <ul className="mt-2 list-disc space-y-1 pl-5">
              <li>prestar e autenticar o Serviço (execução de contrato / legítimo interesse);</li>
              <li>controlar cotas, créditos e pagamentos;</li>
              <li>prevenir fraude e abuso (legítimo interesse / obrigação legal);</li>
              <li>cumprir obrigações legais e responder a autoridades competentes.</li>
            </ul>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-[#0c0c0c]">5. Compartilhamento</h2>
            <p className="mt-2">
              Podemos compartilhar dados com provedores essenciais (hospedagem, autenticação,
              pagamento), sempre sob obrigação de confidencialidade e nas finalidades descritas.
              Não vendemos dados pessoais.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-[#0c0c0c]">6. Retenção e segurança</h2>
            <p className="mt-2">
              Mantemos dados de conta e de uso pelo tempo necessário à prestação do Serviço e a
              obrigações legais. Aplicamos medidas técnicas e organizacionais razoáveis (controle
              de acesso, isolamento por usuário, HTTPS). Nenhum sistema é 100% invulnerável.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-[#0c0c0c]">7. Seus direitos (LGPD)</h2>
            <p className="mt-2">
              Você pode solicitar confirmação de tratamento, acesso, correção, anonimização,
              portabilidade, eliminação (quando cabível), informação sobre compartilhamentos e
              revogação de consentimento. Pedidos podem ser feitos pelos canais de suporte do site.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-[#0c0c0c]">8. Cookies e armazenamento local</h2>
            <p className="mt-2">
              Usamos armazenamento local do navegador para sessão de autenticação e preferências
              básicas. Sem cookies de rastreamento publicitário de terceiros no fluxo principal.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-[#0c0c0c]">9. Alterações</h2>
            <p className="mt-2">
              Esta Política pode ser atualizada. A data no topo indica a versão vigente.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-[#0c0c0c]">10. Contato</h2>
            <p className="mt-2">
              Para exercer direitos ou esclarecer dúvidas sobre privacidade, utilize o suporte
              indicado no DocSplit. Consulte também os{' '}
              <Link to="/terms" className="font-semibold text-[#0c0c0c] underline underline-offset-2">
                Termos de Uso
              </Link>
              .
            </p>
          </section>
        </div>

        <p className="mt-12 text-sm text-[#727272]">
          <Link to="/" className="font-semibold text-[#0c0c0c] hover:underline">
            ← Voltar ao início
          </Link>
        </p>
      </main>
    </div>
  )
}
