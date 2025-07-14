/**
 * Live Games Screen - Real-time game monitoring dashboard
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
import { LiveGamesStackScreenProps } from '../../navigation/types';
import { fetchLiveGames, clearError } from '../../store/slices/liveGamesSlice';
import { useWebSocket, useLiveGamesWebSocket, useOfflineData } from '../../hooks';
import { apiClient } from '../../services';

// Components
import LiveGameCard from '../../components/LiveGameCard';
import FilterButton from '../../components/FilterButton';
import EmptyState from '../../components/EmptyState';
import ErrorState from '../../components/ErrorState';

type Props = LiveGamesStackScreenProps<'LiveGamesList'>;

const LiveGamesScreen: React.FC<Props> = ({ navigation }) => {
  const dispatch = useDispatch();
  const theme = useSelector((state: RootState) => state.userPreferences.theme);
  const betting = useSelector((state: RootState) => state.userPreferences.betting);
  const { liveGames, isLoading, error, lastUpdate } = useSelector((state: RootState) => state.liveGames);
  
  // WebSocket connection for real-time updates
  useLiveGamesWebSocket();
  const { isConnected } = useWebSocket();

  const [refreshing, setRefreshing] = useState(false);
  const [filters, setFilters] = useState({
    sports: betting.followedSports,
    status: 'all' as 'all' | 'live' | 'upcoming' | 'finished',
    sortBy: 'start_time' as 'start_time' | 'sport' | 'status',
  });

  // Use offline-aware data fetching
  const {
    data: offlineData,
    isOffline,
    refetch: refetchOffline,
  } = useOfflineData(
    () => apiClient.getLiveGames(filters.sports),
    'liveGames',
    []
  );

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
    live: '#EF4444',
    upcoming: '#F59E0B',
    finished: '#6B7280',
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
    },
    connectionStatus: {
      flexDirection: 'row',
      alignItems: 'center',
      marginRight: 12,
    },
    connectionDot: {
      width: 8,
      height: 8,
      borderRadius: 4,
      marginRight: 6,
    },
    connectionText: {
      fontSize: 12,
      color: colors.textSecondary,
    },
    offlineBanner: {
      backgroundColor: colors.warning,
      paddingHorizontal: 16,
      paddingVertical: 8,
      flexDirection: 'row',
      alignItems: 'center',
    },
    offlineBannerText: {
      color: '#FFFFFF',
      fontSize: 14,
      fontWeight: '500',
      marginLeft: 8,
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
    statsContainer: {
      flexDirection: 'row',
      justifyContent: 'space-between',
      paddingHorizontal: 16,
      paddingVertical: 12,
      backgroundColor: colors.surface,
      borderBottomWidth: 1,
      borderBottomColor: colors.border,
    },
    statItem: {
      alignItems: 'center',
    },
    statValue: {
      fontSize: 18,
      fontWeight: 'bold',
      color: colors.accent,
    },
    statLabel: {
      fontSize: 12,
      color: colors.textSecondary,
      marginTop: 2,
    },
    lastUpdateText: {
      fontSize: 12,
      color: colors.textSecondary,
      textAlign: 'center',
      paddingVertical: 8,
    },
    sectionHeader: {
      fontSize: 16,
      fontWeight: '600',
      color: colors.text,
      marginVertical: 12,
      marginHorizontal: 16,
    },
  });

  useEffect(() => {
    loadLiveGames();
  }, []);

  useEffect(() => {
    if (error) {
      Alert.alert('Error', error, [
        { text: 'OK', onPress: () => dispatch(clearError()) }
      ]);
    }
  }, [error, dispatch]);

  const loadLiveGames = useCallback(async () => {
    try {
      if (!isOffline) {
        await dispatch(fetchLiveGames({
          sports: filters.sports,
        }) as any);
      } else {
        await refetchOffline();
      }
    } catch (error) {
      console.error('Error loading live games:', error);
    }
  }, [dispatch, filters, isOffline, refetchOffline]);

  const handleRefresh = useCallback(async () => {
    setRefreshing(true);
    await loadLiveGames();
    setRefreshing(false);
  }, [loadLiveGames]);

  const handleGamePress = useCallback((gameId: string) => {
    navigation.navigate('GameDetails', { gameId });
  }, [navigation]);

  const handleLiveBetting = useCallback((gameId: string) => {
    navigation.navigate('LiveBetting', { gameId });
  }, [navigation]);

  const handleFilterChange = useCallback((newFilters: Partial<typeof filters>) => {
    setFilters(prev => ({ ...prev, ...newFilters }));
  }, []);

  // Use offline data if available, otherwise use live data
  const displayGames = isOffline ? offlineData : liveGames;

  const filteredAndSortedGames = displayGames
    .filter(game => {
      if (filters.sports.length > 0 && !filters.sports.includes(game.sport)) {
        return false;
      }
      if (filters.status !== 'all' && game.status !== filters.status) {
        return false;
      }
      return true;
    })
    .sort((a, b) => {
      switch (filters.sortBy) {
        case 'start_time':
          return new Date(a.start_time).getTime() - new Date(b.start_time).getTime();
        case 'sport':
          return a.sport.localeCompare(b.sport);
        case 'status':
          return a.status.localeCompare(b.status);
        default:
          return 0;
      }
    });

  // Group games by status
  const gamesByStatus = filteredAndSortedGames.reduce((acc, game) => {
    if (!acc[game.status]) {
      acc[game.status] = [];
    }
    acc[game.status].push(game);
    return acc;
  }, {} as Record<string, any[]>);

  const statsData = {
    total: filteredAndSortedGames.length,
    live: gamesByStatus.live?.length || 0,
    upcoming: gamesByStatus.upcoming?.length || 0,
    finished: gamesByStatus.finished?.length || 0,
  };

  const renderGame = ({ item }: { item: any }) => (
    <LiveGameCard
      game={item}
      onPress={() => handleGamePress(item.id)}
      onLiveBetting={() => handleLiveBetting(item.id)}
      isOffline={isOffline}
    />
  );

  const renderSection = (status: string, games: any[]) => {
    if (games.length === 0) return null;

    const statusColors = {
      live: colors.live,
      upcoming: colors.upcoming,
      finished: colors.finished,
    };

    return (
      <View key={status}>
        <View style={[styles.sectionHeader, { flexDirection: 'row', alignItems: 'center' }]}>
          <View 
            style={{
              width: 8,
              height: 8,
              borderRadius: 4,
              backgroundColor: statusColors[status as keyof typeof statusColors] || colors.textSecondary,
              marginRight: 8,
            }}
          />
          <Text style={styles.sectionHeader}>
            {status.charAt(0).toUpperCase() + status.slice(1)} ({games.length})
          </Text>
        </View>
        {games.map((game, index) => (
          <View key={game.id} style={{ marginBottom: 12 }}>
            <LiveGameCard
              game={game}
              onPress={() => handleGamePress(game.id)}
              onLiveBetting={() => handleLiveBetting(game.id)}
              isOffline={isOffline}
            />
          </View>
        ))}
      </View>
    );
  };

  if (isLoading && displayGames.length === 0) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.header}>
          <Text style={styles.headerTitle}>Live Games</Text>
        </View>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={colors.accent} />
          <Text style={[styles.connectionText, { marginTop: 12 }]}>
            Loading live games...
          </Text>
        </View>
      </SafeAreaView>
    );
  }

  if (error && displayGames.length === 0) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.header}>
          <Text style={styles.headerTitle}>Live Games</Text>
        </View>
        <ErrorState
          message={error}
          onRetry={loadLiveGames}
        />
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Live Games</Text>
        <View style={styles.headerActions}>
          <View style={styles.connectionStatus}>
            <View 
              style={[
                styles.connectionDot, 
                { backgroundColor: isConnected && !isOffline ? colors.success : colors.error }
              ]} 
            />
            <Text style={styles.connectionText}>
              {isOffline ? 'Offline' : isConnected ? 'Live' : 'Connecting'}
            </Text>
          </View>
          <TouchableOpacity onPress={handleRefresh}>
            <Icon name="refresh" size={24} color={colors.text} />
          </TouchableOpacity>
        </View>
      </View>

      {/* Offline Banner */}
      {isOffline && (
        <View style={styles.offlineBanner}>
          <Icon name="cloud-offline" size={16} color="#FFFFFF" />
          <Text style={styles.offlineBannerText}>
            Showing cached data - Connect to internet for latest updates
          </Text>
        </View>
      )}

      {/* Stats */}
      <View style={styles.statsContainer}>
        <View style={styles.statItem}>
          <Text style={[styles.statValue, { color: colors.live }]}>
            {statsData.live}
          </Text>
          <Text style={styles.statLabel}>Live</Text>
        </View>
        <View style={styles.statItem}>
          <Text style={[styles.statValue, { color: colors.upcoming }]}>
            {statsData.upcoming}
          </Text>
          <Text style={styles.statLabel}>Upcoming</Text>
        </View>
        <View style={styles.statItem}>
          <Text style={[styles.statValue, { color: colors.finished }]}>
            {statsData.finished}
          </Text>
          <Text style={styles.statLabel}>Finished</Text>
        </View>
        <View style={styles.statItem}>
          <Text style={styles.statValue}>{statsData.total}</Text>
          <Text style={styles.statLabel}>Total</Text>
        </View>
      </View>

      {/* Filter Bar */}
      <View style={styles.filterContainer}>
        <FilterButton
          title={`Sports (${filters.sports.length})`}
          active={filters.sports.length > 0}
          onPress={() => {}}
        />
        <FilterButton
          title={`Status: ${filters.status}`}
          active={filters.status !== 'all'}
          onPress={() => {}}
        />
        <FilterButton
          title={`Sort: ${filters.sortBy.replace('_', ' ')}`}
          active={false}
          onPress={() => {}}
        />
      </View>

      {/* Games List */}
      <View style={styles.listContainer}>
        {filteredAndSortedGames.length === 0 ? (
          <EmptyState
            icon="game-controller-outline"
            title="No Live Games"
            message="No games match your current filters. Try adjusting your settings or check back later."
            actionText="Refresh"
            onAction={handleRefresh}
          />
        ) : (
          <FlatList
            data={Object.entries(gamesByStatus)}
            renderItem={({ item: [status, games] }) => renderSection(status, games)}
            keyExtractor={([status]) => status}
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
          />
        )}
        
        {lastUpdate && !isOffline && (
          <Text style={styles.lastUpdateText}>
            Last updated: {new Date(lastUpdate).toLocaleTimeString()}
          </Text>
        )}
      </View>
    </SafeAreaView>
  );
};

export default LiveGamesScreen;