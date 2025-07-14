import { UserProfile } from '@/types'
import { CheckBadgeIcon } from '@heroicons/react/24/solid'
import { 
  UserPlusIcon, 
  UserMinusIcon,
  ChartBarIcon,
  CurrencyDollarIcon,
  TrophyIcon 
} from '@heroicons/react/24/outline'
import { clsx } from 'clsx'

interface UserProfileCardProps {
  profile: UserProfile
  isFollowing?: boolean
  onFollow?: () => void
  onUnfollow?: () => void
  showActions?: boolean
}

export const UserProfileCard = ({ 
  profile, 
  isFollowing = false,
  onFollow,
  onUnfollow,
  showActions = true 
}: UserProfileCardProps) => {
  const formatNumber = (num: number) => {
    if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`
    if (num >= 1000) return `${(num / 1000).toFixed(1)}K`
    return num.toString()
  }

  const getTierColor = (tier: string) => {
    switch (tier) {
      case 'expert': return 'text-purple-400 bg-purple-900/30'
      case 'pro': return 'text-blue-400 bg-blue-900/30'
      default: return 'text-gray-400 bg-gray-900/30'
    }
  }

  return (
    <div className="bg-gray-800 rounded-lg p-6">
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-4">
          {profile.avatar_url ? (
            <img
              src={profile.avatar_url}
              alt={profile.display_name}
              className="w-20 h-20 rounded-full object-cover"
            />
          ) : (
            <div className="w-20 h-20 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
              <span className="text-2xl font-bold text-white">
                {profile.display_name.charAt(0).toUpperCase()}
              </span>
            </div>
          )}
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-xl font-bold">{profile.display_name}</h3>
              {profile.verified && (
                <CheckBadgeIcon className="h-5 w-5 text-blue-400" />
              )}
            </div>
            <p className="text-gray-400">@{profile.username}</p>
            <span className={clsx(
              'inline-flex items-center px-2 py-1 rounded-full text-xs font-medium mt-1',
              getTierColor(profile.subscription_tier)
            )}>
              {profile.subscription_tier.toUpperCase()}
            </span>
          </div>
        </div>
        
        {showActions && (
          <button
            onClick={isFollowing ? onUnfollow : onFollow}
            className={clsx(
              'flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-colors',
              isFollowing
                ? 'bg-gray-700 hover:bg-gray-600 text-gray-300'
                : 'bg-blue-600 hover:bg-blue-700 text-white'
            )}
          >
            {isFollowing ? (
              <>
                <UserMinusIcon className="h-4 w-4" />
                Unfollow
              </>
            ) : (
              <>
                <UserPlusIcon className="h-4 w-4" />
                Follow
              </>
            )}
          </button>
        )}
      </div>

      {profile.bio && (
        <p className="text-gray-300 mb-4">{profile.bio}</p>
      )}

      <div className="grid grid-cols-2 gap-4 mb-4">
        <div className="text-center">
          <p className="text-2xl font-bold">{formatNumber(profile.followers_count)}</p>
          <p className="text-sm text-gray-400">Followers</p>
        </div>
        <div className="text-center">
          <p className="text-2xl font-bold">{formatNumber(profile.following_count)}</p>
          <p className="text-sm text-gray-400">Following</p>
        </div>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="bg-gray-900 rounded-lg p-3">
          <ChartBarIcon className="h-5 w-5 text-blue-400 mb-1" />
          <p className="text-lg font-semibold">{profile.win_rate}%</p>
          <p className="text-xs text-gray-400">Win Rate</p>
        </div>
        <div className="bg-gray-900 rounded-lg p-3">
          <CurrencyDollarIcon className="h-5 w-5 text-green-400 mb-1" />
          <p className="text-lg font-semibold">${formatNumber(profile.total_profit)}</p>
          <p className="text-xs text-gray-400">Profit</p>
        </div>
        <div className="bg-gray-900 rounded-lg p-3">
          <TrophyIcon className="h-5 w-5 text-yellow-400 mb-1" />
          <p className="text-lg font-semibold">{profile.roi}%</p>
          <p className="text-xs text-gray-400">ROI</p>
        </div>
        <div className="bg-gray-900 rounded-lg p-3">
          <p className="text-lg font-semibold">{formatNumber(profile.total_bets)}</p>
          <p className="text-xs text-gray-400">Total Bets</p>
        </div>
      </div>

      <div className="mt-4 flex flex-wrap gap-2">
        {profile.sports.map((sport) => (
          <span
            key={sport}
            className="px-2 py-1 bg-gray-700 text-gray-300 rounded text-xs"
          >
            {sport}
          </span>
        ))}
      </div>
    </div>
  )
}