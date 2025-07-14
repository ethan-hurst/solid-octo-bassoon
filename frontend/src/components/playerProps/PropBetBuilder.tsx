import { useState } from 'react'
import { Player } from '@/types'
import { TrashIcon, PlusIcon } from '@heroicons/react/24/outline'
import { clsx } from 'clsx'

interface PropBetSelection {
  player: Player
  prop_type: string
  selection: 'over' | 'under'
  line: number
  odds: number
  bookmaker: string
}

interface PropBetBuilderProps {
  onSubmit: (selections: PropBetSelection[], stake: number) => void
}

export const PropBetBuilder = ({ onSubmit }: PropBetBuilderProps) => {
  const [selections, setSelections] = useState<PropBetSelection[]>([])
  const [stake, setStake] = useState<number>(10)


  const removeSelection = (index: number) => {
    setSelections(selections.filter((_, i) => i !== index))
  }

  const calculateParlayOdds = () => {
    if (selections.length === 0) return 0
    
    // Convert American odds to decimal and multiply
    const decimalOdds = selections.map(s => {
      if (s.odds > 0) {
        return (s.odds / 100) + 1
      } else {
        return (100 / Math.abs(s.odds)) + 1
      }
    })
    
    const parlayDecimal = decimalOdds.reduce((acc, odds) => acc * odds, 1)
    
    // Convert back to American odds
    if (parlayDecimal >= 2) {
      return Math.round((parlayDecimal - 1) * 100)
    } else {
      return Math.round(-100 / (parlayDecimal - 1))
    }
  }

  const calculatePayout = () => {
    const parlayOdds = calculateParlayOdds()
    if (parlayOdds > 0) {
      return stake + (stake * (parlayOdds / 100))
    } else {
      return stake + (stake * (100 / Math.abs(parlayOdds)))
    }
  }

  const formatOdds = (odds: number) => {
    return odds > 0 ? `+${odds}` : odds.toString()
  }

  return (
    <div className="bg-gray-800 rounded-lg p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="text-xl font-bold">Prop Parlay Builder</h3>
        <span className="text-sm text-gray-400">
          {selections.length} leg{selections.length !== 1 ? 's' : ''}
        </span>
      </div>

      {/* Selected Props */}
      <div className="space-y-3">
        {selections.length === 0 ? (
          <div className="text-center py-8 text-gray-400">
            <PlusIcon className="h-12 w-12 mx-auto mb-2 opacity-50" />
            <p>Add props to build your parlay</p>
          </div>
        ) : (
          selections.map((selection, index) => (
            <div
              key={`${selection.player.id}-${selection.prop_type}-${index}`}
              className="bg-gray-900 rounded-lg p-4 flex items-center justify-between"
            >
              <div className="flex items-center gap-3">
                {selection.player.image_url ? (
                  <img
                    src={selection.player.image_url}
                    alt={selection.player.name}
                    className="w-10 h-10 rounded-full object-cover"
                  />
                ) : (
                  <div className="w-10 h-10 rounded-full bg-gray-700 flex items-center justify-center">
                    <span className="text-sm font-bold">
                      {selection.player.jersey_number || selection.player.name.charAt(0)}
                    </span>
                  </div>
                )}
                <div>
                  <p className="font-medium">{selection.player.name}</p>
                  <p className="text-sm text-gray-400">
                    {selection.selection === 'over' ? 'Over' : 'Under'} {selection.line}{' '}
                    {selection.prop_type} • {formatOdds(selection.odds)}
                  </p>
                </div>
              </div>
              <button
                onClick={() => removeSelection(index)}
                className="text-red-400 hover:text-red-300 p-2"
              >
                <TrashIcon className="h-5 w-5" />
              </button>
            </div>
          ))
        )}
      </div>

      {/* Stake and Calculation */}
      {selections.length > 0 && (
        <div className="space-y-4 pt-4 border-t border-gray-700">
          <div className="flex items-center gap-4">
            <label className="text-sm font-medium text-gray-400">Stake:</label>
            <div className="relative">
              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400">$</span>
              <input
                type="number"
                value={stake}
                onChange={(e) => setStake(Math.max(1, parseInt(e.target.value) || 0))}
                className="bg-gray-900 border border-gray-700 rounded pl-8 pr-4 py-2 w-32 text-right focus:outline-none focus:border-blue-500"
              />
            </div>
          </div>

          <div className="grid grid-cols-3 gap-4 text-center">
            <div>
              <p className="text-sm text-gray-400">Parlay Odds</p>
              <p className="text-2xl font-bold text-blue-400">{formatOdds(calculateParlayOdds())}</p>
            </div>
            <div>
              <p className="text-sm text-gray-400">To Win</p>
              <p className="text-2xl font-bold text-green-400">
                ${(calculatePayout() - stake).toFixed(2)}
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-400">Total Payout</p>
              <p className="text-2xl font-bold">${calculatePayout().toFixed(2)}</p>
            </div>
          </div>

          <button
            onClick={() => onSubmit(selections, stake)}
            className={clsx(
              'w-full py-3 rounded-lg font-medium transition-colors',
              selections.length >= 2
                ? 'bg-blue-600 hover:bg-blue-700 text-white'
                : 'bg-gray-700 text-gray-400 cursor-not-allowed'
            )}
            disabled={selections.length < 2}
          >
            {selections.length < 2
              ? 'Add at least 2 selections for a parlay'
              : `Place ${selections.length}-Leg Parlay`}
          </button>
        </div>
      )}
    </div>
  )
}

// Export the selection type for use in parent components
export type { PropBetSelection }