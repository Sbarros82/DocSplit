import { useState } from 'react'
import { useAuth } from '@/components/AuthProvider'
import { Header } from '@/components/Header'
import { Check } from 'lucide-react'
import { toast } from 'sonner'

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000'

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
      'Sem marca d\'água',
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
      'Sem marca d\'água',
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
      'Sem marca d\'água',
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
      'Sem marca d\'água',
      'Suporte prioritário',
      'Acesso antecipado a novos recursos',
      'API disponível',
    ],
  },
]

export function Pricing() {
  const { user, getAccessToken } = useAuth()
  const [loading, setLoading] = useState<string | null>(null)

  const handleCheckout = async (packageId: string) => {
    if (!user) {
      toast.error('Faça login para continuar')
      window.location.href = '/login'
      return
    }

    setLoading(packageId)

    try {
      const token = await getAccessToken()
      if (!token) {
        throw new Error('Sessão expirada. Faça login novamente.')
      }

      const response = await fetch(`${BACKEND_URL}/api/payment/create-checkout`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
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
      
      // Redirecionar para o Mercado Pago
      window.location.href = data.checkout_url
    } catch (error) {
      console.error(error)
      toast.error(error instanceof Error ? error.message : 'Erro ao processar pagamento. Tente novamente.')
      setLoading(null)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      <div className="py-12">
      <div className="max-w-7xl mx-auto px-6">
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            Escolha Seu Pacote
          </h1>
          <p className="text-xl text-gray-600">
            Pague apenas pelo que usar. Créditos válidos por 90 dias.
          </p>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
          {packages.map((pkg) => (
            <div
              key={pkg.id}
              className={`
                bg-white rounded-lg shadow-lg p-6 border-2 relative
                ${pkg.popular ? 'border-blue-600' : 'border-transparent'}
              `}
            >
              {pkg.popular && (
                <div className="absolute -top-4 left-1/2 -translate-x-1/2 bg-blue-600 text-white px-4 py-1 rounded-full text-sm font-semibold">
                  Mais Popular
                </div>
              )}
              
              <h3 className="text-2xl font-bold text-gray-900 mb-2">{pkg.name}</h3>
              <p className="text-gray-600 text-sm mb-4">{pkg.description}</p>
              
              <div className="mb-6">
                <span className="text-4xl font-bold text-gray-900">R$ {pkg.price}</span>
                <span className="text-gray-600 ml-2">/ {pkg.credits} MB</span>
              </div>

              <button
                onClick={() => handleCheckout(pkg.id)}
                disabled={loading !== null}
                className={`
                  w-full py-3 rounded-lg font-semibold transition mb-6
                  ${pkg.popular
                    ? 'bg-blue-600 text-white hover:bg-blue-700'
                    : 'bg-gray-100 text-gray-900 hover:bg-gray-200'
                  }
                  ${loading === pkg.id ? 'opacity-50 cursor-wait' : ''}
                `}
              >
                {loading === pkg.id ? 'Processando...' : 'Adquirir Agora'}
              </button>

              <ul className="space-y-3">
                {pkg.features.map((feature, idx) => (
                  <li key={idx} className="flex items-start gap-2">
                    <Check className="h-5 w-5 text-green-600 flex-shrink-0 mt-0.5" />
                    <span className="text-sm text-gray-700">{feature}</span>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        {/* FAQ */}
        <div className="max-w-3xl mx-auto">
          <h2 className="text-2xl font-bold text-center mb-8">Perguntas Frequentes</h2>
          <div className="space-y-6">
            <div>
              <h3 className="font-semibold text-lg mb-2">Como funcionam os créditos?</h3>
              <p className="text-gray-600">
                Cada arquivo processa descontamos o tamanho em MB do seu saldo. Um PDF de 5 MB consome 5 MB de créditos.
              </p>
            </div>
            <div>
              <h3 className="font-semibold text-lg mb-2">Os créditos expiram?</h3>
              <p className="text-gray-600">
                Sim, após 90 dias da compra. Você receberá avisos antes de expirar.
              </p>
            </div>
            <div>
              <h3 className="font-semibold text-lg mb-2">Posso usar sem pagar?</h3>
              <p className="text-gray-600">
                Sim! Você tem 3 uploads gratuitos por dia (máx 2 MB cada, 10 páginas).
              </p>
            </div>
            <div>
              <h3 className="font-semibold text-lg mb-2">Quais formas de pagamento?</h3>
              <p className="text-gray-600">
                PIX (instantâneo), cartão de crédito/débito e boleto via Mercado Pago.
              </p>
            </div>
          </div>
        </div>
      </div>
      </div>
    </div>
  )
}
