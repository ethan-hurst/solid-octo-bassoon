import { useState } from 'react'
import { MagnifyingGlassIcon } from '@heroicons/react/24/outline'
import { Player, SportType } from '@/types'
import { useQuery } from '@tanstack/react-query'
import { apiClient } from '@/api/client'

interface PlayerSearchProps {
  sport?: SportType
  onSelectPlayer: (player: Player) => void
}

export const PlayerSearch = ({ sport, onSelectPlayer }: PlayerSearchProps) => {
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedSport, setSelectedSport] = useState<SportType | 'all'>(sport || 'all')

  const { data: players, isLoading } = useQuery({
    queryKey: ['players', searchTerm, selectedSport],
    queryFn: async () => {
      const params = new URLSearchParams()
      if (searchTerm) params.append('search', searchTerm)
      if (selectedSport !== 'all') params.append('sport', selectedSport)
      
      const { data } = await apiClient.get<Player[]>(`/players?${params}`)
      return data
    },
    enabled: searchTerm.length > 2 || selectedSport !== 'all',
  })

  const sports = [
    { value: 'all', label: 'All Sports' },
    { value: SportType.NFL, label: 'NFL' },
    { value: SportType.NBA, label: 'NBA' },
    { value: SportType.MLB, label: 'MLB' },
    { value: SportType.NHL, label: 'NHL' },
  ]

  return (
    <div className="space-y-4">
      <div className="flex gap-2">
        <div className="relative flex-1">
          <MagnifyingGlassIcon className="absolute left-3 top-3 h-5 w-5 text-gray-400" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search players by name..."
            className="w-full bg-gray-800 border border-gray-700 rounded-lg pl-10 pr-4 py-3 text-white placeholder-gray-400 focus:outline-none focus:border-blue-500"
          />
        </div>
        <select
          value={selectedSport}
          onChange={(e) => setSelectedSport(e.target.value as SportType | 'all')}
          className="bg-gray-800 border border-gray-700 rounded-lg px-4 py-3 text-white focus:outline-none focus:border-blue-500"
        >
          {sports.map((sport) => (
            <option key={sport.value} value={sport.value}>
              {sport.label}
            </option>
          ))}
        </select>
      </div>

      {isLoading && (
        <div className="text-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto"></div>
        </div>
      )}

      {players && players.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {players.map((player) => (
            <button
              key={player.id}
              onClick={() => onSelectPlayer(player)}
              className="bg-gray-800 border border-gray-700 rounded-lg p-4 hover:border-blue-500 transition-colors text-left"
            >
              <div className="flex items-center gap-3">
                {player.image_url ? (
                  <img
                    src={player.image_url}
                    alt={player.name}
                    className="w-12 h-12 rounded-full object-cover"
                  />
                ) : (
                  <div className="w-12 h-12 rounded-full bg-gray-700 flex items-center justify-center">
                    <span className="text-xl font-bold">
                      {player.jersey_number || player.name.charAt(0)}
                    </span>
                  </div>
                )}
                <div>
                  <h3 className="font-semibold">{player.name}</h3>
                  <p className="text-sm text-gray-400">
                    {player.team} • {player.position}
                  </p>
                </div>
              </div>
            </button>
          ))}
        </div>
      )}

      {players && players.length === 0 && searchTerm && (
        <p className="text-center text-gray-400 py-8">
          No players found matching "{searchTerm}"
        </p>
      )}
    </div>
  )
}