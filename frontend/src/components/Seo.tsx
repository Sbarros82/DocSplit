import { useEffect } from 'react'

const SITE_URL = 'https://doc-split-beta.vercel.app'
const DEFAULT_IMAGE = `${SITE_URL}/og-image.png`

type SeoProps = {
  title: string
  description: string
  path?: string
  image?: string
  type?: 'website' | 'article'
  noindex?: boolean
  jsonLd?: Record<string, unknown> | Record<string, unknown>[]
}

function upsertMeta(attr: 'name' | 'property', key: string, content: string) {
  let el = document.head.querySelector(`meta[${attr}="${key}"]`) as HTMLMetaElement | null
  if (!el) {
    el = document.createElement('meta')
    el.setAttribute(attr, key)
    document.head.appendChild(el)
  }
  el.setAttribute('content', content)
}

function upsertLink(rel: string, href: string) {
  let el = document.head.querySelector(`link[rel="${rel}"]`) as HTMLLinkElement | null
  if (!el) {
    el = document.createElement('link')
    el.setAttribute('rel', rel)
    document.head.appendChild(el)
  }
  el.setAttribute('href', href)
}

/**
 * Atualiza title/description/canonical/Open Graph por rota (SPA).
 * Google e redes sociais leem melhor metadados consistentes com a URL real.
 */
export function Seo({
  title,
  description,
  path = '/',
  image = DEFAULT_IMAGE,
  type = 'website',
  noindex = false,
  jsonLd,
}: SeoProps) {
  useEffect(() => {
    const url = `${SITE_URL}${path.startsWith('/') ? path : `/${path}`}`
    document.title = title
    upsertMeta('name', 'description', description)
    upsertMeta('name', 'robots', noindex ? 'noindex, nofollow' : 'index, follow')
    upsertLink('canonical', url)

    upsertMeta('property', 'og:title', title)
    upsertMeta('property', 'og:description', description)
    upsertMeta('property', 'og:type', type)
    upsertMeta('property', 'og:url', url)
    upsertMeta('property', 'og:image', image)
    upsertMeta('property', 'og:locale', 'pt_BR')
    upsertMeta('property', 'og:site_name', 'DocSplit')

    upsertMeta('name', 'twitter:card', 'summary_large_image')
    upsertMeta('name', 'twitter:title', title)
    upsertMeta('name', 'twitter:description', description)
    upsertMeta('name', 'twitter:image', image)

    const scriptId = 'docsplit-jsonld'
    const existing = document.getElementById(scriptId)
    if (existing) existing.remove()
    if (jsonLd) {
      const script = document.createElement('script')
      script.id = scriptId
      script.type = 'application/ld+json'
      script.text = JSON.stringify(jsonLd)
      document.head.appendChild(script)
    }

    return () => {
      const s = document.getElementById(scriptId)
      if (s) s.remove()
    }
  }, [title, description, path, image, type, noindex, jsonLd])

  return null
}

export { SITE_URL }
