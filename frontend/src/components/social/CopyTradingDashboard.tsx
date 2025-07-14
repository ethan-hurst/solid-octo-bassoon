import { CopySettings, UserProfile, SportType } from '@/types'
import { useQuery, useMutation } from '@tanstack/react-query'
import { apiClient } from '@/api/client'
import { Switch } from '@headlessui/react'
import { clsx } from 'clsx'
import toast from 'react-hot-toast'
import { CheckBadgeIcon } from '@heroicons/react/24/solid'

interface CopyTradingDashboardProps {
  userId: string
}

export const CopyTradingDashboard = ({ userId }: CopyTradingDashboardProps) => {

  // Fetch followed users with copy settings
  const { data: copySettings, refetch } = useQuery({
    queryKey: ['copySettings', userId],
    queryFn: async () => {
      const { data } = await apiClient.get<CopySettings[]>(`/users/${userId}/copy-settings`)
      return data
    },
  })

  // Fetch available experts to follow
  const { data: experts } = useQuery({
    queryKey: ['experts'],
    queryFn: async () => {
      const { data } = await apiClient.get<UserProfile[]>('/users/experts')
      return data
    },
  })

  // Update copy settings mutation
  const updateSettings = useMutation({
    mutationFn: async (settings: Partial<CopySettings>) => {
      const { data } = await apiClient.put(`/users/${userId}/copy-settings/${settings.followed_user_id}`, settings)
      return data
    },
    onSuccess: () => {
      toast.success('Copy settings updated')
      refetch()
    },
  })

  const handleToggleAutoCopy = (followedUserId: string, enabled: boolean) => {
    updateSettings.mutate({ followed_user_id: followedUserId, auto_copy: enabled })
  }

  const handleUpdateStakeLimit = (followedUserId: string, field: 'max_stake_per_bet' | 'max_daily_stake', value: number) => {
    updateSettings.mutate({ followed_user_id: followedUserId, [field]: value })
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold mb-2">Copy Trading Dashboard</h2>
        <p className="text-gray-400">
          Automatically copy trades from successful bettors
        </p>
      </div>

      {/* Active Copy Settings */}
      <div className="space-y-4">
        <h3 className="text-lg font-semibold">Active Copy Traders</h3>
        {copySettings && copySettings.length > 0 ? (
          copySettings.map((setting) => (
            <div key={setting.followed_user_id} className="bg-gray-800 rounded-lg p-6">
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
                    <span className="font-bold text-white">E</span>
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <h4 className="font-semibold">Expert Trader</h4>
                      <CheckBadgeIcon className="h-4 w-4 text-blue-400" />
                    </div>
                    <p className="text-sm text-gray-400">Following since 30 days ago</p>
                  </div>
                </div>
                <Switch
                  checked={setting.auto_copy}
                  onChange={(enabled) => handleToggleAutoCopy(setting.followed_user_id, enabled)}
                  className={clsx(
                    'relative inline-flex h-6 w-11 items-center rounded-full transition-colors',
                    setting.auto_copy ? 'bg-blue-600' : 'bg-gray-700'
                  )}
                >
                  <span
                    className={clsx(
                      'inline-block h-4 w-4 transform rounded-full bg-white transition-transform',
                      setting.auto_copy ? 'translate-x-6' : 'translate-x-1'
                    )}
                  />
                </Switch>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-400 mb-2">
                    Max Stake Per Bet
                  </label>
                  <div className="relative">
                    <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400">$</span>
                    <input
                      type="number"
                      value={setting.max_stake_per_bet}
                      onChange={(e) => handleUpdateStakeLimit(
                        setting.followed_user_id, 
                        'max_stake_per_bet', 
                        parseInt(e.target.value) || 0
                      )}
                      className="w-full bg-gray-900 border border-gray-700 rounded-lg pl-8 pr-4 py-2 focus:outline-none focus:border-blue-500"
                    />
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-400 mb-2">
                    Max Daily Stake
                  </label>
                  <div className="relative">
                    <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400">$</span>
                    <input
                      type="number"
                      value={setting.max_daily_stake}
                      onChange={(e) => handleUpdateStakeLimit(
                        setting.followed_user_id, 
                        'max_daily_stake', 
                        parseInt(e.target.value) || 0
                      )}
                      className="w-full bg-gray-900 border border-gray-700 rounded-lg pl-8 pr-4 py-2 focus:outline-none focus:border-blue-500"
                    />
                  </div>
                </div>
              </div>

              <div className="mt-4">
                <label className="block text-sm font-medium text-gray-400 mb-2">
                  Minimum Edge Required
                </label>
                <input
                  type="range"
                  min="0"
                  max="20"
                  step="0.5"
                  value={setting.min_edge * 100}
                  onChange={(e) => updateSettings.mutate({
                    followed_user_id: setting.followed_user_id,
                    min_edge: parseFloat(e.target.value) / 100
                  })}
                  className="w-full"
                />
                <div className="flex justify-between text-sm text-gray-400 mt-1">
                  <span>0%</span>
                  <span className="text-blue-400 font-medium">{(setting.min_edge * 100).toFixed(1)}%</span>
                  <span>20%</span>
                </div>
              </div>

              <div className="mt-4">
                <p className="text-sm font-medium text-gray-400 mb-2">Copy Sports</p>
                <div className="flex flex-wrap gap-2">
                  {Object.values(SportType).map((sport) => (
                    <button
                      key={sport}
                      onClick={() => {
                        const newSports = setting.copy_sports.includes(sport)
                          ? setting.copy_sports.filter(s => s !== sport)
                          : [...setting.copy_sports, sport]
                        updateSettings.mutate({
                          followed_user_id: setting.followed_user_id,
                          copy_sports: newSports
                        })
                      }}
                      className={clsx(
                        'px-3 py-1 rounded text-sm transition-colors',
                        setting.copy_sports.includes(sport)
                          ? 'bg-blue-600 text-white'
                          : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                      )}
                    >
                      {sport}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          ))
        ) : (
          <p className="text-gray-400 text-center py-8 bg-gray-800 rounded-lg">
            You're not copying any traders yet. Browse experts below to get started.
          </p>
        )}
      </div>

      {/* Available Experts */}
      <div className="space-y-4">
        <h3 className="text-lg font-semibold">Top Experts to Follow</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {experts?.map((expert) => (
            <div key={expert.id} className="bg-gray-800 rounded-lg p-4">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-3">
                  {expert.avatar_url ? (
                    <img
                      src={expert.avatar_url}
                      alt={expert.display_name}
                      className="w-10 h-10 rounded-full object-cover"
                    />
                  ) : (
                    <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
                      <span className="font-bold text-white">
                        {expert.display_name.charAt(0).toUpperCase()}
                      </span>
                    </div>
                  )}
                  <div>
                    <div className="flex items-center gap-2">
                      <h4 className="font-medium">{expert.display_name}</h4>
                      {expert.verified && (
                        <CheckBadgeIcon className="h-4 w-4 text-blue-400" />
                      )}
                    </div>
                    <p className="text-sm text-gray-400">
                      {expert.win_rate}% WR • {expert.roi}% ROI
                    </p>
                  </div>
                </div>
                <button
                  className="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded transition-colors"
                  onClick={() => {
                    // Add logic to follow and set up copy trading
                    toast.success(`Started following ${expert.display_name}`)
                  }}
                >
                  Follow
                </button>
              </div>
              <div className="flex gap-4 text-sm text-gray-400">
                <span>${expert.total_profit.toFixed(0)} profit</span>
                <span>{expert.total_bets} bets</span>
                <span>{expert.followers_count} followers</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}