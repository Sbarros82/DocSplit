import { useCallback, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { motion, useReducedMotion } from 'motion/react'
import {
  AlertCircle,
  ArrowRight,
  CheckCircle2,
  FileText,
  Loader2,
  Lock,
  Upload as UploadIcon,
  Zap,
} from 'lucide-react'
import { toast } from 'sonner'
import { Header } from '@/components/Header'
import { useAuth } from '@/components/AuthProvider'

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000'
const easeOutCubic = [0.215, 0.61, 0.355, 1] as const

export function Upload() {
  const { user, profile, refreshProfile, getAccessToken } = useAuth()
  const navigate = useNavigate()
  const reduceMotion = useReducedMotion()
  const [file, setFile] = useState<File | null>(null)
  const [uploading, setUploading] = useState(false)
  const [progress, setProgress] = useState(0)
  const [result, setResult] = useState<any>(null)
  const [dragging, setDragging] = useState(false)

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setDragging(false)
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
      navigate('/login?next=' + encodeURIComponent('/upload'))
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
      const token = await getAccessToken().catch(() => null)
      const headers: Record<string, string> = {}
      if (token) headers.Authorization = `Bearer ${token}`
      const response = await fetch(`${BACKEND_URL}/api/download/${result.download_id}`, { headers })
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
    } catch {
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
    <div className="min-h-screen bg-white text-[#0c0c0c]">
      <Header />

      <section className="relative overflow-hidden px-6 pb-8 pt-12 md:pt-14">
        <div className="pointer-events-none absolute inset-0" aria-hidden>
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_right,rgba(183,255,51,0.22),transparent_42%)]" />
          {!reduceMotion && (
            <motion.div
              className="absolute -right-16 top-0 h-72 w-72 rounded-full bg-[#b7ff33]/25 blur-3xl"
              animate={{ x: [0, -30, 15, 0], y: [0, 20, -10, 0] }}
              transition={{ duration: 14, repeat: Infinity, ease: 'easeInOut' }}
            />
          )}
        </div>

        <div className="relative mx-auto max-w-3xl text-center">
          <motion.p
            className="text-sm font-medium text-[#727272]"
            initial={reduceMotion ? false : { opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, ease: easeOutCubic }}
          >
            Separação inteligente
          </motion.p>
          <motion.h1
            className="mt-1 text-3xl font-semibold tracking-tight md:text-4xl"
            initial={reduceMotion ? false : { opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.45, ease: easeOutCubic, delay: 0.05 }}
          >
            Processar documento
          </motion.h1>
          <motion.p
            className="mt-3 text-[#727272]"
            initial={reduceMotion ? false : { opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.45, ease: easeOutCubic, delay: 0.1 }}
          >
            Envie um PDF para separar e organizar automaticamente
          </motion.p>
        </div>
      </section>

      <div className="relative mx-auto max-w-3xl px-6 pb-16">
        {user && (
          <motion.div
            className="mb-6 flex flex-col gap-3 rounded-2xl border border-black/8 bg-[#f7f8fa] px-5 py-4 sm:flex-row sm:items-center sm:justify-between"
            initial={reduceMotion ? false : { opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, ease: easeOutCubic }}
          >
            <div className="flex items-center gap-3">
              <span className="flex h-9 w-9 items-center justify-center rounded-full bg-[#b7ff33]">
                <FileText className="h-4 w-4 text-[#0c0c0c]" />
              </span>
              <span className="text-sm">
                Créditos disponíveis: <strong>{availableCredits} MB</strong>
                {availableCredits <= 0 && (
                  <span className="text-[#727272]">
                    {' '}
                    · {Math.max(0, 3 - (profile?.free_uses_today || 0))}/3 usos grátis hoje
                  </span>
                )}
              </span>
            </div>
            <Link
              to="/pricing"
              className="inline-flex items-center gap-1 text-sm font-semibold text-[#0c0c0c] underline underline-offset-2"
            >
              Comprar mais
              <ArrowRight className="h-3.5 w-3.5" />
            </Link>
          </motion.div>
        )}

        {!result ? (
          <>
            <motion.div
              onDrop={handleDrop}
              onDragOver={(e) => {
                e.preventDefault()
                setDragging(true)
              }}
              onDragLeave={() => setDragging(false)}
              className={`rounded-2xl border-2 border-dashed p-10 text-center transition ${
                file || dragging
                  ? 'border-[#0c0c0c] bg-[#f7f8fa]'
                  : 'border-black/15 bg-white hover:border-black/30'
              } ${uploading ? 'pointer-events-none opacity-60' : ''}`}
              initial={reduceMotion ? false : { opacity: 0, y: 18 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.45, ease: easeOutCubic, delay: 0.08 }}
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
                    <span className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-[#b7ff33]">
                      <UploadIcon className="h-6 w-6 text-[#0c0c0c]" />
                    </span>
                    <p className="text-lg font-semibold">Arraste um PDF aqui ou clique para selecionar</p>
                    <p className="mt-2 text-sm text-[#727272]">Máximo: 100 MB · 500 páginas</p>
                  </>
                ) : (
                  <>
                    <span className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-[#0c0c0c]">
                      <FileText className="h-6 w-6 text-[#b7ff33]" />
                    </span>
                    <p className="text-lg font-semibold">{file.name}</p>
                    <p className="mt-2 text-sm text-[#727272]">
                      {formatFileSize(file.size)}
                      {availableCredits > 0
                        ? ` · ${availableCredits} MB de créditos`
                        : ` · ${Math.max(0, 3 - (profile?.free_uses_today || 0))}/3 usos grátis hoje`}
                    </p>
                    {!uploading && (
                      <button
                        type="button"
                        onClick={(e) => {
                          e.preventDefault()
                          setFile(null)
                        }}
                        className="mt-4 text-sm font-semibold text-[#727272] underline underline-offset-2 hover:text-[#0c0c0c]"
                      >
                        Remover arquivo
                      </button>
                    )}
                  </>
                )}
              </label>
            </motion.div>

            {file && !uploading && (
              <div className="mt-6 flex justify-center">
                <button
                  type="button"
                  onClick={handleUpload}
                  disabled={!user}
                  className="inline-flex items-center gap-2 rounded-full bg-[#b7ff33] px-8 py-3.5 text-base font-semibold text-[#0c0c0c] shadow-[0_8px_24px_rgba(183,255,51,0.35)] transition hover:bg-[#c8ff66] disabled:cursor-not-allowed disabled:bg-[#e6e8ee] disabled:text-[#9b9b9b] disabled:shadow-none"
                >
                  <UploadIcon className="h-5 w-5" />
                  {user ? 'Processar documento' : 'Faça login para processar'}
                </button>
              </div>
            )}

            {uploading && (
              <div className="mt-8">
                <div className="mb-3 flex items-center justify-center gap-3">
                  <Loader2 className="h-5 w-5 animate-spin text-[#0c0c0c]" />
                  <span className="text-sm font-medium">Processando documento...</span>
                </div>
                <div className="h-2 w-full overflow-hidden rounded-full bg-[#f4f5f7]">
                  <div
                    className="h-full rounded-full bg-[#b7ff33] transition-all duration-300"
                    style={{ width: `${progress}%` }}
                  />
                </div>
              </div>
            )}

            {!user && (
              <div className="mt-6 flex items-start gap-3 rounded-2xl border border-black/10 bg-[#0c0c0c] p-5 text-white">
                <span className="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-[#b7ff33]">
                  <AlertCircle className="h-4 w-4 text-[#0c0c0c]" />
                </span>
                <div>
                  <p className="font-semibold">Login necessário</p>
                  <p className="mt-1 text-sm text-[#b8b8b8]">
                    Faça login para processar documentos. Usuários cadastrados têm 3 uploads gratuitos por dia.
                  </p>
                  <Link
                    to="/login?next=/upload"
                    className="mt-3 inline-flex items-center gap-1 text-sm font-semibold text-[#b7ff33]"
                  >
                    Entrar agora
                    <ArrowRight className="h-3.5 w-3.5" />
                  </Link>
                </div>
              </div>
            )}
          </>
        ) : (
          <motion.div
            className="rounded-2xl border border-black/8 bg-[#f7f8fa] p-8"
            initial={reduceMotion ? false : { opacity: 0, y: 18 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.45, ease: easeOutCubic }}
          >
            <div className="text-center">
              <span className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-[#b7ff33]">
                <CheckCircle2 className="h-7 w-7 text-[#0c0c0c]" />
              </span>
              <h2 className="text-2xl font-semibold tracking-tight">Processamento concluído</h2>
              <p className="mt-2 text-[#727272]">
                Seu documento foi separado e organizado com sucesso
              </p>
            </div>

            <div className="mt-8 grid grid-cols-3 gap-3">
              <div className="rounded-2xl bg-white p-4 text-center">
                <p className="text-sm text-[#727272]">Páginas</p>
                <p className="mt-1 text-2xl font-semibold">
                  {result.total_pages || result.stats?.total_pages || 0}
                </p>
              </div>
              <div className="rounded-2xl bg-white p-4 text-center">
                <p className="text-sm text-[#727272]">Documentos</p>
                <p className="mt-1 text-2xl font-semibold">
                  {result.documents_count || result.stats?.total_documents || 0}
                </p>
              </div>
              <div className="rounded-2xl bg-white p-4 text-center">
                <p className="text-sm text-[#727272]">Créditos</p>
                <p className="mt-1 text-2xl font-semibold">{result.credits_used || 0} MB</p>
              </div>
            </div>

            <div className="mt-8 flex flex-col gap-3 sm:flex-row">
              <button
                type="button"
                onClick={handleDownload}
                className="flex-1 rounded-full bg-[#b7ff33] px-6 py-3.5 text-sm font-semibold text-[#0c0c0c] hover:bg-[#c8ff66]"
              >
                Download ZIP
              </button>
              <button
                type="button"
                onClick={() => {
                  setFile(null)
                  setResult(null)
                }}
                className="flex-1 rounded-full border border-black/15 bg-white px-6 py-3.5 text-sm font-semibold hover:bg-[#f4f5f7]"
              >
                Processar outro
              </button>
            </div>
          </motion.div>
        )}

        <div className="mt-12 grid gap-6 text-center md:grid-cols-3">
          {[
            {
              icon: FileText,
              title: 'Formatos suportados',
              text: 'Boletos, PIX, NF-e, DARF, Folha de Pagamento, Contas e mais',
            },
            {
              icon: Lock,
              title: 'Segurança',
              text: 'Arquivos processados e removidos logo após o download',
            },
            {
              icon: Zap,
              title: 'Velocidade',
              text: 'OCR automático para documentos digitalizados',
            },
          ].map((item) => (
            <div key={item.title}>
              <span className="mx-auto mb-3 flex h-10 w-10 items-center justify-center rounded-full bg-[#b7ff33]">
                <item.icon className="h-4 w-4 text-[#0c0c0c]" />
              </span>
              <h3 className="font-semibold">{item.title}</h3>
              <p className="mt-2 text-sm text-[#727272]">{item.text}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
