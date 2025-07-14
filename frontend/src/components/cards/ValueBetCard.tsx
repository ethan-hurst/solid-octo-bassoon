import { ValueBet } from '@/types'
import { formatDistanceToNow } from 'date-fns'

interface ValueBetCardProps {
  bet: ValueBet
  onPlace: (bet: ValueBet) => void
}

export const ValueBetCard = ({ bet, onPlace }: ValueBetCardProps) => {
  const { market, edge, expected_value, confidence_score, kelly_fraction } = bet
  
  return (
    <div className="bg-gray-800 rounded-lg p-4 border border-gray-700 hover:border-blue-500 transition-colors">
      <div className="flex justify-between items-start mb-3">
        <div>
          <h3 className="text-lg font-semibold">{market.home_team} vs {market.away_team}</h3>
          <p className="text-sm text-gray-400">{market.sport.toUpperCase()}</p>
        </div>
        <span className="text-green-400 font-mono text-lg">
          {(edge * 100).toFixed(1)}% edge
        </span>
      </div>
      
      <div className="grid grid-cols-2 gap-3 mb-4">
        <div className="text-sm">
          <span className="text-gray-400">Best Odds:</span>
          <span className="ml-2 font-mono">{market.bookmaker_odds[0]?.odds.toFixed(2)}</span>
        </div>
        <div className="text-sm">
          <span className="text-gray-400">EV:</span>
          <span className="ml-2 font-mono text-green-400">
            +{(expected_value * 100).toFixed(1)}%
          </span>
        </div>
        <div className="text-sm">
          <span className="text-gray-400">Confidence:</span>
          <span className="ml-2">{(confidence_score * 100).toFixed(0)}%</span>
        </div>
        <div className="text-sm">
          <span className="text-gray-400">Kelly:</span>
          <span className="ml-2">{(kelly_fraction * 100).toFixed(1)}%</span>
        </div>
      </div>
      
      <div className="flex items-center justify-between">
        <span className="text-xs text-gray-500">
          {formatDistanceToNow(new Date(bet.created_at), { addSuffix: true })}
        </span>
        <button
          onClick={() => onPlace(bet)}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md transition-colors"
        >
          Place Bet
        </button>
      </div>
    </div>
  )
}