import { Link } from 'react-router-dom'
import { FileText, Menu, X, Wrench, PencilLine } from 'lucide-react'
import { useState, type MouseEvent } from 'react'
import { LoginModal } from './LoginModal'
import { useAuth } from './AuthProvider'

const TOOLS_URL = '/ferramentas.html'
const EDIT_URL = '/editar.html'

export function Header() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const [loginModalOpen, setLoginModalOpen] = useState(false)
  const { user, profile, signOut } = useAuth()

  const [loginRedirect, setLoginRedirect] = useState('/dashboard')

  const openTools = (event: MouseEvent) => {
    event.preventDefault()
    setMobileMenuOpen(false)
    window.location.href = TOOLS_URL
  }

  const openEditor = (event: MouseEvent) => {
    event.preventDefault()
    setMobileMenuOpen(false)
    window.location.href = EDIT_URL
  }

  const openLogin = (next = '/dashboard') => {
    setMobileMenuOpen(false)
    setLoginRedirect(next)
    setLoginModalOpen(true)
  }

  return (
    <>
      <header className="bg-white border-b border-gray-200 sticky top-0 z-50">
        <div className="max-w-6xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <Link to="/" className="flex items-center gap-2">
              <div className="bg-[#0c0c0c] p-2 rounded-lg">
                <FileText className="h-6 w-6 text-[#b7ff33]" />
              </div>
              <span className="text-xl font-bold text-gray-900">DocSplit</span>
            </Link>

            <nav className="hidden md:flex items-center gap-6">
              <Link to="/" className="text-gray-600 hover:text-gray-900 transition">
                Início
              </Link>
              {user && (
                <>
                  <a
                    href={TOOLS_URL}
                    className="flex items-center gap-1 text-gray-600 hover:text-gray-900 transition"
                    onClick={openTools}
                  >
                    <Wrench className="h-4 w-4" />
                    Ferramentas PDF
                  </a>
                  <a
                    href={EDIT_URL}
                    className="flex items-center gap-1 text-gray-600 hover:text-gray-900 transition"
                    onClick={openEditor}
                  >
                    <PencilLine className="h-4 w-4" />
                    Corrigir texto
                  </a>
                </>
              )}
              <Link to="/pricing" className="text-gray-600 hover:text-gray-900 transition">
                Preços
              </Link>
              {user ? (
                <>
                  <Link to="/dashboard" className="text-gray-600 hover:text-gray-900 transition">
                    Dashboard
                  </Link>
                  {(profile?.role === 'admin' ||
                    user.email?.toLowerCase() === 'sbarros1982@gmail.com') && (
                    <Link to="/admin" className="text-gray-600 hover:text-gray-900 transition">
                      Admin
                    </Link>
                  )}
                  <button
                    onClick={() => signOut()}
                    className="text-gray-600 hover:text-gray-900 transition"
                  >
                    Sair
                  </button>
                </>
              ) : (
                <button
                  onClick={() => openLogin(window.location.pathname || '/dashboard')}
                  className="bg-[#0c0c0c] text-white px-6 py-2 rounded-full hover:bg-black transition"
                >
                  Login
                </button>
              )}
            </nav>

            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="md:hidden p-2 text-gray-600 hover:text-gray-900"
            >
              {mobileMenuOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
            </button>
          </div>

          {mobileMenuOpen && (
            <nav className="md:hidden mt-4 pb-4 border-t border-gray-200 pt-4 flex flex-col gap-3">
              <Link
                to="/"
                className="text-gray-600 hover:text-gray-900 transition"
                onClick={() => setMobileMenuOpen(false)}
              >
                Início
              </Link>
              {user && (
                <>
                  <a
                    href={TOOLS_URL}
                    className="flex items-center gap-1 text-gray-600 hover:text-gray-900 transition"
                    onClick={openTools}
                  >
                    <Wrench className="h-4 w-4" />
                    Ferramentas PDF
                  </a>
                  <a
                    href={EDIT_URL}
                    className="flex items-center gap-1 text-gray-600 hover:text-gray-900 transition"
                    onClick={openEditor}
                  >
                    <PencilLine className="h-4 w-4" />
                    Corrigir texto
                  </a>
                </>
              )}
              <Link
                to="/pricing"
                className="text-gray-600 hover:text-gray-900 transition"
                onClick={() => setMobileMenuOpen(false)}
              >
                Preços
              </Link>
              {user ? (
                <>
                  <Link
                    to="/dashboard"
                    className="text-gray-600 hover:text-gray-900 transition"
                    onClick={() => setMobileMenuOpen(false)}
                  >
                    Dashboard
                  </Link>
                  {(profile?.role === 'admin' ||
                    user.email?.toLowerCase() === 'sbarros1982@gmail.com') && (
                    <Link
                      to="/admin"
                      className="text-gray-600 hover:text-gray-900 transition"
                      onClick={() => setMobileMenuOpen(false)}
                    >
                      Admin
                    </Link>
                  )}
                  <button
                    onClick={() => {
                      signOut()
                      setMobileMenuOpen(false)
                    }}
                    className="text-left text-gray-600 hover:text-gray-900 transition"
                  >
                    Sair
                  </button>
                </>
              ) : (
                <button
                  onClick={() => openLogin(window.location.pathname || '/dashboard')}
                  className="bg-[#0c0c0c] text-white px-6 py-2 rounded-full hover:bg-black transition text-left"
                >
                  Login
                </button>
              )}
            </nav>
          )}
        </div>
      </header>

      <LoginModal
        isOpen={loginModalOpen}
        onClose={() => setLoginModalOpen(false)}
        redirectTo={loginRedirect}
      />
    </>
  )
}
