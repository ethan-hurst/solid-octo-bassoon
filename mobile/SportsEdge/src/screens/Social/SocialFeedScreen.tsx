/**
 * Social Feed Screen - Social betting community interface
 */
import React, { useEffect, useState, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  RefreshControl,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useSelector, useDispatch } from 'react-redux';
import { useNavigation } from '@react-navigation/native';
import Icon from 'react-native-vector-icons/Ionicons';

import { RootState } from '../../store';
import { SocialStackScreenProps } from '../../navigation/types';
import { useSocialWebSocket, useOfflineAnalytics } from '../../hooks';
import { apiClient } from '../../services';

// Components
import SocialPostCard from '../../components/SocialPostCard';
import FilterButton from '../../components/FilterButton';
import EmptyState from '../../components/EmptyState';
import CreatePostModal from '../../components/CreatePostModal';

type Props = SocialStackScreenProps<'SocialFeed'>;

interface SocialPost {
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
}

const SocialFeedScreen: React.FC<Props> = ({ navigation }) => {
  const theme = useSelector((state: RootState) => state.userPreferences.theme);
  const { trackScreenView, trackUserAction } = useOfflineAnalytics();
  
  // WebSocket connection for real-time updates
  useSocialWebSocket();

  const [posts, setPosts] = useState<SocialPost[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [filters, setFilters] = useState({
    type: 'all' as 'all' | 'bet_share' | 'analysis' | 'discussion' | 'result',
    timeframe: '24h' as '1h' | '24h' | '7d' | '30d',
    following_only: false,
  });

  const isDark = theme.theme === 'dark' || 
    (theme.theme === 'auto' && new Date().getHours() > 18);

  const colors = {
    background: isDark ? '#0F172A' : '#FFFFFF',
    surface: isDark ? '#1E293B' : '#F8FAFC',
    text: isDark ? '#F1F5F9' : '#1E293B',
    textSecondary: isDark ? '#94A3B8' : '#64748B',
    border: isDark ? '#334155' : '#E2E8F0',
    accent: theme.accentColor,
    success: '#10B981',
    warning: '#F59E0B',
    error: '#EF4444',
  };

  const styles = StyleSheet.create({
    container: {
      flex: 1,
      backgroundColor: colors.background,
    },
    header: {
      flexDirection: 'row',
      justifyContent: 'space-between',
      alignItems: 'center',
      paddingHorizontal: 16,
      paddingVertical: 12,
      borderBottomWidth: 1,
      borderBottomColor: colors.border,
    },
    headerTitle: {
      fontSize: 28,
      fontWeight: 'bold',
      color: colors.text,
    },
    headerActions: {
      flexDirection: 'row',
      alignItems: 'center',
      gap: 12,
    },
    headerButton: {
      padding: 8,
    },
    filterContainer: {
      flexDirection: 'row',
      paddingHorizontal: 16,
      paddingVertical: 12,
      backgroundColor: colors.surface,
      borderBottomWidth: 1,
      borderBottomColor: colors.border,
    },
    listContainer: {
      flex: 1,
    },
    listContent: {
      padding: 16,
    },
    loadingContainer: {
      flex: 1,
      justifyContent: 'center',
      alignItems: 'center',
    },
    createButton: {
      position: 'absolute',
      right: 20,
      bottom: 90, // Above tab bar
      width: 56,
      height: 56,
      borderRadius: 28,
      backgroundColor: colors.accent,
      justifyContent: 'center',
      alignItems: 'center',
      shadowColor: colors.text,
      shadowOffset: { width: 0, height: 4 },
      shadowOpacity: 0.3,
      shadowRadius: 8,
      elevation: 8,
    },
    trendingSection: {
      marginBottom: 20,
    },
    sectionTitle: {
      fontSize: 18,
      fontWeight: '600',
      color: colors.text,
      marginBottom: 12,
    },
    trendingTags: {
      flexDirection: 'row',
      flexWrap: 'wrap',
      gap: 8,
    },
    trendingTag: {
      backgroundColor: colors.surface,
      borderRadius: 16,
      paddingHorizontal: 12,
      paddingVertical: 6,
      borderWidth: 1,
      borderColor: colors.border,
    },
    trendingTagText: {
      fontSize: 14,
      color: colors.text,
      fontWeight: '500',
    },
    feedSection: {
      marginTop: 20,
    },
  });

  useEffect(() => {
    trackScreenView('SocialFeed');
    loadSocialFeed();
  }, [filters]);

  const loadSocialFeed = useCallback(async () => {
    try {
      setIsLoading(true);
      
      const response = await apiClient.getSocialFeed(1, 20, {
        type: filters.type !== 'all' ? filters.type : undefined,
        timeframe: filters.timeframe,
        following_only: filters.following_only,
      });
      
      setPosts(response.data.posts || []);
    } catch (error: any) {
      console.error('Error loading social feed:', error);
      Alert.alert('Error', 'Failed to load social feed');
    } finally {
      setIsLoading(false);
    }
  }, [filters]);

  const handleRefresh = useCallback(async () => {
    setRefreshing(true);
    await loadSocialFeed();
    setRefreshing(false);
  }, [loadSocialFeed]);

  const handleLikePost = useCallback(async (postId: string) => {
    try {
      await apiClient.post(`/social/posts/${postId}/like`);
      
      setPosts(prev => prev.map(post => 
        post.id === postId 
          ? { 
              ...post, 
              is_liked: !post.is_liked,
              likes_count: post.is_liked ? post.likes_count - 1 : post.likes_count + 1
            }
          : post
      ));

      await trackUserAction('like_post', { post_id: postId });
    } catch (error) {
      console.error('Error liking post:', error);
    }
  }, [trackUserAction]);

  const handleFollowUser = useCallback(async (userId: string) => {
    try {
      await apiClient.post(`/social/users/${userId}/follow`);
      
      setPosts(prev => prev.map(post => 
        post.user.id === userId 
          ? { ...post, is_following_user: !post.is_following_user }
          : post
      ));

      await trackUserAction('follow_user', { user_id: userId });
    } catch (error) {
      console.error('Error following user:', error);
    }
  }, [trackUserAction]);

  const handleCopyBet = useCallback(async (postId: string, betData: any) => {
    try {
      await apiClient.post('/social/copy-bet', {
        original_post_id: postId,
        bet_data: betData,
      });
      
      Alert.alert(
        'Bet Copied!',
        'The bet has been added to your betslip.',
        [{ text: 'OK' }]
      );

      await trackUserAction('copy_bet', { post_id: postId, bet_id: betData.id });
    } catch (error: any) {
      console.error('Error copying bet:', error);
      Alert.alert('Error', error.message || 'Failed to copy bet');
    }
  }, [trackUserAction]);

  const handleSharePost = useCallback(async (postId: string) => {
    // TODO: Implement native sharing
    await trackUserAction('share_post', { post_id: postId });
    Alert.alert('Share', 'Sharing functionality coming soon!');
  }, [trackUserAction]);

  const handleCommentPress = useCallback((postId: string) => {
    // TODO: Navigate to comments screen
    navigation.navigate('BetPost', { postId });
  }, [navigation]);

  const handleUserPress = useCallback((userId: string) => {
    navigation.navigate('UserProfile', { userId });
  }, [navigation]);

  const handleCreatePost = useCallback(() => {
    setShowCreateModal(true);
    trackUserAction('open_create_post');
  }, [trackUserAction]);

  const handleFilterChange = useCallback((newFilters: Partial<typeof filters>) => {
    setFilters(prev => ({ ...prev, ...newFilters }));
  }, []);

  const renderPost = ({ item }: { item: SocialPost }) => (
    <SocialPostCard
      post={item}
      onLike={() => handleLikePost(item.id)}
      onComment={() => handleCommentPress(item.id)}
      onShare={() => handleSharePost(item.id)}
      onUserPress={() => handleUserPress(item.user.id)}
      onFollow={() => handleFollowUser(item.user.id)}
      onCopyBet={item.bet ? () => handleCopyBet(item.id, item.bet) : undefined}
    />
  );

  const renderTrendingSection = () => {
    const trendingTags = ['#NBA', '#NFL', '#ValueBets', '#LiveBetting', '#Parlays'];
    
    return (
      <View style={styles.trendingSection}>
        <Text style={styles.sectionTitle}>Trending</Text>
        <View style={styles.trendingTags}>
          {trendingTags.map((tag, index) => (
            <TouchableOpacity 
              key={index}
              style={styles.trendingTag}
              onPress={() => {
                // TODO: Filter by tag
                trackUserAction('click_trending_tag', { tag });
              }}
            >
              <Text style={styles.trendingTagText}>{tag}</Text>
            </TouchableOpacity>
          ))}
        </View>
      </View>
    );
  };

  if (isLoading && posts.length === 0) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.header}>
          <Text style={styles.headerTitle}>Social</Text>
        </View>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={colors.accent} />
          <Text style={[{ color: colors.textSecondary, marginTop: 12 }]}>
            Loading social feed...
          </Text>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Social</Text>
        <View style={styles.headerActions}>
          <TouchableOpacity 
            style={styles.headerButton}
            onPress={() => {
              // TODO: Navigate to search/discover
              trackUserAction('open_social_search');
            }}
          >
            <Icon name="search" size={24} color={colors.text} />
          </TouchableOpacity>
          <TouchableOpacity 
            style={styles.headerButton}
            onPress={() => {
              // TODO: Navigate to notifications
              trackUserAction('open_social_notifications');
            }}
          >
            <Icon name="notifications-outline" size={24} color={colors.text} />
          </TouchableOpacity>
        </View>
      </View>

      {/* Filter Bar */}
      <View style={styles.filterContainer}>
        <FilterButton
          title={`Type: ${filters.type}`}
          active={filters.type !== 'all'}
          onPress={() => {
            // TODO: Show filter modal
          }}
        />
        <FilterButton
          title={filters.timeframe}
          active={filters.timeframe !== '24h'}
          onPress={() => {
            // TODO: Show timeframe picker
          }}
        />
        <FilterButton
          title="Following"
          active={filters.following_only}
          onPress={() => handleFilterChange({ following_only: !filters.following_only })}
        />
      </View>

      {/* Social Feed */}
      <View style={styles.listContainer}>
        {posts.length === 0 ? (
          <EmptyState
            icon="people-outline"
            title="No Posts Yet"
            message="Follow other users or share your own bets to see posts in your social feed."
            actionText="Create Post"
            onAction={handleCreatePost}
          />
        ) : (
          <FlatList
            data={posts}
            renderItem={renderPost}
            keyExtractor={(item) => item.id}
            contentContainerStyle={styles.listContent}
            refreshControl={
              <RefreshControl
                refreshing={refreshing}
                onRefresh={handleRefresh}
                tintColor={colors.accent}
                colors={[colors.accent]}
              />
            }
            showsVerticalScrollIndicator={false}
            ItemSeparatorComponent={() => <View style={{ height: 16 }} />}
            ListHeaderComponent={renderTrendingSection}
          />
        )}
      </View>

      {/* Create Post Button */}
      <TouchableOpacity 
        style={styles.createButton}
        onPress={handleCreatePost}
        activeOpacity={0.8}
      >
        <Icon name="add" size={28} color="#FFFFFF" />
      </TouchableOpacity>

      {/* Create Post Modal */}
      <CreatePostModal
        visible={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        onPostCreated={(newPost) => {
          setPosts(prev => [newPost, ...prev]);
          setShowCreateModal(false);
        }}
      />
    </SafeAreaView>
  );
};

export default SocialFeedScreen;