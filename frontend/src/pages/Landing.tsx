import { Link } from 'react-router-dom'
import { FileText, Zap, Shield, Check } from 'lucide-react'
import { Header } from '@/components/Header'

export function Landing() {
  return (
    <div className="min-h-screen">
      <Header />
      {/* Hero */}
      <section className="bg-gradient-to-br from-blue-50 to-indigo-100 py-20">
        <div className="max-w-6xl mx-auto px-6">
          <div className="text-center max-w-3xl mx-auto">
            <h1 className="text-5xl md:text-6xl font-bold text-gray-900 mb-6">
              Separe PDFs Misturados
              <span className="block text-blue-600 mt-2">Automaticamente</span>
            </h1>
            <p className="text-xl text-gray-700 mb-8">
              Identifica boletos, PIX, notas fiscais, DARF e outros documentos brasileiros.
              Um PDF com 50 páginas vira 30 arquivos organizados em segundos.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link
                to="/upload"
                className="bg-blue-600 text-white px-8 py-4 rounded-lg font-semibold hover:bg-blue-700 transition text-lg shadow-lg hover:shadow-xl"
              >
                Experimentar Grátis
              </Link>
              <Link
                to="/pricing"
                className="bg-white text-blue-600 border-2 border-blue-600 px-8 py-4 rounded-lg font-semibold hover:bg-blue-50 transition text-lg"
              >
                Ver Preços
              </Link>
            </div>
            <p className="text-sm text-gray-600 mt-4">
              ✨ 3 arquivos grátis por dia · Sem cartão de crédito
            </p>
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="py-20">
        <div className="max-w-6xl mx-auto px-6">
          <h2 className="text-3xl font-bold text-center mb-12">Como Funciona</h2>
          <div className="grid md:grid-cols-3 gap-8">
            <div className="text-center">
              <div className="bg-blue-100 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
                <FileText className="h-8 w-8 text-blue-600" />
              </div>
              <h3 className="text-xl font-semibold mb-2">1. Upload do PDF</h3>
              <p className="text-gray-600">
                Arraste o PDF digitalizado ou com múltiplos documentos misturados
              </p>
            </div>
            <div className="text-center">
              <div className="bg-green-100 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
                <Zap className="h-8 w-8 text-green-600" />
              </div>
              <h3 className="text-xl font-semibold mb-2">2. Classificação Automática</h3>
              <p className="text-gray-600">
                IA identifica PIX, boletos, NF-e, DARF, folha, energia e mais
              </p>
            </div>
            <div className="text-center">
              <div className="bg-purple-100 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
                <Shield className="h-8 w-8 text-purple-600" />
              </div>
              <h3 className="text-xl font-semibold mb-2">3. Baixe Organizado</h3>
              <p className="text-gray-600">
                ZIP com PDFs nomeados + índice Excel. Nada se perde.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Social Proof */}
      <section className="bg-gray-50 py-16">
        <div className="max-w-4xl mx-auto px-6 text-center">
          <div className="grid grid-cols-3 gap-8">
            <div>
              <p className="text-4xl font-bold text-blue-600">12.456</p>
              <p className="text-gray-600 mt-2">Documentos processados</p>
            </div>
            <div>
              <p className="text-4xl font-bold text-blue-600">1.834</p>
              <p className="text-gray-600 mt-2">Usuários ativos</p>
            </div>
            <div>
              <p className="text-4xl font-bold text-blue-600">4.9</p>
              <p className="text-gray-600 mt-2">Avaliação média</p>
            </div>
          </div>
        </div>
      </section>

      {/* Use Cases */}
      <section className="py-20">
        <div className="max-w-6xl mx-auto px-6">
          <h2 className="text-3xl font-bold text-center mb-12">Perfeito Para</h2>
          <div className="grid md:grid-cols-2 gap-8">
            <div className="border border-gray-200 rounded-lg p-6">
              <h3 className="text-xl font-semibold mb-3">📊 Contadores</h3>
              <p className="text-gray-600 mb-4">
                Organize documentos de dezenas de clientes em minutos. Separa NF-e, DARF, folhas de pagamento automaticamente.
              </p>
              <ul className="space-y-2">
                <li className="flex items-start gap-2">
                  <Check className="h-5 w-5 text-green-600 flex-shrink-0 mt-0.5" />
                  <span className="text-sm">Economize horas de trabalho manual</span>
                </li>
                <li className="flex items-start gap-2">
                  <Check className="h-5 w-5 text-green-600 flex-shrink-0 mt-0.5" />
                  <span className="text-sm">Evite erros de arquivamento</span>
                </li>
              </ul>
            </div>

            <div className="border border-gray-200 rounded-lg p-6">
              <h3 className="text-xl font-semibold mb-3">🏢 Empresas</h3>
              <p className="text-gray-600 mb-4">
                Separe boletos, comprovantes PIX e faturas vindos do banco ou scanner de forma automática.
              </p>
              <ul className="space-y-2">
                <li className="flex items-start gap-2">
                  <Check className="h-5 w-5 text-green-600 flex-shrink-0 mt-0.5" />
                  <span className="text-sm">Processe lotes grandes (até 200 páginas)</span>
                </li>
                <li className="flex items-start gap-2">
                  <Check className="h-5 w-5 text-green-600 flex-shrink-0 mt-0.5" />
                  <span className="text-sm">Integração via API disponível</span>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="bg-blue-600 text-white py-16">
        <div className="max-w-4xl mx-auto px-6 text-center">
          <h2 className="text-3xl font-bold mb-4">Comece Agora Gratuitamente</h2>
          <p className="text-xl mb-8 text-blue-100">
            3 arquivos por dia, sem cadastro de cartão. Upgrade quando precisar.
          </p>
          <Link
            to="/upload"
            className="bg-white text-blue-600 px-8 py-4 rounded-lg font-semibold hover:bg-blue-50 transition text-lg inline-block shadow-lg hover:shadow-xl"
          >
            Separar Primeiro PDF
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-900 text-gray-400 py-8">
        <div className="max-w-6xl mx-auto px-6 text-center text-sm">
          <p>&copy; 2026 DocSplit. Seus arquivos são processados e deletados imediatamente.</p>
          <p className="mt-2">
            <Link to="/privacy" className="hover:text-white">Privacidade</Link>
            {' · '}
            <Link to="/terms" className="hover:text-white">Termos de Uso</Link>
          </p>
        </div>
      </footer>
    </div>
  )
}
