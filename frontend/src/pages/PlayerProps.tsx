import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { apiClient } from '@/api/client'
import { Player, PropBet, PropComparison, SportType } from '@/types'
import { PlayerSearch } from '@/components/playerProps/PlayerSearch'
import { PlayerPerformanceCard } from '@/components/playerProps/PlayerPerformanceCard'
import { PropsComparisonTable } from '@/components/playerProps/PropsComparisonTable'
import { PropBetBuilder, PropBetSelection } from '@/components/playerProps/PropBetBuilder'
import toast from 'react-hot-toast'

export const PlayerProps = () => {
  const [selectedPlayer, setSelectedPlayer] = useState<Player | null>(null)
  const [selectedSport, setSelectedSport] = useState<SportType>(SportType.NBA)

  // Fetch available prop bets
  const { data: propBets } = useQuery({
    queryKey: ['propBets', selectedSport],
    queryFn: async () => {
      const { data } = await apiClient.get<PropBet[]>(`/props/bets?sport=${selectedSport}`)
      return data
    },
  })

  // Fetch prop comparisons
  const { data: comparisons } = useQuery({
    queryKey: ['propComparisons', selectedPlayer?.id],
    queryFn: async () => {
      if (!selectedPlayer) return []
      const { data } = await apiClient.get<PropComparison[]>(
        `/props/comparisons?player_id=${selectedPlayer.id}`
      )
      return data
    },
    enabled: !!selectedPlayer,
  })

  const handleSelectPlayer = (player: Player) => {
    setSelectedPlayer(player)
  }

  const handleSelectBet = (
    comparison: PropComparison,
    _type: 'over' | 'under',
    bookmaker: string
  ) => {
    const line = comparison.lines.find(l => l.bookmaker === bookmaker)
    if (!line) return

    // Add to prop bet builder in the PropBetBuilder component
    // This is handled by the PropBetBuilder component itself
    toast.success(`Added ${comparison.player.name} to parlay builder`)
  }

  const handleSubmitParlay = async (selections: PropBetSelection[], stake: number) => {
    try {
      await apiClient.post('/props/parlay', {
        selections: selections.map(s => ({
          player_id: s.player.id,
          prop_type: s.prop_type,
          selection: s.selection,
          line: s.line,
          bookmaker: s.bookmaker,
        })),
        stake,
      })
      toast.success('Parlay placed successfully!')
    } catch (error) {
      toast.error('Failed to place parlay')
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">Player Props Intelligence</h1>
        <select
          value={selectedSport}
          onChange={(e) => setSelectedSport(e.target.value as SportType)}
          className="bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-blue-500"
        >
          <option value={SportType.NBA}>NBA</option>
          <option value={SportType.NFL}>NFL</option>
          <option value={SportType.MLB}>MLB</option>
          <option value={SportType.NHL}>NHL</option>
        </select>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Content */}
        <div className="lg:col-span-2 space-y-6">
          {/* Player Search */}
          <div className="bg-gray-800 rounded-lg p-6">
            <h2 className="text-xl font-semibold mb-4">Find Players</h2>
            <PlayerSearch sport={selectedSport} onSelectPlayer={handleSelectPlayer} />
          </div>

          {/* Selected Player Performance */}
          {selectedPlayer && (
            <PlayerPerformanceCard player={selectedPlayer} />
          )}

          {/* Props Comparison Table */}
          {comparisons && comparisons.length > 0 && (
            <div className="bg-gray-800 rounded-lg p-6">
              <h2 className="text-xl font-semibold mb-4">Available Props</h2>
              <PropsComparisonTable
                comparisons={comparisons}
                onSelectBet={handleSelectBet}
              />
            </div>
          )}

          {/* Top Value Props */}
          {propBets && propBets.length > 0 && (
            <div className="bg-gray-800 rounded-lg p-6">
              <h2 className="text-xl font-semibold mb-4">AI Recommended Props</h2>
              <div className="space-y-4">
                {propBets.slice(0, 5).map((bet) => (
                  <div
                    key={bet.id}
                    className="bg-gray-900 rounded-lg p-4 flex items-center justify-between"
                  >
                    <div className="flex items-center gap-4">
                      <div className="text-center">
                        <p className="text-2xl font-bold text-blue-400">
                          {(bet.confidence * 100).toFixed(0)}%
                        </p>
                        <p className="text-xs text-gray-400">Confidence</p>
                      </div>
                      <div>
                        <p className="font-medium">
                          {bet.player.name} {bet.prediction} {bet.line} {bet.prop_type}
                        </p>
                        <p className="text-sm text-gray-400">{bet.reasoning}</p>
                      </div>
                    </div>
                    <button className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded transition-colors">
                      Bet {bet.prediction}
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Sidebar - Prop Bet Builder */}
        <div className="lg:sticky lg:top-6 h-fit">
          <PropBetBuilder onSubmit={handleSubmitParlay} />
        </div>
      </div>
    </div>
  )
}