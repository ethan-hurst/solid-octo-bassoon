import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { apiClient } from '@/api/client'
import { BetPost, UserProfile } from '@/types'
import { UserProfileCard } from '@/components/social/UserProfileCard'
import { BetPostCard } from '@/components/social/BetPostCard'
import { CopyTradingDashboard } from '@/components/social/CopyTradingDashboard'
import { useAuthStore } from '@/stores/authStore'
import { 
  UserGroupIcon, 
  FireIcon, 
  ChartBarIcon,
  DocumentDuplicateIcon 
} from '@heroicons/react/24/outline'
import toast from 'react-hot-toast'

type TabType = 'feed' | 'leaderboard' | 'following' | 'copy-trading'

export const SocialTrading = () => {
  const [activeTab, setActiveTab] = useState<TabType>('feed')
  const user = useAuthStore((state) => state.user)

  // Fetch social feed
  const { data: feedPosts, refetch: refetchFeed } = useQuery({
    queryKey: ['socialFeed'],
    queryFn: async () => {
      const { data } = await apiClient.get<BetPost[]>('/social/feed')
      return data
    },
  })

  // Fetch leaderboard
  const { data: leaderboard } = useQuery({
    queryKey: ['leaderboard'],
    queryFn: async () => {
      const { data } = await apiClient.get<UserProfile[]>('/social/leaderboard')
      return data
    },
  })

  // Fetch following list
  const { data: following } = useQuery({
    queryKey: ['following', user?.id],
    queryFn: async () => {
      if (!user) return []
      const { data } = await apiClient.get<UserProfile[]>(`/users/${user.id}/following`)
      return data
    },
    enabled: !!user,
  })

  const handleLikePost = async (postId: string) => {
    try {
      await apiClient.post(`/social/posts/${postId}/like`)
      refetchFeed()
    } catch (error) {
      toast.error('Failed to like post')
    }
  }

  const handleFollowUser = async (userId: string) => {
    try {
      await apiClient.post(`/users/${userId}/follow`)
      toast.success('Successfully followed user')
    } catch (error) {
      toast.error('Failed to follow user')
    }
  }

  const handleUnfollowUser = async (userId: string) => {
    try {
      await apiClient.delete(`/users/${userId}/follow`)
      toast.success('Unfollowed user')
    } catch (error) {
      toast.error('Failed to unfollow user')
    }
  }

  const tabs = [
    { id: 'feed', label: 'Feed', icon: FireIcon },
    { id: 'leaderboard', label: 'Leaderboard', icon: ChartBarIcon },
    { id: 'following', label: 'Following', icon: UserGroupIcon },
    { id: 'copy-trading', label: 'Copy Trading', icon: DocumentDuplicateIcon },
  ]

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Social Trading</h1>
        <p className="text-gray-400 mt-1">
          Follow successful bettors and copy their strategies
        </p>
      </div>

      {/* Tab Navigation */}
      <div className="border-b border-gray-700">
        <nav className="flex space-x-8">
          {tabs.map((tab) => {
            const Icon = tab.icon
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as TabType)}
                className={`flex items-center gap-2 py-3 px-1 border-b-2 transition-colors ${
                  activeTab === tab.id
                    ? 'border-blue-500 text-blue-400'
                    : 'border-transparent text-gray-400 hover:text-gray-300'
                }`}
              >
                <Icon className="h-5 w-5" />
                {tab.label}
              </button>
            )
          })}
        </nav>
      </div>

      {/* Tab Content */}
      <div>
        {activeTab === 'feed' && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="space-y-4">
              <h2 className="text-xl font-semibold">Recent Bets</h2>
              {feedPosts?.map((post) => (
                <BetPostCard
                  key={post.id}
                  post={post}
                  onLike={() => handleLikePost(post.id)}
                  onComment={() => toast('Comments coming soon')}
                  onShare={() => toast('Sharing coming soon')}
                  onViewBet={() => toast('Bet details coming soon')}
                />
              ))}
            </div>
            <div className="space-y-4">
              <h2 className="text-xl font-semibold">Trending Bettors</h2>
              {leaderboard?.slice(0, 3).map((profile) => (
                <UserProfileCard
                  key={profile.id}
                  profile={profile}
                  isFollowing={false}
                  onFollow={() => handleFollowUser(profile.id)}
                  onUnfollow={() => handleUnfollowUser(profile.id)}
                />
              ))}
            </div>
          </div>
        )}

        {activeTab === 'leaderboard' && (
          <div>
            <div className="bg-gray-800 rounded-lg overflow-hidden">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-gray-700">
                    <th className="text-left py-4 px-6 text-sm font-medium text-gray-400">Rank</th>
                    <th className="text-left py-4 px-6 text-sm font-medium text-gray-400">Bettor</th>
                    <th className="text-center py-4 px-6 text-sm font-medium text-gray-400">Win Rate</th>
                    <th className="text-center py-4 px-6 text-sm font-medium text-gray-400">ROI</th>
                    <th className="text-center py-4 px-6 text-sm font-medium text-gray-400">Profit</th>
                    <th className="text-center py-4 px-6 text-sm font-medium text-gray-400">Followers</th>
                    <th className="text-right py-4 px-6 text-sm font-medium text-gray-400">Action</th>
                  </tr>
                </thead>
                <tbody>
                  {leaderboard?.map((profile, index) => (
                    <tr key={profile.id} className="border-b border-gray-800 hover:bg-gray-800/50">
                      <td className="py-4 px-6">
                        <span className={`font-bold ${
                          index === 0 ? 'text-yellow-400' :
                          index === 1 ? 'text-gray-300' :
                          index === 2 ? 'text-orange-400' : ''
                        }`}>
                          #{index + 1}
                        </span>
                      </td>
                      <td className="py-4 px-6">
                        <div className="flex items-center gap-3">
                          {profile.avatar_url ? (
                            <img
                              src={profile.avatar_url}
                              alt={profile.display_name}
                              className="w-10 h-10 rounded-full object-cover"
                            />
                          ) : (
                            <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
                              <span className="font-bold text-white">
                                {profile.display_name.charAt(0).toUpperCase()}
                              </span>
                            </div>
                          )}
                          <div>
                            <p className="font-medium">{profile.display_name}</p>
                            <p className="text-sm text-gray-400">@{profile.username}</p>
                          </div>
                        </div>
                      </td>
                      <td className="py-4 px-6 text-center">
                        <span className="text-green-400 font-medium">{profile.win_rate}%</span>
                      </td>
                      <td className="py-4 px-6 text-center">
                        <span className="text-blue-400 font-medium">{profile.roi}%</span>
                      </td>
                      <td className="py-4 px-6 text-center">
                        <span className="font-medium">${profile.total_profit.toFixed(0)}</span>
                      </td>
                      <td className="py-4 px-6 text-center">
                        <span className="text-gray-400">{profile.followers_count}</span>
                      </td>
                      <td className="py-4 px-6 text-right">
                        <button
                          onClick={() => handleFollowUser(profile.id)}
                          className="px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded transition-colors"
                        >
                          Follow
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {activeTab === 'following' && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {following && following.length > 0 ? (
              following.map((profile) => (
                <UserProfileCard
                  key={profile.id}
                  profile={profile}
                  isFollowing={true}
                  onFollow={() => handleFollowUser(profile.id)}
                  onUnfollow={() => handleUnfollowUser(profile.id)}
                />
              ))
            ) : (
              <div className="col-span-full text-center py-12 text-gray-400">
                <UserGroupIcon className="h-16 w-16 mx-auto mb-4 opacity-50" />
                <p className="text-lg">You're not following anyone yet</p>
                <p className="text-sm mt-1">Check out the leaderboard to find successful bettors</p>
              </div>
            )}
          </div>
        )}

        {activeTab === 'copy-trading' && user && (
          <CopyTradingDashboard userId={user.id} />
        )}
      </div>
    </div>
  )
}