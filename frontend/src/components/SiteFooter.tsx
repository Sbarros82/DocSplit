import { Link } from 'react-router-dom'
import { Lock } from 'lucide-react'
import { APP_VERSION } from '@/lib/version'

export function SiteFooter() {
  return (
    <footer className="border-t border-black/10 px-6 py-10 text-center text-sm text-[#727272]">
      <p className="flex items-center justify-center gap-2">
        <Lock className="h-4 w-4" />
        © 2026 DocSplit. Arquivos processados e removidos em seguida.
      </p>
      <p className="mt-2">
        <Link to="/privacy" className="hover:text-[#0c0c0c]">
          Privacidade
        </Link>
        {' · '}
        <Link to="/terms" className="hover:text-[#0c0c0c]">
          Termos de Uso
        </Link>
        {' · '}
        <span>v{APP_VERSION}</span>
      </p>
    </footer>
  )
}
