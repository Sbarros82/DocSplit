import { Link } from 'react-router-dom'
import { Header } from '@/components/Header'

export function Terms() {
  return (
    <div className="min-h-screen bg-white text-[#0c0c0c]">
      <Header />
      <main className="mx-auto max-w-3xl px-6 py-16">
        <p className="text-sm font-medium text-[#727272]">Documento legal</p>
        <h1 className="mt-2 text-4xl font-semibold tracking-tight">Termos de Uso</h1>
        <p className="mt-3 text-[#727272]">Última atualização: 20 de agosto de 2026</p>

        <div className="prose-doc mt-10 space-y-8 text-[15px] leading-7 text-[#3a3a3a]">
          <section>
            <h2 className="text-xl font-semibold text-[#0c0c0c]">1. Aceitação</h2>
            <p className="mt-2">
              Ao acessar ou usar o DocSplit (“Serviço”), você concorda com estes Termos de Uso.
              Se não concordar, não utilize o Serviço. O uso contínuo após alterações implica
              aceitação da versão atualizada.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-[#0c0c0c]">2. Descrição do Serviço</h2>
            <p className="mt-2">
              O DocSplit é uma ferramenta online para organizar e manipular arquivos PDF,
              incluindo separação automática de documentos brasileiros, operações de edição
              (juntar, comprimir, girar, proteger, corrigir texto etc.) e painel de créditos.
              O Serviço é oferecido “como está”, sujeito a limites técnicos e de disponibilidade.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-[#0c0c0c]">3. Conta e acesso</h2>
            <p className="mt-2">
              O uso das ferramentas e da cota gratuita exige conta autenticada. Você é responsável
              por manter a confidencialidade das suas credenciais e por toda atividade realizada
              na sua conta. Informe-nos imediatamente em caso de uso não autorizado.
            </p>
            <p className="mt-2">
              Cada conta possui identificação única. Você não deve tentar acessar dados, arquivos
              ou painéis de outros usuários.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-[#0c0c0c]">4. Uso permitido e proibido</h2>
            <p className="mt-2">Você se compromete a usar o Serviço apenas de forma lícita. É proibido:</p>
            <ul className="mt-2 list-disc space-y-1 pl-5">
              <li>enviar conteúdo ilegal, fraudulento ou que viole direitos de terceiros;</li>
              <li>tentar burlar limites de uso, autenticação ou segurança;</li>
              <li>realizar engenharia reversa abusiva, scraping agressivo ou ataques à infraestrutura;</li>
              <li>usar o Serviço para spam, phishing ou distribuição de malware;</li>
              <li>compartilhar ou revender acesso à conta sem autorização.</li>
            </ul>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-[#0c0c0c]">5. Arquivos enviados</h2>
            <p className="mt-2">
              Você declara ter legitimidade para enviar e processar os arquivos. O DocSplit trata
              os PDFs de forma temporária para executar a operação solicitada. Não usamos o
              conteúdo dos seus documentos para treinar modelos de IA de terceiros nem para fins
              comerciais alheios ao Serviço.
            </p>
            <p className="mt-2">
              Documentos assinados digitalmente podem perder validade jurídica após edição.
              Avalie riscos legais antes de alterar PDFs oficiais.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-[#0c0c0c]">6. Planos, créditos e pagamentos</h2>
            <p className="mt-2">
              Pode haver limite gratuito diário e pacotes de créditos pagos. Valores, validade e
              benefícios aparecem na página de preços no momento da compra. Pagamentos são
              processados por intermediários (ex.: Mercado Pago). Reembolsos, quando cabíveis,
              seguem a legislação aplicável e as regras do meio de pagamento.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-[#0c0c0c]">7. Privacidade e proteção de dados</h2>
            <p className="mt-2">
              O tratamento de dados pessoais segue a nossa{' '}
              <Link to="/privacy" className="font-semibold text-[#0c0c0c] underline underline-offset-2">
                Política de Privacidade
              </Link>
              , em conformidade com a LGPD (Lei nº 13.709/2018), quando aplicável.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-[#0c0c0c]">8. Disponibilidade e limitação de responsabilidade</h2>
            <p className="mt-2">
              Empregamos esforços razoáveis para manter o Serviço disponível e seguro, mas não
              garantimos funcionamento ininterrupto, isento de erros ou adequado a qualquer
              finalidade específica. Na máxima extensão permitida pela lei, o DocSplit não
              responde por lucros cessantes, perda de dados ou danos indiretos decorrentes do uso
              ou da impossibilidade de uso do Serviço.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-[#0c0c0c]">9. Propriedade intelectual</h2>
            <p className="mt-2">
              Marca, interface, código e materiais do DocSplit pertencem aos seus titulares.
              Você mantém os direitos sobre os arquivos que envia. Não concedemos licença para
              copiar, modificar ou explorar comercialmente o Serviço além do uso autorizado.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-[#0c0c0c]">10. Suspensão e encerramento</h2>
            <p className="mt-2">
              Podemos suspender ou encerrar o acesso em caso de violação destes Termos, risco
              à segurança, fraude ou obrigação legal. Você pode deixar de usar o Serviço a
              qualquer momento.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-[#0c0c0c]">11. Alterações</h2>
            <p className="mt-2">
              Estes Termos podem ser atualizados. A data no topo indica a versão vigente.
              Alterações relevantes podem ser comunicadas no site ou por outros meios razoáveis.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-[#0c0c0c]">12. Lei aplicável</h2>
            <p className="mt-2">
              Estes Termos são regidos pelas leis da República Federativa do Brasil. Foro da
              comarca do domicílio do consumidor, quando aplicável o Código de Defesa do Consumidor;
              nos demais casos, foro competente conforme a legislação vigente.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-[#0c0c0c]">13. Contato</h2>
            <p className="mt-2">
              Dúvidas sobre estes Termos: utilize os canais de suporte indicados no site DocSplit.
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
