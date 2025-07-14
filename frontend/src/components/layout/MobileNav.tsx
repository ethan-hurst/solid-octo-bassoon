import { NavLink } from 'react-router-dom'
import { 
  HomeIcon, 
  ChartBarIcon, 
  UserGroupIcon,
  ChartPieIcon,
  Bars3Icon
} from '@heroicons/react/24/outline'
import { clsx } from 'clsx'

const mobileNavigation = [
  { name: 'Home', href: '/', icon: HomeIcon },
  { name: 'Analysis', href: '/analysis', icon: ChartBarIcon },
  { name: 'Social', href: '/social', icon: UserGroupIcon },
  { name: 'Portfolio', href: '/portfolio', icon: ChartPieIcon },
  { name: 'More', href: '#', icon: Bars3Icon },
]

interface MobileNavProps {
  onMenuClick: () => void
}

export const MobileNav = ({ onMenuClick }: MobileNavProps) => {
  return (
    <nav className="fixed bottom-0 left-0 right-0 bg-gray-900 border-t border-gray-700 md:hidden z-50">
      <div className="grid grid-cols-5 h-16">
        {mobileNavigation.map((item) => {
          if (item.name === 'More') {
            return (
              <button
                key={item.name}
                onClick={onMenuClick}
                className="flex flex-col items-center justify-center text-gray-400 hover:text-white transition-colors"
              >
                <item.icon className="h-6 w-6" />
                <span className="text-xs mt-1">{item.name}</span>
              </button>
            )
          }

          return (
            <NavLink
              key={item.name}
              to={item.href}
              className={({ isActive }) =>
                clsx(
                  'flex flex-col items-center justify-center transition-colors',
                  isActive ? 'text-blue-400' : 'text-gray-400 hover:text-white'
                )
              }
            >
              <item.icon className="h-6 w-6" />
              <span className="text-xs mt-1">{item.name}</span>
            </NavLink>
          )
        })}
      </div>
    </nav>
  )
}