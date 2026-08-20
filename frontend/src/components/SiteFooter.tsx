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
        Desenvolvido por{' '}
        <a
          href="https://sergio-portfolio-three.vercel.app/"
          target="_blank"
          rel="noopener noreferrer"
          className="font-medium text-[#0c0c0c] underline underline-offset-2 hover:text-[#727272]"
        >
          Sergio Barros
        </a>
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
        <Link to="/blog" className="hover:text-[#0c0c0c]">
          Blog
        </Link>
        {' · '}
        <span>v{APP_VERSION}</span>
      </p>
    </footer>
  )
}
