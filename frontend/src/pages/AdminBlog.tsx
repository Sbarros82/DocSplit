import { FormEvent, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { ArrowLeft, PencilLine, Plus, Trash2 } from 'lucide-react'
import { toast } from 'sonner'
import { Header } from '@/components/Header'
import { SiteFooter } from '@/components/SiteFooter'
import { useAuth } from '@/components/AuthProvider'

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000'

type Post = {
  id: string
  slug: string
  title: string
  excerpt: string
  body_md: string
  published: boolean
  published_at: string | null
  updated_at: string
}

const EMPTY = {
  title: '',
  excerpt: '',
  body_md: '',
  published: true,
}

export function AdminBlog() {
  const { user, loading: authLoading, getAccessToken } = useAuth()
  const [allowed, setAllowed] = useState(false)
  const [checking, setChecking] = useState(true)
  const [posts, setPosts] = useState<Post[]>([])
  const [editingId, setEditingId] = useState<string | null>(null)
  const [form, setForm] = useState(EMPTY)
  const [saving, setSaving] = useState(false)

  const authHeaders = async () => {
    const token = await getAccessToken()
    if (!token) throw new Error('Sessão expirada')
    return {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
    }
  }

  const loadPosts = async () => {
    const headers = await authHeaders()
    const r = await fetch(`${BACKEND_URL}/api/blog/posts?include_drafts=true`, { headers })
    if (!r.ok) throw new Error('Falha ao listar posts')
    const data = await r.json()
    setPosts(data.posts || [])
  }

  useEffect(() => {
    if (authLoading) return
    if (!user) {
      window.location.href = '/login?next=' + encodeURIComponent('/admin/blog')
      return
    }
    ;(async () => {
      try {
        const headers = await authHeaders()
        const me = await fetch(`${BACKEND_URL}/api/admin/me`, { headers })
        if (!me.ok) {
          setAllowed(false)
          return
        }
        setAllowed(true)
        await loadPosts()
      } catch (error) {
        toast.error(error instanceof Error ? error.message : 'Erro')
        setAllowed(false)
      } finally {
        setChecking(false)
      }
    })()
  }, [user, authLoading])

  const resetForm = () => {
    setEditingId(null)
    setForm(EMPTY)
  }

  const onEdit = (post: Post) => {
    setEditingId(post.id)
    setForm({
      title: post.title,
      excerpt: post.excerpt || '',
      body_md: post.body_md || '',
      published: post.published,
    })
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  const onSubmit = async (event: FormEvent) => {
    event.preventDefault()
    setSaving(true)
    try {
      const headers = await authHeaders()
      const url = editingId
        ? `${BACKEND_URL}/api/blog/admin/posts/${editingId}`
        : `${BACKEND_URL}/api/blog/admin/posts`
      const r = await fetch(url, {
        method: editingId ? 'PUT' : 'POST',
        headers,
        body: JSON.stringify(form),
      })
      const data = await r.json().catch(() => ({}))
      if (!r.ok) {
        throw new Error(typeof data.detail === 'string' ? data.detail : 'Falha ao salvar')
      }
      toast.success(editingId ? 'Post atualizado' : 'Post criado')
      resetForm()
      await loadPosts()
    } catch (error) {
      toast.error(error instanceof Error ? error.message : 'Erro ao salvar')
    } finally {
      setSaving(false)
    }
  }

  const onDelete = async (id: string) => {
    if (!window.confirm('Excluir este post?')) return
    try {
      const headers = await authHeaders()
      const r = await fetch(`${BACKEND_URL}/api/blog/admin/posts/${id}`, {
        method: 'DELETE',
        headers,
      })
      if (!r.ok) throw new Error('Falha ao excluir')
      toast.success('Post excluído')
      if (editingId === id) resetForm()
      await loadPosts()
    } catch (error) {
      toast.error(error instanceof Error ? error.message : 'Erro ao excluir')
    }
  }

  if (checking || authLoading) {
    return (
      <div className="min-h-screen bg-white">
        <Header />
        <p className="p-10 text-center text-[#727272]">Carregando...</p>
      </div>
    )
  }

  if (!allowed) {
    return (
      <div className="min-h-screen bg-white">
        <Header />
        <div className="mx-auto max-w-lg px-6 py-20 text-center">
          <h1 className="text-2xl font-semibold">Acesso negado</h1>
          <Link to="/dashboard" className="mt-6 inline-block rounded-full bg-[#0c0c0c] px-5 py-2.5 text-sm font-semibold text-white">
            Voltar
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-white text-[#0c0c0c]">
      <Header />
      <section className="px-6 pb-6 pt-12">
        <div className="mx-auto max-w-5xl">
          <Link to="/admin" className="inline-flex items-center gap-1 text-sm text-[#727272] hover:text-[#0c0c0c]">
            <ArrowLeft className="h-4 w-4" />
            Voltar ao admin
          </Link>
          <h1 className="mt-3 text-3xl font-semibold tracking-tight">Blog · dicas de uso</h1>
          <p className="mt-2 text-[#727272]">
            Crie e publique artigos. Markdown simples: # título, ## seção, - lista, **negrito**.
          </p>
        </div>
      </section>

      <div className="mx-auto grid max-w-5xl gap-6 px-6 pb-16 lg:grid-cols-2">
        <form onSubmit={onSubmit} className="rounded-2xl border border-black/8 bg-[#f7f8fa] p-6">
          <h2 className="mb-4 flex items-center gap-2 text-lg font-semibold">
            {editingId ? <PencilLine className="h-5 w-5" /> : <Plus className="h-5 w-5" />}
            {editingId ? 'Editar post' : 'Novo post'}
          </h2>
          <label className="mb-3 block text-sm">
            Título
            <input
              required
              value={form.title}
              onChange={(e) => setForm((f) => ({ ...f, title: e.target.value }))}
              className="mt-1 w-full rounded-xl border border-black/10 bg-white px-3 py-2.5"
            />
          </label>
          <label className="mb-3 block text-sm">
            Resumo (lista do blog)
            <textarea
              value={form.excerpt}
              onChange={(e) => setForm((f) => ({ ...f, excerpt: e.target.value }))}
              rows={2}
              className="mt-1 w-full rounded-xl border border-black/10 bg-white px-3 py-2.5"
            />
          </label>
          <label className="mb-3 block text-sm">
            Conteúdo (Markdown)
            <textarea
              required
              value={form.body_md}
              onChange={(e) => setForm((f) => ({ ...f, body_md: e.target.value }))}
              rows={14}
              className="mt-1 w-full rounded-xl border border-black/10 bg-white px-3 py-2.5 font-mono text-sm"
              placeholder={'# Título\n\nTexto...\n\n## Seção\n\n- item 1\n- item 2'}
            />
          </label>
          <label className="mb-4 flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={form.published}
              onChange={(e) => setForm((f) => ({ ...f, published: e.target.checked }))}
            />
            Publicar agora
          </label>
          <div className="flex gap-2">
            <button
              type="submit"
              disabled={saving}
              className="flex-1 rounded-full bg-[#b7ff33] py-3 text-sm font-semibold text-[#0c0c0c] hover:bg-[#c8ff66] disabled:opacity-50"
            >
              {saving ? 'Salvando...' : editingId ? 'Salvar alterações' : 'Criar post'}
            </button>
            {editingId && (
              <button
                type="button"
                onClick={resetForm}
                className="rounded-full border border-black/15 bg-white px-4 py-3 text-sm font-semibold"
              >
                Cancelar
              </button>
            )}
          </div>
        </form>

        <div className="rounded-2xl border border-black/8 bg-white p-6">
          <h2 className="mb-4 text-lg font-semibold">Posts</h2>
          <div className="divide-y divide-black/8">
            {posts.map((post) => (
              <div key={post.id} className="flex items-start justify-between gap-3 py-3">
                <div className="min-w-0">
                  <p className="font-medium">{post.title}</p>
                  <p className="text-sm text-[#727272]">
                    /{post.slug} · {post.published ? 'publicado' : 'rascunho'}
                  </p>
                </div>
                <div className="flex shrink-0 gap-1">
                  <button
                    type="button"
                    onClick={() => onEdit(post)}
                    className="rounded-full bg-[#f4f5f7] p-2"
                    aria-label="Editar"
                  >
                    <PencilLine className="h-4 w-4" />
                  </button>
                  <button
                    type="button"
                    onClick={() => onDelete(post.id)}
                    className="rounded-full bg-[#f4f5f7] p-2"
                    aria-label="Excluir"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              </div>
            ))}
            {posts.length === 0 && <p className="py-8 text-center text-[#727272]">Nenhum post ainda.</p>}
          </div>
          <Link to="/blog" className="mt-4 inline-block text-sm font-semibold underline underline-offset-2">
            Ver blog público
          </Link>
        </div>
      </div>
      <SiteFooter />
    </div>
  )
}
