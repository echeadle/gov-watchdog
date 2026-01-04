import { Link, useLocation } from 'react-router-dom'
import { MessageSquare, Users, Home, FileText } from 'lucide-react'

const navItems = [
  { path: '/', label: 'Home', icon: Home },
  { path: '/members', label: 'Members', icon: Users },
  { path: '/bills', label: 'Bills', icon: FileText },
  { path: '/chat', label: 'AI Assistant', icon: MessageSquare },
]

export default function Header() {
  const location = useLocation()

  return (
    <header className="bg-white border-b-4 border-primary-600 sticky top-0 z-50 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Masthead - Editorial Style */}
        <div className="py-6 border-b border-slate-200">
          <div className="flex items-baseline justify-between">
            {/* Logo - Bold, Editorial */}
            <Link to="/" className="group flex items-baseline gap-3">
              <h1 className="font-display text-3xl md:text-4xl font-black tracking-tight text-slate-900 group-hover:text-primary-600 transition-colors">
                Gov Watchdog
              </h1>
              <span className="hidden md:inline font-mono text-xs uppercase tracking-wider text-slate-500">
                Congressional Oversight
              </span>
            </Link>

            {/* Secondary Navigation - Simple */}
            <div className="flex items-center gap-2">
              <span className="hidden sm:inline text-sm text-slate-500 font-mono">
                Live Data
              </span>
              <div className="w-2 h-2 bg-accent-500 rounded-full animate-pulse" />
            </div>
          </div>
        </div>

        {/* Main Navigation - Tab Style */}
        <nav className="flex gap-1 py-3">
          {navItems.map(({ path, label, icon: Icon }) => {
            const isActive = location.pathname === path ||
                            (path !== '/' && location.pathname.startsWith(path))

            return (
              <Link
                key={path}
                to={path}
                className={`
                  flex items-center gap-2 px-4 py-2 font-medium text-sm
                  border-b-2 transition-all duration-200
                  ${isActive
                    ? 'border-primary-600 text-primary-600'
                    : 'border-transparent text-slate-600 hover:text-slate-900 hover:border-slate-300'
                  }
                `}
              >
                <Icon className="w-4 h-4" />
                <span className="hidden sm:inline">{label}</span>
              </Link>
            )
          })}
        </nav>
      </div>
    </header>
  )
}
