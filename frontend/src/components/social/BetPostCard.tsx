import { BetPost } from '@/types'
import { formatDistanceToNow } from 'date-fns'
import { 
  HeartIcon as HeartSolid,
  ChatBubbleLeftIcon,
  ShareIcon
} from '@heroicons/react/24/solid'
import { HeartIcon as HeartOutline } from '@heroicons/react/24/outline'
import { CheckBadgeIcon } from '@heroicons/react/24/solid'
import { useState } from 'react'
import { clsx } from 'clsx'

interface BetPostCardProps {
  post: BetPost
  onLike: () => void
  onComment: () => void
  onShare: () => void
  onViewBet: () => void
}

export const BetPostCard = ({ 
  post, 
  onLike, 
  onComment, 
  onShare,
  onViewBet 
}: BetPostCardProps) => {
  const [isLiked, setIsLiked] = useState(post.is_liked || false)
  const [likesCount, setLikesCount] = useState(post.likes_count)

  const handleLike = () => {
    setIsLiked(!isLiked)
    setLikesCount(isLiked ? likesCount - 1 : likesCount + 1)
    onLike()
  }

  const formatOdds = (odds: number) => {
    return odds > 0 ? `+${odds}` : odds.toString()
  }

  return (
    <div className="bg-gray-800 rounded-lg p-6 space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          {post.user.avatar_url ? (
            <img
              src={post.user.avatar_url}
              alt={post.user.display_name}
              className="w-12 h-12 rounded-full object-cover"
            />
          ) : (
            <div className="w-12 h-12 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
              <span className="font-bold text-white">
                {post.user.display_name.charAt(0).toUpperCase()}
              </span>
            </div>
          )}
          <div>
            <div className="flex items-center gap-2">
              <h4 className="font-semibold">{post.user.display_name}</h4>
              {post.user.verified && (
                <CheckBadgeIcon className="h-4 w-4 text-blue-400" />
              )}
            </div>
            <p className="text-sm text-gray-400">
              @{post.user.username} • {formatDistanceToNow(new Date(post.created_at), { addSuffix: true })}
            </p>
          </div>
        </div>
      </div>

      {/* Bet Details */}
      <div className="bg-gray-900 rounded-lg p-4">
        <div className="flex items-center justify-between mb-3">
          <div>
            <p className="text-sm text-gray-400">{post.bet.market.sport.toUpperCase()}</p>
            <h3 className="font-semibold">
              {post.bet.market.home_team} vs {post.bet.market.away_team}
            </h3>
          </div>
          <div className="text-right">
            <p className="text-2xl font-bold text-green-400">
              {(post.bet.edge * 100).toFixed(1)}%
            </p>
            <p className="text-sm text-gray-400">Edge</p>
          </div>
        </div>
        
        <div className="grid grid-cols-3 gap-2 text-sm">
          <div>
            <span className="text-gray-400">Bet:</span>
            <p className="font-medium">{post.bet.market.bet_type}</p>
          </div>
          <div>
            <span className="text-gray-400">Odds:</span>
            <p className="font-medium font-mono">
              {formatOdds(post.bet.market.bookmaker_odds[0]?.odds || 0)}
            </p>
          </div>
          <div>
            <span className="text-gray-400">Kelly:</span>
            <p className="font-medium">{(post.bet.kelly_fraction * 100).toFixed(1)}%</p>
          </div>
        </div>

        <button
          onClick={onViewBet}
          className="mt-3 w-full py-2 bg-blue-600 hover:bg-blue-700 text-white rounded transition-colors text-sm font-medium"
        >
          View Full Analysis
        </button>
      </div>

      {/* Analysis Text */}
      {post.analysis && (
        <p className="text-gray-300 whitespace-pre-wrap">{post.analysis}</p>
      )}

      {/* Engagement Actions */}
      <div className="flex items-center justify-between pt-4 border-t border-gray-700">
        <button
          onClick={handleLike}
          className={clsx(
            'flex items-center gap-2 px-4 py-2 rounded-lg transition-colors',
            isLiked
              ? 'text-red-400 bg-red-900/20 hover:bg-red-900/30'
              : 'text-gray-400 hover:bg-gray-700'
          )}
        >
          {isLiked ? (
            <HeartSolid className="h-5 w-5" />
          ) : (
            <HeartOutline className="h-5 w-5" />
          )}
          <span>{likesCount}</span>
        </button>

        <button
          onClick={onComment}
          className="flex items-center gap-2 px-4 py-2 rounded-lg text-gray-400 hover:bg-gray-700 transition-colors"
        >
          <ChatBubbleLeftIcon className="h-5 w-5" />
          <span>{post.comments_count}</span>
        </button>

        <button
          onClick={onShare}
          className="flex items-center gap-2 px-4 py-2 rounded-lg text-gray-400 hover:bg-gray-700 transition-colors"
        >
          <ShareIcon className="h-5 w-5" />
          <span>{post.shares_count}</span>
        </button>
      </div>
    </div>
  )
}