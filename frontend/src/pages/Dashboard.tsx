import { useQuery } from '@tanstack/react-query'
import { apiClient } from '@/api/client'
import { ValueBetCard } from '@/components/cards/ValueBetCard'
import { StatsCard } from '@/components/cards/StatsCard'
import { ValueBet, PerformanceSummary } from '@/types'

export const Dashboard = () => {
  const { data: valueBets, isLoading } = useQuery({
    queryKey: ['valueBets'],
    queryFn: async () => {
      const { data } = await apiClient.post<ValueBet[]>('/analysis/value-bets?min_edge=0.05', {
        sport: 'americanfootball_nfl'
      })
      return data
    },
    refetchInterval: 30000, // Refresh every 30 seconds
  })
  
  const { data: performance } = useQuery({
    queryKey: ['performance'],
    queryFn: async () => {
      const { data } = await apiClient.get<PerformanceSummary>('/analysis/performance/summary')
      return data
    },
  })
  
  if (isLoading) {
    return <div className="flex justify-center p-8">Loading...</div>
  }
  
  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Dashboard</h1>
      
      {/* Stats Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatsCard
          title="Total P&L"
          value={`$${performance?.total_profit || 0}`}
          change={performance?.profit_change || 0}
        />
        <StatsCard
          title="Win Rate"
          value={`${performance?.win_rate || 0}%`}
          change={performance?.win_rate_change || 0}
        />
        <StatsCard
          title="Active Bets"
          value={performance?.active_bets || 0}
        />
        <StatsCard
          title="Avg Edge"
          value={`${performance?.avg_edge || 0}%`}
        />
      </div>
      
      {/* Value Bets */}
      <div>
        <h2 className="text-2xl font-semibold mb-4">Live Value Bets</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {valueBets?.map((bet) => (
            <ValueBetCard
              key={bet.id}
              bet={bet}
              onPlace={(bet) => console.log('Place bet:', bet)}
            />
          ))}
        </div>
        {(!valueBets || valueBets.length === 0) && (
          <p className="text-gray-400">No value bets available at the moment.</p>
        )}
      </div>
    </div>
  )
}