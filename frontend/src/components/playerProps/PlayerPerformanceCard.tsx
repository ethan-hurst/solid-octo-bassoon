import { Player, PlayerStats } from '@/types'
import { useQuery } from '@tanstack/react-query'
import { apiClient } from '@/api/client'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
} from 'recharts'

interface PlayerPerformanceCardProps {
  player: Player
}

export const PlayerPerformanceCard = ({ player }: PlayerPerformanceCardProps) => {
  const { data: stats, isLoading } = useQuery({
    queryKey: ['playerStats', player.id],
    queryFn: async () => {
      const { data } = await apiClient.get<PlayerStats>(`/players/${player.id}/stats`)
      return data
    },
  })

  if (isLoading) {
    return (
      <div className="bg-gray-800 rounded-lg p-6 animate-pulse">
        <div className="h-4 bg-gray-700 rounded w-3/4 mb-4"></div>
        <div className="h-32 bg-gray-700 rounded"></div>
      </div>
    )
  }

  if (!stats) return null

  // Format recent form data for line chart
  const formData = stats.recent_form.map((value, index) => ({
    game: `G${index + 1}`,
    value,
  }))

  // Format stats for radar chart
  const radarData = Object.entries(stats.averages).slice(0, 6).map(([key, value]) => ({
    stat: key.replace(/_/g, ' ').toUpperCase(),
    value,
    fullMark: Math.max(...Object.values(stats.averages)) * 1.2,
  }))

  return (
    <div className="bg-gray-800 rounded-lg p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          {player.image_url ? (
            <img
              src={player.image_url}
              alt={player.name}
              className="w-16 h-16 rounded-full object-cover"
            />
          ) : (
            <div className="w-16 h-16 rounded-full bg-gray-700 flex items-center justify-center">
              <span className="text-2xl font-bold">
                {player.jersey_number || player.name.charAt(0)}
              </span>
            </div>
          )}
          <div>
            <h3 className="text-xl font-bold">{player.name}</h3>
            <p className="text-gray-400">
              {player.team} • {player.position} • {stats.games_played} games
            </p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-6">
        {/* Recent Form Chart */}
        <div>
          <h4 className="text-sm font-medium text-gray-400 mb-2">Recent Form</h4>
          <ResponsiveContainer width="100%" height={150}>
            <LineChart data={formData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="game" stroke="#9CA3AF" />
              <YAxis stroke="#9CA3AF" />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1F2937',
                  border: '1px solid #374151',
                  borderRadius: '0.375rem',
                }}
              />
              <Line
                type="monotone"
                dataKey="value"
                stroke="#3B82F6"
                strokeWidth={2}
                dot={{ fill: '#3B82F6' }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Stats Radar */}
        <div>
          <h4 className="text-sm font-medium text-gray-400 mb-2">Season Averages</h4>
          <ResponsiveContainer width="100%" height={150}>
            <RadarChart data={radarData}>
              <PolarGrid stroke="#374151" />
              <PolarAngleAxis dataKey="stat" stroke="#9CA3AF" fontSize={10} />
              <PolarRadiusAxis stroke="#374151" />
              <Radar
                name={player.name}
                dataKey="value"
                stroke="#3B82F6"
                fill="#3B82F6"
                fillOpacity={0.3}
              />
            </RadarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Key Stats */}
      <div className="grid grid-cols-3 gap-4">
        {Object.entries(stats.averages).slice(0, 3).map(([key, value]) => (
          <div key={key} className="bg-gray-900 rounded p-3">
            <p className="text-xs text-gray-400 uppercase">{key.replace(/_/g, ' ')}</p>
            <p className="text-2xl font-bold text-blue-400">{value.toFixed(1)}</p>
          </div>
        ))}
      </div>
    </div>
  )
}