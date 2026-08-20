/** Helpers de redirecionamento pós-login. */

const DEFAULT_NEXT = '/dashboard'

/** Normaliza o destino após login (evita open-redirect). */
export function sanitizeNextPath(raw: string | null | undefined): string {
  if (!raw) return DEFAULT_NEXT
  const path = raw.trim()
  if (!path.startsWith('/') || path.startsWith('//') || path.includes('://')) {
    return DEFAULT_NEXT
  }
  return path
}

/** URL absoluta do callback OAuth (sempre cai na página React /login). */
export function oauthCallbackUrl(nextPath: string): string {
  const next = sanitizeNextPath(nextPath)
  return `${window.location.origin}/login?next=${encodeURIComponent(next)}`
}

/** Navega para o destino após login (HTML estático vs rota React). */
export function goToAfterLogin(nextPath: string): void {
  const next = sanitizeNextPath(nextPath)
  if (next.endsWith('.html') || next.startsWith('/ferramentas') || next.startsWith('/editar')) {
    window.location.href = next
    return
  }
  window.location.href = next
}

export function loginUrlWithNext(nextPath: string): string {
  return `/login?next=${encodeURIComponent(sanitizeNextPath(nextPath))}`
}
