import { useEffect } from 'react'
import { useSearchParams, Link } from 'react-router-dom'
import { Header } from '@/components/Header'
import { useAuth } from '@/components/AuthProvider'
import { CheckCircle, XCircle, Clock } from 'lucide-react

type ResultType = 'success' | 'failure' | 'pending'

const CONFIG: Record<ResultType, { icon: typeof CheckCircle; title: string; description: string; color: string }> = {
  success: {
    icon: CheckCircle,
    title: 'Pagamento aprovado!',
    description: 'Seus créditos foram adicionados à sua conta. Você já pode usar o DocSplit.',
    color: 'text-green-600',
  },
  failure: {
    icon: XCircle,
    title: 'Pagamento não aprovado',
    description: 'O pagamento não foi concluído. Tente novamente ou escolha outro método de pagamento.',
    color: 'text-red-600',
  },
  pending: {
    icon: Clock,
    title: 'Pagamento pendente',
    description: 'Estamos aguardando a confirmação do pagamento. Seus créditos serão liberados assim que aprovado.',
    color: 'text-yellow-600',
  },
}

export function PaymentResult({ type }: { type: ResultType }) {
  const [searchParams] = useSearchParams()
  const { refreshProfile } = useAuth()
  const paymentId = searchParams.get('payment_id')
  const status = searchParams.get('status')

  useEffect(() => {
    if (type === 'success' || type === 'pending') {
      refreshProfile()
    }
  }, [type, refreshProfile])

  const { icon: Icon, title, description, color } = CONFIG[type]

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      <div className="max-w-lg mx-auto px-6 py-20 text-center">
        <Icon className={`h-16 w-16 mx-auto mb-6 ${color}`} />
        <h1 className="text-2xl font-bold text-gray-900 mb-3">{title}</h1>
        <p className="text-gray-600 mb-8">{description}</p>

        {paymentId && paymentId !== 'null' && (
          <p className="text-sm text-gray-400 mb-6">
            ID do pagamento: {paymentId}
          </p>
        )}

        {status && status !== 'null' && (
          <p className="text-sm text-gray-400 mb-6">
            Status: {status}
          </p>
        )}

        <div className="flex flex-col sm:flex-row gap-3 justify-center">
          <Link
            to="/dashboard"
            className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition font-medium"
          >
            Ir para o Painel
          </Link>
          {type === 'failure' && (
            <Link
              to="/pricing"
              className="border border-gray-300 text-gray-700 px-6 py-3 rounded-lg hover:bg-gray-100 transition font-medium"
            >
              Tentar novamente
            </Link>
          )}
        </div>
      </div>
    </div>
  )
}
