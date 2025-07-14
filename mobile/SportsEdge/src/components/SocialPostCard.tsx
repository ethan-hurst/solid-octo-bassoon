/**
 * Social Post Card Component
 */
import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Image,
  Dimensions,
} from 'react-native';
import { useSelector } from 'react-redux';
import Icon from 'react-native-vector-icons/Ionicons';

import { RootState } from '../store';

const { width } = Dimensions.get('window');

interface SocialPostCardProps {
  post: {
    id: string;
    user: {
      id: string;
      username: string;
      avatar?: string;
      verified: boolean;
      followers_count: number;
      roi_30d: number;
    };
    type: 'bet_share' | 'analysis' | 'discussion' | 'result';
    content: string;
    bet?: {
      id: string;
      event: string;
      selection: string;
      odds: number;
      stake: number;
      status: 'pending' | 'won' | 'lost' | 'void';
    };
    media?: {
      type: 'image' | 'video';
      url: string;
    }[];
    likes_count: number;
    comments_count: number;
    shares_count: number;
    is_liked: boolean;
    is_following_user: boolean;
    created_at: string;
    tags?: string[];
  };
  onLike: () => void;
  onComment: () => void;
  onShare: () => void;
  onUserPress: () => void;
  onFollow: () => void;
  onCopyBet?: () => void;
}

