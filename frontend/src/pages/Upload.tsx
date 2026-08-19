import { useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { Header } from '@/components/Header'
import { useAuth } from '@/components/AuthProvider'
import { Upload as UploadIcon, FileText, AlertCircle, CheckCircle2, Loader2 } from 'lucide-react'
import { toast } from 'sonner'

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000'

export function Upload() {
  const { user, profile, refreshProfile, getAccessToken } = useAuth()
  const navigate = useNavigate()
  const [file, setFile] = useState<File | null>(null)
  const [uploading, setUploading] = useState(false)
  const [progress, setProgress] = useState(0)
  const [result, setResult] = useState<any>(null)

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    const droppedFile = e.dataTransfer.files[0]
    if (droppedFile && droppedFile.type === 'application/pdf') {
      setFile(droppedFile)
    } else {
      toast.error('Por favor, envie apenas arquivos PDF')
    }
  }, [])

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0]
    if (selectedFile && selectedFile.type === 'application/pdf') {
      setFile(selectedFile)
    } else {
      toast.error('Por favor, envie apenas arquivos PDF')
    }
  }

  const handleUpload = async () => {
    if (!file) return

    if (!user) {
      toast.error('Faça login para processar documentos')
      navigate('/login')
      return
    }

    const fileSizeMb = file.size / (1024 * 1024)
    if (fileSizeMb > 100) {
      toast.error('Arquivo excede o limite de 100 MB')
      return
    }

    const availableCredits = profile
      ? Math.max(0, (profile.total_credits_mb || 0) - (profile.used_credits_mb || 0))
      : 0
    const freeUses = profile?.free_uses_today || 0

    if (availableCredits < fileSizeMb) {
      if (freeUses >= 3) {
        toast.error('Sem créditos e limite gratuito diário atingido. Adquira créditos para continuar.')
        navigate('/pricing')
        return
      }
      if (fileSizeMb > 2) {
        toast.error('Arquivo maior que 2 MB. No plano gratuito o máximo é 2 MB. Adquira créditos para arquivos maiores.')
        navigate('/pricing')
        return
      }
    }

    setUploading(true)
    setProgress(8)
    const progressTimer = window.setInterval(() => {
      setProgress((current) => (current < 90 ? current + 4 : current))
    }, 800)

    try {
      const token = await getAccessToken()
      if (!token) {
        throw new Error('Sessão expirada. Faça login novamente.')
      }

      const formData = new FormData()
      formData.append('file', file)

      const response = await fetch(`${BACKEND_URL}/api/process`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
        },
        body: formData,
      })

      if (!response.ok) {
        const error = await response.json().catch(() => ({}))
        const detail = error.detail
        const message = typeof detail === 'string' ? detail : 'Erro ao processar PDF'
        throw new Error(message)
      }

      const data = await response.json()
      setProgress(100)
      setResult(data)
      toast.success('PDF processado com sucesso!')
      await refreshProfile()
    } catch (error: any) {
      console.error('Erro:', error)
      toast.error(error.message || 'Erro ao processar PDF')
    } finally {
      window.clearInterval(progressTimer)
      setUploading(false)
    }
  }

  const handleDownload = async () => {
    if (!result?.download_id) return

    try {
      const response = await fetch(`${BACKEND_URL}/api/download/${result.download_id}`)
      if (!response.ok) throw new Error('Erro ao baixar arquivo')

      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `docsplit_${result.download_id}.zip`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
    } catch (error) {
      toast.error('Erro ao baixar arquivo')
    }
  }

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return bytes + ' B'
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
  }

  const availableCredits = profile
    ? Math.max(0, (profile.total_credits_mb || 0) - (profile.used_credits_mb || 0))
    : 0

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      
      <div className="max-w-4xl mx-auto px-6 py-12">
        {/* Título */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Processar Documento
          </h1>
          <p className="text-gray-600">
            Envie um PDF para separar e organizar automaticamente
          </p>
        </div>

        {/* Créditos Disponíveis */}
        {user && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <FileText className="h-5 w-5 text-blue-600" />
                <span className="text-sm font-medium text-blue-900">
                  Créditos disponíveis: <strong>{availableCredits} MB</strong>
                </span>
              </div>
              <button
                onClick={() => navigate('/pricing')}
                className="text-sm text-blue-600 hover:text-blue-700 font-semibold"
              >
                Comprar mais
              </button>
            </div>
          </div>
        )}

        {!result ? (
          <>
            {/* Área de Upload */}
            <div
              onDrop={handleDrop}
              onDragOver={(e) => e.preventDefault()}
              className={`
                border-2 border-dashed rounded-lg p-12 text-center transition
                ${file ? 'border-blue-500 bg-blue-50' : 'border-gray-300 bg-white hover:border-gray-400'}
                ${uploading ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
              `}
            >
              <input
                type="file"
                accept=".pdf"
                onChange={handleFileSelect}
                disabled={uploading}
                className="hidden"
                id="file-upload"
              />
              
              <label htmlFor="file-upload" className="cursor-pointer">
                {!file ? (
                  <>
                    <UploadIcon className="h-16 w-16 text-gray-400 mx-auto mb-4" />
                    <p className="text-lg font-semibold text-gray-700 mb-2">
                      Arraste um PDF aqui ou clique para selecionar
                    </p>
                    <p className="text-sm text-gray-500">
                      Máximo: 100 MB • 500 páginas
                    </p>
                  </>
                ) : (
                  <>
                    <FileText className="h-16 w-16 text-blue-600 mx-auto mb-4" />
                    <p className="text-lg font-semibold text-gray-900 mb-1">
                      {file.name}
                    </p>
                    <p className="text-sm text-gray-600 mb-4">
                      {formatFileSize(file.size)}
                      {availableCredits > 0 ? ` · ${availableCredits} MB de créditos` : ` · ${Math.max(0, 3 - (profile?.free_uses_today || 0))}/3 usos grátis hoje`}
                    </p>
                    {!uploading && (
                      <button
                        onClick={(e) => {
                          e.preventDefault()
                          setFile(null)
                        }}
                        className="text-sm text-red-600 hover:text-red-700"
                      >
                        Remover arquivo
                      </button>
                    )}
                  </>
                )}
              </label>
            </div>

            {/* Botão de Processar */}
            {file && !uploading && (
              <div className="mt-6 flex justify-center">
                <button
                  onClick={handleUpload}
                  disabled={!user}
                  className="bg-blue-600 text-white px-8 py-3 rounded-lg font-semibold hover:bg-blue-700 transition disabled:bg-gray-300 disabled:cursor-not-allowed flex items-center gap-2"
                >
                  <UploadIcon className="h-5 w-5" />
                  {user ? 'Processar Documento' : 'Faça login para processar'}
                </button>
              </div>
            )}

            {/* Loading */}
            {uploading && (
              <div className="mt-6">
                <div className="flex items-center justify-center gap-3 mb-3">
                  <Loader2 className="h-5 w-5 text-blue-600 animate-spin" />
                  <span className="text-sm font-medium text-gray-700">
                    Processando documento...
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                    style={{ width: `${progress}%` }}
                  />
                </div>
              </div>
            )}

            {/* Aviso sem login */}
            {!user && (
              <div className="mt-6 bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                <div className="flex items-start gap-3">
                  <AlertCircle className="h-5 w-5 text-yellow-600 flex-shrink-0 mt-0.5" />
                  <div>
                    <p className="text-sm font-medium text-yellow-900 mb-1">
                      Login necessário
                    </p>
                    <p className="text-sm text-yellow-700">
                      Faça login para processar documentos. Usuários cadastrados têm 3 uploads gratuitos por dia.
                    </p>
                  </div>
                </div>
              </div>
            )}
          </>
        ) : (
          /* Resultado */
          <div className="bg-white rounded-lg shadow-lg p-8">
            <div className="text-center mb-6">
              <CheckCircle2 className="h-16 w-16 text-green-600 mx-auto mb-4" />
              <h2 className="text-2xl font-bold text-gray-900 mb-2">
                Processamento Concluído!
              </h2>
              <p className="text-gray-600">
                Seu documento foi separado e organizado com sucesso
              </p>
            </div>

            {/* Estatísticas */}
            <div className="grid grid-cols-3 gap-4 mb-6">
              <div className="bg-gray-50 rounded-lg p-4 text-center">
                <p className="text-sm text-gray-600 mb-1">Páginas</p>
                <p className="text-2xl font-bold text-gray-900">{result.total_pages || result.stats?.total_pages || 0}</p>
              </div>
              <div className="bg-gray-50 rounded-lg p-4 text-center">
                <p className="text-sm text-gray-600 mb-1">Documentos</p>
                <p className="text-2xl font-bold text-blue-600">{result.documents_count || result.stats?.total_documents || 0}</p>
              </div>
              <div className="bg-gray-50 rounded-lg p-4 text-center">
                <p className="text-sm text-gray-600 mb-1">Créditos</p>
                <p className="text-2xl font-bold text-gray-900">{result.credits_used || 0} MB</p>
              </div>
            </div>

            {/* Botões */}
            <div className="flex flex-col sm:flex-row gap-4">
              <button
                onClick={handleDownload}
                className="flex-1 bg-blue-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-blue-700 transition"
              >
                Download ZIP
              </button>
              <button
                onClick={() => {
                  setFile(null)
                  setResult(null)
                }}
                className="flex-1 bg-gray-100 text-gray-700 px-6 py-3 rounded-lg font-semibold hover:bg-gray-200 transition"
              >
                Processar Outro
              </button>
            </div>
          </div>
        )}

        {/* Informações */}
        <div className="mt-8 grid md:grid-cols-3 gap-6 text-center">
          <div>
            <h3 className="font-semibold text-gray-900 mb-2">📄 Formatos Suportados</h3>
            <p className="text-sm text-gray-600">
              Boletos, PIX, NF-e, DARF, Folha de Pagamento, Contas e mais
            </p>
          </div>
          <div>
            <h3 className="font-semibold text-gray-900 mb-2">🔒 Segurança</h3>
            <p className="text-sm text-gray-600">
              Seus arquivos são processados e deletados imediatamente após o download
            </p>
          </div>
          <div>
            <h3 className="font-semibold text-gray-900 mb-2">⚡ Velocidade</h3>
            <p className="text-sm text-gray-600">
              Processamento rápido com OCR automático para documentos digitalizados
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
