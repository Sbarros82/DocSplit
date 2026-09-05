import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { motion, useReducedMotion } from 'motion/react'
import { ArrowRight, BookOpen } from 'lucide-react'
import { Header } from '@/components/Header'
import { SiteFooter } from '@/components/SiteFooter'
import { Seo } from '@/components/Seo'

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000'
const easeOutCubic = [0.215, 0.61, 0.355, 1] as const

type Post = {
  id: string
  slug: string
  title: string
  excerpt: string
  published_at: string | null
}

export function Blog() {
  const reduceMotion = useReducedMotion()
  const [posts, setPosts] = useState<Post[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    ;(async () => {
      try {
        const r = await fetch(`${BACKEND_URL}/api/blog/posts`)
        if (!r.ok) throw new Error('Não foi possível carregar o blog')
        const data = await r.json()
        setPosts(data.posts || [])
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Erro ao carregar')
      } finally {
        setLoading(false)
      }
    })()
  }, [])

  return (
    <div className="min-h-screen bg-white text-[#0c0c0c]">
      <Seo
        title="Blog DocSplit — Como separar, juntar e organizar PDFs"
        description="Guias práticos: separar lote de boletos e NF-e, juntar PDFs, créditos e plano faturado. Dicas para contadores e pequenas empresas."
        path="/blog"
      />
      <Header />
      <section className="relative overflow-hidden px-6 pb-8 pt-14 md:pt-16">
        <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_top_right,rgba(183,255,51,0.2),transparent_42%)]" />
        <div className="relative mx-auto max-w-4xl text-center">
          <p className="text-sm font-medium text-[#727272]">Blog</p>
          <h1 className="mt-2 text-4xl font-semibold tracking-tight md:text-5xl">Dicas de uso</h1>
          <p className="mx-auto mt-4 max-w-2xl text-[#727272]">
            Guias práticos para separar lotes, juntar PDFs e tirar mais do DocSplit no dia a dia do escritório.
          </p>
        </div>
      </section>

      <div className="mx-auto max-w-4xl px-6 pb-16">
        {loading && <p className="py-16 text-center text-[#727272]">Carregando...</p>}
        {error && <p className="py-16 text-center text-[#727272]">{error}</p>}
        {!loading && !error && posts.length === 0 && (
          <p className="py-16 text-center text-[#727272]">Em breve publicaremos as primeiras dicas.</p>
        )}

        <div className="grid gap-4">
          {posts.map((post, index) => (
            <motion.article
              key={post.id}
              initial={reduceMotion ? false : { opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, ease: easeOutCubic, delay: 0.05 * index }}
              className="rounded-2xl border border-black/8 bg-[#f7f8fa] p-6 transition hover:border-black/15 hover:bg-white"
            >
              <div className="flex items-start gap-4">
                <span className="mt-1 flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-[#b7ff33]">
                  <BookOpen className="h-4 w-4" />
                </span>
                <div className="min-w-0 flex-1">
                  {post.published_at && (
                    <p className="text-xs text-[#9b9b9b]">
                      {new Date(post.published_at).toLocaleDateString('pt-BR')}
                    </p>
                  )}
                  <h2 className="mt-1 text-xl font-semibold tracking-tight">{post.title}</h2>
                  <p className="mt-2 text-sm leading-6 text-[#727272]">{post.excerpt}</p>
                  <Link
                    to={`/blog/${post.slug}`}
                    className="mt-4 inline-flex items-center gap-1 text-sm font-semibold underline underline-offset-2"
                  >
                    Ler dica
                    <ArrowRight className="h-3.5 w-3.5" />
                  </Link>
                </div>
              </div>
            </motion.article>
          ))}
        </div>
      </div>
      <SiteFooter />
    </div>
  )
}
