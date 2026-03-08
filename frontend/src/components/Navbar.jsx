import { NavLink } from 'react-router-dom'

const NAV_LINKS = [
  { to: '/',        label: 'Dashboard'    },
  { to: '/brief',   label: 'Weekly Brief' },
  { to: '/settings', label: 'Settings'   },
]

export default function Navbar() {
  return (
    <nav style={{ backgroundColor: '#1a1a2e' }} className="shadow-lg">
      <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">

        {/* Branding */}
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-blue-500 flex items-center justify-center flex-shrink-0">
            <span className="text-white font-bold text-sm">P</span>
          </div>
          <span className="text-white font-bold text-lg tracking-tight">
            Prop<span className="text-blue-400">Pulse</span>
          </span>
          <span className="text-gray-500 text-xs ml-1 hidden sm:block">
            Melbourne Property Intelligence
          </span>
        </div>

        {/* Nav links */}
        <div className="flex items-center gap-1">
          {NAV_LINKS.map(({ to, label }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              className={({ isActive }) =>
                `px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-blue-600 text-white'
                    : 'text-gray-300 hover:text-white hover:bg-white/10'
                }`
              }
            >
              {label}
            </NavLink>
          ))}
        </div>

      </div>
    </nav>
  )
}
