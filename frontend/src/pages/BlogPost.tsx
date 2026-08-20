import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { ArrowLeft } from 'lucide-react'
import { Header } from '@/components/Header'
import { SiteFooter } from '@/components/SiteFooter'
import { markdownToHtml } from '@/lib/markdown'

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000'

type Post = {
  slug: string
  title: string
  excerpt: string
  body_md: string
  published_at: string | null
  author_email: string | null
}

export function BlogPost() {
  const { slug } = useParams<{ slug: string }>()
  const [post, setPost] = useState<Post | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!slug) return
    ;(async () => {
      try {
        const r = await fetch(`${BACKEND_URL}/api/blog/posts/${encodeURIComponent(slug)}`)
        if (r.status === 404) throw new Error('Post não encontrado')
        if (!r.ok) throw new Error('Erro ao carregar o post')
        const data = await r.json()
        setPost(data.post)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Erro')
      } finally {
        setLoading(false)
      }
    })()
  }, [slug])

  return (
    <div className="min-h-screen bg-white text-[#0c0c0c]">
      <Header />
      <main className="mx-auto max-w-3xl px-6 py-14">
        <Link to="/blog" className="inline-flex items-center gap-1 text-sm text-[#727272] hover:text-[#0c0c0c]">
          <ArrowLeft className="h-4 w-4" />
          Voltar ao blog
        </Link>

        {loading && <p className="mt-16 text-center text-[#727272]">Carregando...</p>}
        {error && (
          <div className="mt-16 text-center">
            <p className="text-[#727272]">{error}</p>
            <Link to="/blog" className="mt-4 inline-block font-semibold underline">
              Ver todas as dicas
            </Link>
          </div>
        )}

        {post && (
          <article className="mt-8">
            {post.published_at && (
              <p className="text-sm text-[#9b9b9b]">
                {new Date(post.published_at).toLocaleDateString('pt-BR')}
              </p>
            )}
            <div
              className="blog-body"
              dangerouslySetInnerHTML={{ __html: markdownToHtml(post.body_md) }}
            />
            {post.excerpt && (
              <p className="mt-10 rounded-2xl border border-black/8 bg-[#f7f8fa] p-5 text-sm text-[#727272]">
                {post.excerpt}
              </p>
            )}
          </article>
        )}
      </main>
      <SiteFooter />
    </div>
  )
}
