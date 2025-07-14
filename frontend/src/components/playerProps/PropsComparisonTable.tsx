import { PropComparison } from '@/types'
import { ArrowUpIcon, ArrowDownIcon } from '@heroicons/react/24/solid'
import { clsx } from 'clsx'

interface PropsComparisonTableProps {
  comparisons: PropComparison[]
  onSelectBet: (comparison: PropComparison, type: 'over' | 'under', bookmaker: string) => void
}

export const PropsComparisonTable = ({ comparisons, onSelectBet }: PropsComparisonTableProps) => {
  const formatOdds = (odds: number) => {
    return odds > 0 ? `+${odds}` : odds.toString()
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full">
        <thead>
          <tr className="border-b border-gray-700">
            <th className="text-left py-3 px-4 text-sm font-medium text-gray-400">Player</th>
            <th className="text-left py-3 px-4 text-sm font-medium text-gray-400">Prop</th>
            <th className="text-center py-3 px-4 text-sm font-medium text-gray-400">Best Over</th>
            <th className="text-center py-3 px-4 text-sm font-medium text-gray-400">Best Under</th>
            <th className="text-right py-3 px-4 text-sm font-medium text-gray-400">All Lines</th>
          </tr>
        </thead>
        <tbody>
          {comparisons.map((comparison, index) => (
            <tr
              key={`${comparison.player.id}-${comparison.prop_type}`}
              className={clsx(
                'border-b border-gray-800 hover:bg-gray-800/50 transition-colors',
                index % 2 === 0 ? 'bg-gray-900/30' : ''
              )}
            >
              <td className="py-4 px-4">
                <div className="flex items-center gap-3">
                  {comparison.player.image_url ? (
                    <img
                      src={comparison.player.image_url}
                      alt={comparison.player.name}
                      className="w-10 h-10 rounded-full object-cover"
                    />
                  ) : (
                    <div className="w-10 h-10 rounded-full bg-gray-700 flex items-center justify-center">
                      <span className="text-sm font-bold">
                        {comparison.player.jersey_number || comparison.player.name.charAt(0)}
                      </span>
                    </div>
                  )}
                  <div>
                    <p className="font-medium">{comparison.player.name}</p>
                    <p className="text-xs text-gray-400">{comparison.player.team}</p>
                  </div>
                </div>
              </td>
              <td className="py-4 px-4">
                <p className="font-medium capitalize">{comparison.prop_type.replace(/_/g, ' ')}</p>
                <p className="text-sm text-gray-400">
                  Line: {comparison.lines[0]?.line || 'N/A'}
                </p>
              </td>
              <td className="py-4 px-4 text-center">
                <button
                  onClick={() => onSelectBet(comparison, 'over', comparison.best_over.bookmaker)}
                  className="inline-flex items-center gap-1 px-3 py-1.5 bg-green-900/30 hover:bg-green-900/50 text-green-400 rounded transition-colors"
                >
                  <ArrowUpIcon className="h-3 w-3" />
                  <span className="font-mono">{formatOdds(comparison.best_over.odds)}</span>
                </button>
                <p className="text-xs text-gray-400 mt-1">{comparison.best_over.bookmaker}</p>
              </td>
              <td className="py-4 px-4 text-center">
                <button
                  onClick={() => onSelectBet(comparison, 'under', comparison.best_under.bookmaker)}
                  className="inline-flex items-center gap-1 px-3 py-1.5 bg-red-900/30 hover:bg-red-900/50 text-red-400 rounded transition-colors"
                >
                  <ArrowDownIcon className="h-3 w-3" />
                  <span className="font-mono">{formatOdds(comparison.best_under.odds)}</span>
                </button>
                <p className="text-xs text-gray-400 mt-1">{comparison.best_under.bookmaker}</p>
              </td>
              <td className="py-4 px-4 text-right">
                <details className="relative">
                  <summary className="cursor-pointer text-sm text-blue-400 hover:text-blue-300">
                    View all ({comparison.lines.length})
                  </summary>
                  <div className="absolute right-0 mt-2 w-64 bg-gray-900 border border-gray-700 rounded-lg shadow-xl z-10 p-3">
                    <div className="space-y-2">
                      {comparison.lines.map((line) => (
                        <div key={line.bookmaker} className="flex justify-between text-sm">
                          <span className="text-gray-400">{line.bookmaker}</span>
                          <div className="flex gap-2">
                            <button
                              onClick={() => onSelectBet(comparison, 'over', line.bookmaker)}
                              className="text-green-400 hover:text-green-300 font-mono"
                            >
                              O{line.line} {formatOdds(line.over_odds)}
                            </button>
                            <span className="text-gray-600">|</span>
                            <button
                              onClick={() => onSelectBet(comparison, 'under', line.bookmaker)}
                              className="text-red-400 hover:text-red-300 font-mono"
                            >
                              U{line.line} {formatOdds(line.under_odds)}
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </details>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}