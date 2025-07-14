import { NavLink } from 'react-router-dom'
import { 
  HomeIcon, 
  ChartBarIcon, 
  BellIcon,
  CurrencyDollarIcon,
  CogIcon,
  ChartPieIcon,
  UserGroupIcon,
  SparklesIcon,
  BeakerIcon
} from '@heroicons/react/24/outline'

const navigation = [
  { name: 'Dashboard', href: '/', icon: HomeIcon },
  { name: 'Live Odds', href: '/odds', icon: CurrencyDollarIcon },
  { name: 'Analysis', href: '/analysis', icon: ChartBarIcon },
  { name: 'Player Props', href: '/player-props', icon: SparklesIcon },
  { name: 'Social Trading', href: '/social', icon: UserGroupIcon },
  { name: 'Portfolio', href: '/portfolio', icon: ChartPieIcon },
  { name: 'Strategies', href: '/strategies', icon: BeakerIcon },
  { name: 'Alerts', href: '/alerts', icon: BellIcon },
  { name: 'Settings', href: '/settings', icon: CogIcon },
]

export const Sidebar = () => {
  return (
    <div className="flex flex-col w-64 bg-gray-800 border-r border-gray-700">
      <nav className="flex-1 px-2 py-4 space-y-1">
        {navigation.map((item) => (
          <NavLink
            key={item.name}
            to={item.href}
            className={({ isActive }) =>
              `group flex items-center px-2 py-2 text-sm font-medium rounded-md transition-colors ${
                isActive
                  ? 'bg-gray-900 text-white'
                  : 'text-gray-300 hover:bg-gray-700 hover:text-white'
              }`
            }
          >
            <item.icon
              className="mr-3 flex-shrink-0 h-6 w-6"
              aria-hidden="true"
            />
            {item.name}
          </NavLink>
        ))}
      </nav>
    </div>
  )
}