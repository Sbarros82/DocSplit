import { Link } from 'react-router-dom'
import { FileText, Menu, X } from 'lucide-react'
import { useState } from 'react'
import { LoginModal } from './LoginModal'
import { useAuth } from './AuthProvider'

export function Header() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const [loginModalOpen, setLoginModalOpen] = useState(false)
  const { user, signOut } = useAuth()

  return (
    <>
      <header className="bg-white border-b border-gray-200 sticky top-0 z-50">
        <div className="max-w-6xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            {/* Logo */}
            <Link to="/" className="flex items-center gap-2">
              <div className="bg-blue-600 p-2 rounded-lg">
                <FileText className="h-6 w-6 text-white" />
              </div>
              <span className="text-xl font-bold text-gray-900">DocSplit</span>
            </Link>

            {/* Desktop Navigation */}
            <nav className="hidden md:flex items-center gap-6">
              <Link to="/" className="text-gray-600 hover:text-gray-900 transition">
                Início
              </Link>
              <Link to="/pricing" className="text-gray-600 hover:text-gray-900 transition">
                Preços
              </Link>
              {user ? (
                <>
                  <Link to="/dashboard" className="text-gray-600 hover:text-gray-900 transition">
                    Dashboard
                  </Link>
                  <button
                    onClick={() => signOut()}
                    className="text-gray-600 hover:text-gray-900 transition"
                  >
                    Sair
                  </button>
                </>
              ) : (
                <button
                  onClick={() => setLoginModalOpen(true)}
                  className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition"
                >
                  Login
                </button>
              )}
            </nav>

            {/* Mobile Menu Button */}
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="md:hidden p-2 text-gray-600 hover:text-gray-900"
            >
              {mobileMenuOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
            </button>
          </div>

          {/* Mobile Menu */}
          {mobileMenuOpen && (
            <nav className="md:hidden mt-4 pb-4 border-t border-gray-200 pt-4 flex flex-col gap-3">
              <Link
                to="/"
                className="text-gray-600 hover:text-gray-900 transition"
                onClick={() => setMobileMenuOpen(false)}
              >
                Início
              </Link>
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
                  onClick={() => {
                    setLoginModalOpen(true)
                    setMobileMenuOpen(false)
                  }}
                  className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition text-left"
                >
                  Login
                </button>
              )}
            </nav>
          )}
        </div>
      </header>

      <LoginModal isOpen={loginModalOpen} onClose={() => setLoginModalOpen(false)} />
    </>
  )
}