const SocialPostCard: React.FC<SocialPostCardProps> = ({
  post,
  onLike,
  onComment,
  onShare,
  onUserPress,
  onFollow,
  onCopyBet,
}) => {
  const theme = useSelector((state: RootState) => state.userPreferences.theme);
  const [imageError, setImageError] = useState(false);

  const isDark = theme.theme === 'dark' || 
    (theme.theme === 'auto' && new Date().getHours() > 18);

  const colors = {
    background: isDark ? '#1E293B' : '#FFFFFF',
    surface: isDark ? '#334155' : '#F8FAFC',
    text: isDark ? '#F1F5F9' : '#1E293B',
    textSecondary: isDark ? '#94A3B8' : '#64748B',
    border: isDark ? '#475569' : '#E2E8F0',
    accent: theme.accentColor,
    success: '#10B981',
    warning: '#F59E0B',
    error: '#EF4444',
    verified: '#3B82F6',
  };

  const getPostTypeIcon = (type: string) => {
    switch (type) {
      case 'bet_share':
        return 'flash';
      case 'analysis':
        return 'analytics';
      case 'discussion':
        return 'chatbubbles';
      case 'result':
        return 'trophy';
      default:
        return 'document-text';
    }
  };

  const getPostTypeColor = (type: string) => {
    switch (type) {
      case 'bet_share':
        return colors.accent;
      case 'analysis':
        return colors.warning;
      case 'discussion':
        return colors.textSecondary;
      case 'result':
        return colors.success;
      default:
        return colors.textSecondary;
    }
  };

  const getBetStatusColor = (status: string) => {
    switch (status) {
      case 'won':
        return colors.success;
      case 'lost':
        return colors.error;
      case 'pending':
        return colors.warning;
      case 'void':
        return colors.textSecondary;
      default:
        return colors.textSecondary;
    }
  };

  const formatTimeAgo = (dateString: string) => {
    const now = new Date();
    const postDate = new Date(dateString);
    const diffMs = now.getTime() - postDate.getTime();
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffMinutes = Math.floor(diffMs / (1000 * 60));

    if (diffMinutes < 60) {
      return `${diffMinutes}m`;
    } else if (diffHours < 24) {
      return `${diffHours}h`;
    } else {
      const diffDays = Math.floor(diffHours / 24);
      return `${diffDays}d`;
    }
  };

  const formatNumber = (num: number): string => {
    if (num >= 1000000) {
      return (num / 1000000).toFixed(1) + 'M';
    } else if (num >= 1000) {
      return (num / 1000).toFixed(1) + 'k';
    }
    return num.toString();
  };

  const styles = StyleSheet.create({
    card: {
      backgroundColor: colors.background,
      borderRadius: 12,
      borderWidth: 1,
      borderColor: colors.border,
      overflow: 'hidden',
    },
    header: {
      flexDirection: 'row',
      alignItems: 'center',
      padding: 16,
      paddingBottom: 12,
    },
    avatar: {
      width: 40,
      height: 40,
      borderRadius: 20,
      backgroundColor: colors.surface,
    },
    avatarFallback: {
      width: 40,
      height: 40,
      borderRadius: 20,
      backgroundColor: colors.accent,
      justifyContent: 'center',
      alignItems: 'center',
    },
    avatarText: {
      color: '#FFFFFF',
      fontSize: 16,
      fontWeight: 'bold',
    },
    userInfo: {
      flex: 1,
      marginLeft: 12,
    },
    userHeader: {
      flexDirection: 'row',
      alignItems: 'center',
    },
    username: {
      fontSize: 16,
      fontWeight: '600',
      color: colors.text,
    },
    verifiedIcon: {
      marginLeft: 4,
    },
    userStats: {
      flexDirection: 'row',
      alignItems: 'center',
      marginTop: 2,
    },
    statText: {
      fontSize: 12,
      color: colors.textSecondary,
      marginRight: 12,
    },
    roiText: {
      fontSize: 12,
      fontWeight: '600',
    },
    positiveRoi: {
      color: colors.success,
    },
    negativeRoi: {
      color: colors.error,
    },
    postMeta: {
      flexDirection: 'row',
      alignItems: 'center',
    },
    postType: {
      flexDirection: 'row',
      alignItems: 'center',
      backgroundColor: colors.surface,
      borderRadius: 12,
      paddingHorizontal: 8,
      paddingVertical: 4,
      marginRight: 8,
    },
    postTypeText: {
      fontSize: 11,
      fontWeight: '500',
      marginLeft: 4,
      textTransform: 'uppercase',
    },
    timeText: {
      fontSize: 12,
      color: colors.textSecondary,
    },
    followButton: {
      backgroundColor: colors.accent,
      borderRadius: 16,
      paddingHorizontal: 12,
      paddingVertical: 6,
    },
    followingButton: {
      backgroundColor: colors.surface,
      borderColor: colors.border,
      borderWidth: 1,
    },
    followButtonText: {
      fontSize: 12,
      fontWeight: '600',
      color: '#FFFFFF',
    },
    followingButtonText: {
      color: colors.text,
    },
    content: {
      paddingHorizontal: 16,
      paddingBottom: 12,
    },
    contentText: {
      fontSize: 15,
      lineHeight: 22,
      color: colors.text,
    },
    tags: {
      flexDirection: 'row',
      flexWrap: 'wrap',
      marginTop: 8,
      gap: 6,
    },
    tag: {
      backgroundColor: colors.surface,
      borderRadius: 12,
      paddingHorizontal: 8,
      paddingVertical: 4,
    },
    tagText: {
      fontSize: 12,
      color: colors.accent,
      fontWeight: '500',
    },
    betCard: {
      margin: 16,
      marginTop: 8,
      backgroundColor: colors.surface,
      borderRadius: 12,
      padding: 16,
      borderWidth: 1,
      borderColor: colors.border,
    },
    betHeader: {
      flexDirection: 'row',
      justifyContent: 'space-between',
      alignItems: 'center',
      marginBottom: 12,
    },
    betEvent: {
      fontSize: 14,
      fontWeight: '600',
      color: colors.text,
      flex: 1,
    },
    betStatus: {
      paddingHorizontal: 8,
      paddingVertical: 4,
      borderRadius: 8,
    },
    betStatusText: {
      fontSize: 11,
      fontWeight: '600',
      textTransform: 'uppercase',
    },
    betDetails: {
      marginBottom: 12,
    },
    betSelection: {
      fontSize: 16,
      fontWeight: '600',
      color: colors.text,
      marginBottom: 4,
    },
    betMetrics: {
      flexDirection: 'row',
      justifyContent: 'space-between',
    },
    betMetric: {
      alignItems: 'center',
    },
    betMetricLabel: {
      fontSize: 11,
      color: colors.textSecondary,
      marginBottom: 2,
    },
    betMetricValue: {
      fontSize: 14,
      fontWeight: '600',
      color: colors.text,
    },
    copyBetButton: {
      backgroundColor: colors.accent,
      borderRadius: 8,
      paddingVertical: 8,
      paddingHorizontal: 16,
      alignSelf: 'center',
      marginTop: 8,
    },
    copyBetButtonText: {
      color: '#FFFFFF',
      fontSize: 14,
      fontWeight: '600',
    },
    media: {
      width: width - 32,
      height: 200,
      marginHorizontal: 16,
      marginBottom: 12,
      borderRadius: 8,
      backgroundColor: colors.surface,
    },
    actions: {
      flexDirection: 'row',
      justifyContent: 'space-between',
      alignItems: 'center',
      paddingHorizontal: 16,
      paddingVertical: 12,
      borderTopWidth: 1,
      borderTopColor: colors.border,
    },
    actionButton: {
      flexDirection: 'row',
      alignItems: 'center',
      paddingHorizontal: 12,
      paddingVertical: 8,
      borderRadius: 8,
    },
    likedButton: {
      backgroundColor: colors.error + '20',
    },
    actionText: {
      fontSize: 14,
      color: colors.textSecondary,
      marginLeft: 6,
      fontWeight: '500',
    },
    likedText: {
      color: colors.error,
    },
  });

  const renderAvatar = () => {
    if (post.user.avatar && !imageError) {
      return (
        <Image
          source={{ uri: post.user.avatar }}
          style={styles.avatar}
          onError={() => setImageError(true)}
        />
      );
    } else {
      return (
        <View style={styles.avatarFallback}>
          <Text style={styles.avatarText}>
            {post.user.username.charAt(0).toUpperCase()}
          </Text>
        </View>
      );
    }
  };

  const renderBetCard = () => {
    if (!post.bet) return null;

    const statusColor = getBetStatusColor(post.bet.status);

    return (
      <View style={styles.betCard}>
        <View style={styles.betHeader}>
          <Text style={styles.betEvent} numberOfLines={1}>
            {post.bet.event}
          </Text>
          <View style={[styles.betStatus, { backgroundColor: statusColor + '20' }]}>
            <Text style={[styles.betStatusText, { color: statusColor }]}>
              {post.bet.status}
            </Text>
          </View>
        </View>
        
        <View style={styles.betDetails}>
          <Text style={styles.betSelection}>{post.bet.selection}</Text>
        </View>

        <View style={styles.betMetrics}>
          <View style={styles.betMetric}>
            <Text style={styles.betMetricLabel}>Odds</Text>
            <Text style={styles.betMetricValue}>
              {post.bet.odds > 0 ? `+${post.bet.odds}` : post.bet.odds}
            </Text>
          </View>
          <View style={styles.betMetric}>
            <Text style={styles.betMetricLabel}>Stake</Text>
            <Text style={styles.betMetricValue}>${post.bet.stake}</Text>
          </View>
          <View style={styles.betMetric}>
            <Text style={styles.betMetricLabel}>To Win</Text>
            <Text style={styles.betMetricValue}>
              ${(post.bet.stake * Math.abs(post.bet.odds) / 100).toFixed(0)}
            </Text>
          </View>
        </View>

        {onCopyBet && post.bet.status === 'pending' && (
          <TouchableOpacity 
            style={styles.copyBetButton}
            onPress={onCopyBet}
            activeOpacity={0.8}
          >
            <Text style={styles.copyBetButtonText}>Copy Bet</Text>
          </TouchableOpacity>
        )}
      </View>
    );
  };

  return (
    <View style={styles.card}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={onUserPress}>
          {renderAvatar()}
        </TouchableOpacity>
        
        <View style={styles.userInfo}>
          <TouchableOpacity onPress={onUserPress}>
            <View style={styles.userHeader}>
              <Text style={styles.username}>{post.user.username}</Text>
              {post.user.verified && (
                <Icon 
                  name="checkmark-circle" 
                  size={16} 
                  color={colors.verified}
                  style={styles.verifiedIcon}
                />
              )}
            </View>
          </TouchableOpacity>
          
          <View style={styles.userStats}>
            <Text style={styles.statText}>
              {formatNumber(post.user.followers_count)} followers
            </Text>
            <Text style={[
              styles.statText,
              styles.roiText,
              post.user.roi_30d >= 0 ? styles.positiveRoi : styles.negativeRoi
            ]}>
              {post.user.roi_30d >= 0 ? '+' : ''}{post.user.roi_30d.toFixed(1)}% ROI
            </Text>
          </View>
        </View>

        <View style={styles.postMeta}>
          <View style={styles.postType}>
            <Icon 
              name={getPostTypeIcon(post.type)} 
              size={12} 
              color={getPostTypeColor(post.type)} 
            />
            <Text style={[styles.postTypeText, { color: getPostTypeColor(post.type) }]}>
              {post.type.replace('_', ' ')}
            </Text>
          </View>
          <Text style={styles.timeText}>{formatTimeAgo(post.created_at)}</Text>
        </View>
      </View>

      {!post.is_following_user && (
        <TouchableOpacity 
          style={[
            styles.followButton,
            post.is_following_user && styles.followingButton
          ]}
          onPress={onFollow}
          activeOpacity={0.8}
        >
          <Text style={[
            styles.followButtonText,
            post.is_following_user && styles.followingButtonText
          ]}>
            {post.is_following_user ? 'Following' : 'Follow'}
          </Text>
        </TouchableOpacity>
      )}

      {/* Content */}
      <View style={styles.content}>
        <Text style={styles.contentText}>{post.content}</Text>
        
        {post.tags && post.tags.length > 0 && (
          <View style={styles.tags}>
            {post.tags.map((tag, index) => (
              <View key={index} style={styles.tag}>
                <Text style={styles.tagText}>#{tag}</Text>
              </View>
            ))}
          </View>
        )}
      </View>

      {/* Bet Card */}
      {renderBetCard()}

      {/* Media */}
      {post.media && post.media.length > 0 && (
        <Image
          source={{ uri: post.media[0].url }}
          style={styles.media}
          resizeMode="cover"
        />
      )}

      {/* Actions */}
      <View style={styles.actions}>
        <TouchableOpacity 
          style={[styles.actionButton, post.is_liked && styles.likedButton]}
          onPress={onLike}
          activeOpacity={0.7}
        >
          <Icon 
            name={post.is_liked ? "heart" : "heart-outline"} 
            size={20} 
            color={post.is_liked ? colors.error : colors.textSecondary} 
          />
          <Text style={[styles.actionText, post.is_liked && styles.likedText]}>
            {formatNumber(post.likes_count)}
          </Text>
        </TouchableOpacity>

        <TouchableOpacity 
          style={styles.actionButton}
          onPress={onComment}
          activeOpacity={0.7}
        >
          <Icon name="chatbubble-outline" size={20} color={colors.textSecondary} />
          <Text style={styles.actionText}>
            {formatNumber(post.comments_count)}
          </Text>
        </TouchableOpacity>

        <TouchableOpacity 
          style={styles.actionButton}
          onPress={onShare}
          activeOpacity={0.7}
        >
          <Icon name="share-outline" size={20} color={colors.textSecondary} />
          <Text style={styles.actionText}>
            {formatNumber(post.shares_count)}
          </Text>
        </TouchableOpacity>
      </View>
    </View>
  );
};

export default SocialPostCard;