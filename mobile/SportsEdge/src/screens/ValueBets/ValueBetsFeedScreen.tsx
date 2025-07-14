/**
 * Value Bets Feed Screen - Main value betting interface
 */
import React, { useEffect, useState, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  RefreshControl,
  TouchableOpacity,
  Alert,
  ActivityIndicator,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useSelector, useDispatch } from 'react-redux';
import { useNavigation } from '@react-navigation/native';
import Icon from 'react-native-vector-icons/Ionicons';

import { RootState } from '../../store';
import { ValueBetsStackScreenProps } from '../../navigation/types';
import { fetchValueBets, clearError } from '../../store/slices/valueBetsSlice';
import { useWebSocket, useValueBetsWebSocket } from '../../hooks';
import { apiClient } from '../../services';

// Components
import ValueBetCard from '../../components/ValueBetCard';
import FilterButton from '../../components/FilterButton';
import EmptyState from '../../components/EmptyState';
import ErrorState from '../../components/ErrorState';

type Props = ValueBetsStackScreenProps<'ValueBetsFeed'>;

const ValueBetsFeedScreen: React.FC<Props> = ({ navigation }) => {
  const dispatch = useDispatch();
  const theme = useSelector((state: RootState) => state.userPreferences.theme);
  const display = useSelector((state: RootState) => state.userPreferences.display);
  const betting = useSelector((state: RootState) => state.userPreferences.betting);
  const { valueBets, isLoading, error, lastUpdate } = useSelector((state: RootState) => state.valueBets);
  
  // WebSocket connection for real-time updates
  useValueBetsWebSocket();
  const { isConnected } = useWebSocket();

  const [refreshing, setRefreshing] = useState(false);
  const [filters, setFilters] = useState({
    sports: betting.followedSports,
    minEdge: betting.minEdgeFilter,
    sortBy: 'edge' as 'edge' | 'time' | 'bookmaker',
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
      fontSize: 20,
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
  });

  // Load value bets on component mount
  useEffect(() => {
    loadValueBets();
  }, []);

  // Handle errors
  useEffect(() => {
    if (error) {
      Alert.alert('Error', error, [
        { text: 'OK', onPress: () => dispatch(clearError()) }
      ]);
    }
  }, [error, dispatch]);

  const loadValueBets = useCallback(async () => {
    try {
      await dispatch(fetchValueBets({
        sports: filters.sports,
        minEdge: filters.minEdge,
        limit: 50,
      }) as any);
    } catch (error) {
      console.error('Error loading value bets:', error);
    }
  }, [dispatch, filters]);

  const handleRefresh = useCallback(async () => {
    setRefreshing(true);
    await loadValueBets();
    setRefreshing(false);
  }, [loadValueBets]);

  const handleFilterPress = useCallback(() => {
    navigation.navigate('FilterSettings');
  }, [navigation]);

  const handleQuickAnalysis = useCallback((betId: string) => {
    navigation.navigate('QuickAnalysis', { betId });
  }, [navigation]);

  const handleBetDetails = useCallback((betId: string) => {
    navigation.navigate('BetDetails', { betId });
  }, [navigation]);

  const filteredAndSortedBets = valueBets
    .filter(bet => {
      if (filters.sports.length > 0 && !filters.sports.includes(bet.sport)) {
        return false;
      }
      return bet.edge >= filters.minEdge;
    })
    .sort((a, b) => {
      switch (filters.sortBy) {
        case 'edge':
          return b.edge - a.edge;
        case 'time':
          return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
        case 'bookmaker':
          return a.bookmaker.localeCompare(b.bookmaker);
        default:
          return 0;
      }
    });

  const statsData = {
    total: filteredAndSortedBets.length,
    avgEdge: filteredAndSortedBets.length > 0 
      ? filteredAndSortedBets.reduce((sum, bet) => sum + bet.edge, 0) / filteredAndSortedBets.length 
      : 0,
    maxEdge: filteredAndSortedBets.length > 0 
      ? Math.max(...filteredAndSortedBets.map(bet => bet.edge)) 
      : 0,
  };

  const renderValueBet = ({ item }: { item: any }) => (
    <ValueBetCard
      valueBet={item}
      onQuickAnalysis={() => handleQuickAnalysis(item.id)}
      onViewDetails={() => handleBetDetails(item.id)}
      compactMode={display.compactMode}
      showProbabilities={display.showProbabilities}
      oddsFormat={display.oddsFormat}
    />
  );

  if (isLoading && valueBets.length === 0) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.header}>
          <Text style={styles.headerTitle}>Value Bets</Text>
        </View>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={colors.accent} />
          <Text style={[styles.connectionText, { marginTop: 12 }]}>
            Loading value bets...
          </Text>
        </View>
      </SafeAreaView>
    );
  }

  if (error && valueBets.length === 0) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.header}>
          <Text style={styles.headerTitle}>Value Bets</Text>
        </View>
        <ErrorState
          message={error}
          onRetry={loadValueBets}
        />
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Value Bets</Text>
        <View style={styles.headerActions}>
          <View style={styles.connectionStatus}>
            <View 
              style={[
                styles.connectionDot, 
                { backgroundColor: isConnected ? colors.success : colors.error }
              ]} 
            />
            <Text style={styles.connectionText}>
              {isConnected ? 'Live' : 'Offline'}
            </Text>
          </View>
          <TouchableOpacity onPress={handleFilterPress}>
            <Icon name="options-outline" size={24} color={colors.text} />
          </TouchableOpacity>
        </View>
      </View>

      {/* Stats */}
      <View style={styles.statsContainer}>
        <View style={styles.statItem}>
          <Text style={styles.statValue}>{statsData.total}</Text>
          <Text style={styles.statLabel}>Total Bets</Text>
        </View>
        <View style={styles.statItem}>
          <Text style={styles.statValue}>
            {(statsData.avgEdge * 100).toFixed(1)}%
          </Text>
          <Text style={styles.statLabel}>Avg Edge</Text>
        </View>
        <View style={styles.statItem}>
          <Text style={styles.statValue}>
            {(statsData.maxEdge * 100).toFixed(1)}%
          </Text>
          <Text style={styles.statLabel}>Max Edge</Text>
        </View>
      </View>

      {/* Filter Bar */}
      <View style={styles.filterContainer}>
        <FilterButton
          title={`Sports (${filters.sports.length})`}
          active={filters.sports.length > 0}
          onPress={handleFilterPress}
        />
        <FilterButton
          title={`Min Edge ${(filters.minEdge * 100).toFixed(0)}%`}
          active={filters.minEdge > 0}
          onPress={handleFilterPress}
        />
        <FilterButton
          title={`Sort: ${filters.sortBy}`}
          active={false}
          onPress={handleFilterPress}
        />
      </View>

      {/* Value Bets List */}
      <View style={styles.listContainer}>
        {filteredAndSortedBets.length === 0 ? (
          <EmptyState
            icon="flash-outline"
            title="No Value Bets"
            message="No value bets match your current filters. Try adjusting your settings or check back later."
            actionText="Adjust Filters"
            onAction={handleFilterPress}
          />
        ) : (
          <FlatList
            data={filteredAndSortedBets}
            renderItem={renderValueBet}
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
            ItemSeparatorComponent={() => <View style={{ height: 12 }} />}
          />
        )}
        
        {lastUpdate && (
          <Text style={styles.lastUpdateText}>
            Last updated: {new Date(lastUpdate).toLocaleTimeString()}
          </Text>
        )}
      </View>
    </SafeAreaView>
  );
};

export default ValueBetsFeedScreen;