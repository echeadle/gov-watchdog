import { Link, useLocation } from 'react-router-dom'
import { Search, MessageSquare, Users } from 'lucide-react'

const navItems = [
  { path: '/', label: 'Home', icon: Search },
  { path: '/members', label: 'Members', icon: Users },
  { path: '/chat', label: 'AI Assistant', icon: MessageSquare },
]

export default function Header() {
  const location = useLocation()

  return (
    <header className="bg-white border-b border-gray-200 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link to="/" className="flex items-center space-x-2">
            <span className="text-2xl">🏛️</span>
            <span className="font-bold text-xl text-gray-900">Gov Watchdog</span>
          </Link>

          {/* Navigation */}
          <nav className="flex space-x-1">
            {navItems.map(({ path, label, icon: Icon }) => {
              const isActive = location.pathname === path
              return (
                <Link
                  key={path}
                  to={path}
                  className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition-colors ${
                    isActive
                      ? 'bg-blue-100 text-blue-700'
                      : 'text-gray-600 hover:bg-gray-100'
                  }`}
                >
                  <Icon className="w-5 h-5" />
                  <span className="hidden sm:inline">{label}</span>
                </Link>
              )
            })}
          </nav>
        </div>
      </div>
    </header>
  )
}
