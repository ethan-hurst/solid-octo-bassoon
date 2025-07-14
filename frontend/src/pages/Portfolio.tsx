import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { apiClient } from '@/api/client'
import { Position, RiskMetrics } from '@/types'
import { RiskMetricsCard } from '@/components/portfolio/RiskMetricsCard'
import { CorrelationMatrix } from '@/components/portfolio/CorrelationMatrix'
import { PnLCalendar } from '@/components/portfolio/PnLCalendar'
import { 
  AreaChart,
  Area,
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  BarChart,
  Bar
} from 'recharts'
import { format } from 'date-fns'

export const Portfolio = () => {
  const [timeRange, setTimeRange] = useState<'1W' | '1M' | '3M' | '1Y' | 'ALL'>('1M')

  // Fetch portfolio positions
  const { data: positions } = useQuery({
    queryKey: ['positions'],
    queryFn: async () => {
      const { data } = await apiClient.get<Position[]>('/portfolio/positions')
      return data
    },
  })

  // Fetch risk metrics
  const { data: riskMetrics } = useQuery({
    queryKey: ['riskMetrics'],
    queryFn: async () => {
      const { data } = await apiClient.get<RiskMetrics>('/portfolio/risk-metrics')
      return data
    },
  })

  // Fetch correlation data
  const { data: correlationData } = useQuery({
    queryKey: ['correlations'],
    queryFn: async () => {
      const { data } = await apiClient.get<{
        matrix: number[][]
        labels: string[]
      }>('/portfolio/correlations')
      return data
    },
  })

  // Fetch P&L calendar data
  const { data: pnlData } = useQuery({
    queryKey: ['pnlCalendar'],
    queryFn: async () => {
      const { data } = await apiClient.get('/portfolio/daily-pnl')
      return data
    },
  })

  // Fetch performance chart data
  const { data: performanceData } = useQuery({
    queryKey: ['performance', timeRange],
    queryFn: async () => {
      const { data } = await apiClient.get(`/portfolio/performance?range=${timeRange}`)
      return data
    },
  })

  // Active positions summary
  const activePositions = positions?.filter(p => p.status === 'pending') || []
  const totalStake = activePositions.reduce((sum, p) => sum + p.stake, 0)
  const totalExposure = activePositions.reduce((sum, p) => sum + (p.stake * p.bet.market.bookmaker_odds[0]?.odds || 0), 0)

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">Portfolio Analytics</h1>
        <div className="flex gap-2">
          {(['1W', '1M', '3M', '1Y', 'ALL'] as const).map((range) => (
            <button
              key={range}
              onClick={() => setTimeRange(range)}
              className={`px-4 py-2 rounded-lg transition-colors ${
                timeRange === range
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
              }`}
            >
              {range}
            </button>
          ))}
        </div>
      </div>

      {/* Top Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-gray-800 rounded-lg p-6">
          <p className="text-sm font-medium text-gray-400">Active Positions</p>
          <p className="text-3xl font-bold mt-2">{activePositions.length}</p>
          <p className="text-sm text-gray-500 mt-1">
            ${totalStake.toFixed(2)} at risk
          </p>
        </div>
        <div className="bg-gray-800 rounded-lg p-6">
          <p className="text-sm font-medium text-gray-400">Total Exposure</p>
          <p className="text-3xl font-bold mt-2">${totalExposure.toFixed(2)}</p>
          <p className="text-sm text-gray-500 mt-1">
            Potential payout
          </p>
        </div>
        <div className="bg-gray-800 rounded-lg p-6">
          <p className="text-sm font-medium text-gray-400">Monthly P&L</p>
          <p className="text-3xl font-bold mt-2 text-green-400">+$1,234.56</p>
          <p className="text-sm text-gray-500 mt-1">
            +12.3% ROI
          </p>
        </div>
        <div className="bg-gray-800 rounded-lg p-6">
          <p className="text-sm font-medium text-gray-400">Win Rate</p>
          <p className="text-3xl font-bold mt-2">58.2%</p>
          <p className="text-sm text-gray-500 mt-1">
            145/249 bets won
          </p>
        </div>
      </div>

      {/* Risk Metrics */}
      {riskMetrics && (
        <RiskMetricsCard metrics={riskMetrics} />
      )}

      {/* Performance Chart */}
      <div className="bg-gray-800 rounded-lg p-6">
        <h3 className="text-xl font-bold mb-6">Cumulative P&L</h3>
        <ResponsiveContainer width="100%" height={300}>
          <AreaChart data={performanceData?.chart || []}>
            <defs>
              <linearGradient id="colorPnL" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#10B981" stopOpacity={0.3}/>
                <stop offset="95%" stopColor="#10B981" stopOpacity={0}/>
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
            <XAxis 
              dataKey="date" 
              stroke="#9CA3AF"
              tickFormatter={(date) => format(new Date(date), 'MMM d')}
            />
            <YAxis stroke="#9CA3AF" />
            <Tooltip
              contentStyle={{
                backgroundColor: '#1F2937',
                border: '1px solid #374151',
                borderRadius: '0.375rem',
              }}
              labelFormatter={(date) => format(new Date(date), 'MMM d, yyyy')}
              formatter={(value: number) => [`$${value.toFixed(2)}`, 'P&L']}
            />
            <Area
              type="monotone"
              dataKey="cumulative_pnl"
              stroke="#10B981"
              fillOpacity={1}
              fill="url(#colorPnL)"
              strokeWidth={2}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Correlation Matrix */}
        {correlationData && (
          <CorrelationMatrix 
            data={correlationData.matrix} 
            labels={correlationData.labels}
          />
        )}

        {/* Win Rate by Sport */}
        <div className="bg-gray-800 rounded-lg p-6">
          <h3 className="text-xl font-bold mb-6">Win Rate by Sport</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={performanceData?.sportStats || []}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="sport" stroke="#9CA3AF" />
              <YAxis stroke="#9CA3AF" />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1F2937',
                  border: '1px solid #374151',
                  borderRadius: '0.375rem',
                }}
                formatter={(value: number) => [`${value.toFixed(1)}%`, 'Win Rate']}
              />
              <Bar dataKey="win_rate" fill="#3B82F6" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* P&L Calendar */}
      {pnlData && (
        <PnLCalendar data={pnlData} />
      )}

      {/* Active Positions Table */}
      <div className="bg-gray-800 rounded-lg p-6">
        <h3 className="text-xl font-bold mb-4">Active Positions</h3>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-700">
                <th className="text-left py-3 px-4 text-sm font-medium text-gray-400">Game</th>
                <th className="text-left py-3 px-4 text-sm font-medium text-gray-400">Bet Type</th>
                <th className="text-center py-3 px-4 text-sm font-medium text-gray-400">Edge</th>
                <th className="text-center py-3 px-4 text-sm font-medium text-gray-400">Odds</th>
                <th className="text-center py-3 px-4 text-sm font-medium text-gray-400">Stake</th>
                <th className="text-center py-3 px-4 text-sm font-medium text-gray-400">To Win</th>
                <th className="text-right py-3 px-4 text-sm font-medium text-gray-400">Placed</th>
              </tr>
            </thead>
            <tbody>
              {activePositions.map((position) => (
                <tr key={position.id} className="border-b border-gray-800 hover:bg-gray-800/50">
                  <td className="py-4 px-4">
                    <div>
                      <p className="font-medium">
                        {position.bet.market.home_team} vs {position.bet.market.away_team}
                      </p>
                      <p className="text-sm text-gray-400">{position.bet.market.sport}</p>
                    </div>
                  </td>
                  <td className="py-4 px-4">{position.bet.market.bet_type}</td>
                  <td className="py-4 px-4 text-center">
                    <span className="text-green-400 font-medium">
                      {(position.bet.edge * 100).toFixed(1)}%
                    </span>
                  </td>
                  <td className="py-4 px-4 text-center font-mono">
                    {position.bet.market.bookmaker_odds[0]?.odds > 0 ? '+' : ''}
                    {position.bet.market.bookmaker_odds[0]?.odds || 'N/A'}
                  </td>
                  <td className="py-4 px-4 text-center">${position.stake.toFixed(2)}</td>
                  <td className="py-4 px-4 text-center text-green-400">
                    ${((position.stake * position.bet.market.bookmaker_odds[0]?.odds || 0) - position.stake).toFixed(2)}
                  </td>
                  <td className="py-4 px-4 text-right text-sm text-gray-400">
                    {format(new Date(position.placed_at), 'MMM d, h:mm a')}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}