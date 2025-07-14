import { ArrowUpIcon, ArrowDownIcon } from '@heroicons/react/24/solid'

interface StatsCardProps {
  title: string
  value: string | number
  change?: number
}

export const StatsCard = ({ title, value, change }: StatsCardProps) => {
  const isPositive = change && change > 0
  const isNegative = change && change < 0

  return (
    <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
      <p className="text-sm text-gray-400 mb-1">{title}</p>
      <p className="text-2xl font-bold">{value}</p>
      {change !== undefined && (
        <div className="flex items-center mt-2">
          {isPositive && (
            <>
              <ArrowUpIcon className="h-4 w-4 text-green-500 mr-1" />
              <span className="text-sm text-green-500">+{change}%</span>
            </>
          )}
          {isNegative && (
            <>
              <ArrowDownIcon className="h-4 w-4 text-red-500 mr-1" />
              <span className="text-sm text-red-500">{change}%</span>
            </>
          )}
          {change === 0 && (
            <span className="text-sm text-gray-400">No change</span>
          )}
        </div>
      )}
    </div>
  )
}