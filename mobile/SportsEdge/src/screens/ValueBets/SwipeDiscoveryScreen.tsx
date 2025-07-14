/**
 * Swipe Discovery Screen - Tinder-like interface for bet discovery
 */
import React, { useEffect, useState, useCallback, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Dimensions,
  TouchableOpacity,
  Alert,
  Animated,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useSelector, useDispatch } from 'react-redux';
import { useNavigation } from '@react-navigation/native';
import Icon from 'react-native-vector-icons/Ionicons';

import { RootState } from '../../store';
import { fetchValueBets } from '../../store/slices/valueBetsSlice';
import { apiClient } from '../../services';

// Components
import SwipeableCard, { SwipeAction } from '../../components/SwipeableCard';
import ValueBetCard from '../../components/ValueBetCard';
import EmptyState from '../../components/EmptyState';

const { width: SCREEN_WIDTH, height: SCREEN_HEIGHT } = Dimensions.get('window');

const SwipeDiscoveryScreen: React.FC = () => {
  const dispatch = useDispatch();
  const navigation = useNavigation();
  const theme = useSelector((state: RootState) => state.userPreferences.theme);
  const betting = useSelector((state: RootState) => state.userPreferences.betting);
  const { valueBets, isLoading } = useSelector((state: RootState) => state.valueBets);

  const [currentIndex, setCurrentIndex] = useState(0);
  const [swipedBets, setSwipedBets] = useState<Set<string>>(new Set());
  const [tutorial, setTutorial] = useState(true);
  
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const scaleAnim = useRef(new Animated.Value(0.8)).current;

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
      fontSize: 20,
      fontWeight: '600',
      color: colors.text,
    },
    headerActions: {
      flexDirection: 'row',
      gap: 12,
    },
    headerButton: {
      padding: 8,
    },
    cardStack: {
      flex: 1,
      justifyContent: 'center',
      alignItems: 'center',
      paddingHorizontal: 20,
    },
    cardContainer: {
      position: 'absolute',
      width: SCREEN_WIDTH - 40,
      height: SCREEN_HEIGHT * 0.7,
    },
    nextCard: {
      opacity: 0.5,
      transform: [{ scale: 0.95 }],
    },
    actionButtons: {
      flexDirection: 'row',
      justifyContent: 'space-around',
      alignItems: 'center',
      paddingHorizontal: 40,
      paddingVertical: 20,
      backgroundColor: colors.surface,
      borderTopWidth: 1,
      borderTopColor: colors.border,
    },
    actionButton: {
      width: 60,
      height: 60,
      borderRadius: 30,
      justifyContent: 'center',
      alignItems: 'center',
      shadowColor: colors.text,
      shadowOffset: { width: 0, height: 2 },
      shadowOpacity: 0.2,
      shadowRadius: 4,
      elevation: 4,
    },
    passButton: {
      backgroundColor: colors.error,
    },
    likeButton: {
      backgroundColor: colors.success,
    },
    superLikeButton: {
      backgroundColor: colors.accent,
    },
    tutorialOverlay: {
      position: 'absolute',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      backgroundColor: 'rgba(0,0,0,0.8)',
      justifyContent: 'center',
      alignItems: 'center',
      zIndex: 1000,
    },
    tutorialCard: {
      backgroundColor: colors.surface,
      borderRadius: 16,
      padding: 24,
      marginHorizontal: 40,
      alignItems: 'center',
    },
    tutorialTitle: {
      fontSize: 24,
      fontWeight: 'bold',
      color: colors.text,
      marginBottom: 16,
      textAlign: 'center',
    },
    tutorialText: {
      fontSize: 16,
      color: colors.textSecondary,
      textAlign: 'center',
      lineHeight: 24,
      marginBottom: 20,
    },
    tutorialActions: {
      flexDirection: 'row',
      gap: 12,
    },
    tutorialButton: {
      paddingHorizontal: 20,
      paddingVertical: 12,
      borderRadius: 8,
    },
    primaryTutorialButton: {
      backgroundColor: colors.accent,
    },
    secondaryTutorialButton: {
      backgroundColor: 'transparent',
      borderWidth: 1,
      borderColor: colors.border,
    },
    tutorialButtonText: {
      fontSize: 16,
      fontWeight: '600',
    },
    primaryTutorialButtonText: {
      color: '#FFFFFF',
    },
    secondaryTutorialButtonText: {
      color: colors.text,
    },
    statsContainer: {
      flexDirection: 'row',
      justifyContent: 'center',
      alignItems: 'center',
      paddingVertical: 12,
      gap: 20,
    },
    statItem: {
      alignItems: 'center',
    },
    statValue: {
      fontSize: 18,
      fontWeight: 'bold',
      color: colors.text,
    },
    statLabel: {
      fontSize: 12,
      color: colors.textSecondary,
      marginTop: 2,
    },
  });

  const swipeActions: { [key: string]: SwipeAction } = {
    left: {
      id: 'pass',
      label: 'Pass',
      icon: 'close',
      color: '#FFFFFF',
      backgroundColor: colors.error,
    },
    right: {
      id: 'like',
      label: 'Add to Betslip',
      icon: 'heart',
      color: '#FFFFFF',
      backgroundColor: colors.success,
    },
    up: {
      id: 'super_like',
      label: 'Quick Analysis',
      icon: 'flash',
      color: '#FFFFFF',
      backgroundColor: colors.accent,
    },
  };

  useEffect(() => {
    loadBets();
    showTutorial();
  }, []);

  const loadBets = useCallback(async () => {
    try {
      await dispatch(fetchValueBets({
        sports: betting.followedSports,
        minEdge: betting.minEdgeFilter,
        limit: 20,
      }) as any);
    } catch (error) {
      console.error('Error loading bets:', error);
    }
  }, [dispatch, betting]);

  const showTutorial = useCallback(() => {
    Animated.parallel([
      Animated.timing(fadeAnim, {
        toValue: 1,
        duration: 300,
        useNativeDriver: true,
      }),
      Animated.spring(scaleAnim, {
        toValue: 1,
        useNativeDriver: true,
        tension: 100,
        friction: 8,
      }),
    ]).start();
  }, [fadeAnim, scaleAnim]);

  const hideTutorial = useCallback(() => {
    Animated.parallel([
      Animated.timing(fadeAnim, {
        toValue: 0,
        duration: 200,
        useNativeDriver: true,
      }),
      Animated.spring(scaleAnim, {
        toValue: 0.8,
        useNativeDriver: true,
        tension: 100,
        friction: 8,
      }),
    ]).start(() => {
      setTutorial(false);
    });
  }, [fadeAnim, scaleAnim]);

  const handleSwipeLeft = useCallback(async (betId: string) => {
    setSwipedBets(prev => new Set(prev).add(betId));
    setCurrentIndex(prev => prev + 1);
    
    try {
      await apiClient.quickAddToBetslip(betId, 'pass', 'swipe_discovery');
    } catch (error) {
      console.error('Error tracking pass action:', error);
    }
  }, []);

  const handleSwipeRight = useCallback(async (betId: string) => {
    setSwipedBets(prev => new Set(prev).add(betId));
    setCurrentIndex(prev => prev + 1);
    
    try {
      await apiClient.quickAddToBetslip(betId, 'add', 'swipe_discovery');
      Alert.alert(
        'Added to Betslip!',
        'The bet has been added to your betslip.',
        [{ text: 'OK' }]
      );
    } catch (error) {
      console.error('Error adding to betslip:', error);
      Alert.alert('Error', 'Failed to add bet to betslip');
    }
  }, []);

  const handleSwipeUp = useCallback((betId: string) => {
    setSwipedBets(prev => new Set(prev).add(betId));
    setCurrentIndex(prev => prev + 1);
    
    // Navigate to quick analysis
    navigation.navigate('QuickAnalysis' as never, { betId } as never);
  }, [navigation]);

  const handleActionButton = useCallback((action: string) => {
    const currentBet = filteredBets[currentIndex];
    if (!currentBet) return;

    switch (action) {
      case 'pass':
        handleSwipeLeft(currentBet.id);
        break;
      case 'like':
        handleSwipeRight(currentBet.id);
        break;
      case 'super_like':
        handleSwipeUp(currentBet.id);
        break;
    }
  }, [currentIndex, handleSwipeLeft, handleSwipeRight, handleSwipeUp]);

  const handleRefresh = useCallback(() => {
    setCurrentIndex(0);
    setSwipedBets(new Set());
    loadBets();
  }, [loadBets]);

  const filteredBets = valueBets.filter(bet => 
    !swipedBets.has(bet.id) && 
    bet.edge >= betting.minEdgeFilter &&
    (betting.followedSports.length === 0 || betting.followedSports.includes(bet.sport))
  );

  const currentBet = filteredBets[currentIndex];
  const nextBet = filteredBets[currentIndex + 1];
  const remainingCount = filteredBets.length - currentIndex;

  if (isLoading && filteredBets.length === 0) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.header}>
          <Text style={styles.headerTitle}>Discover Bets</Text>
        </View>
        <EmptyState
          icon="flash-outline"
          title="Loading Bets"
          message="Finding the best value betting opportunities for you..."
        />
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Discover Bets</Text>
        <View style={styles.headerActions}>
          <TouchableOpacity style={styles.headerButton} onPress={() => setTutorial(true)}>
            <Icon name="help-circle-outline" size={24} color={colors.text} />
          </TouchableOpacity>
          <TouchableOpacity style={styles.headerButton} onPress={handleRefresh}>
            <Icon name="refresh" size={24} color={colors.text} />
          </TouchableOpacity>
        </View>
      </View>

      {/* Stats */}
      <View style={styles.statsContainer}>
        <View style={styles.statItem}>
          <Text style={styles.statValue}>{remainingCount}</Text>
          <Text style={styles.statLabel}>Remaining</Text>
        </View>
        <View style={styles.statItem}>
          <Text style={styles.statValue}>{swipedBets.size}</Text>
          <Text style={styles.statLabel}>Reviewed</Text>
        </View>
        <View style={styles.statItem}>
          <Text style={styles.statValue}>
            {currentBet ? (currentBet.edge * 100).toFixed(1) : '0'}%
          </Text>
          <Text style={styles.statLabel}>Current Edge</Text>
        </View>
      </View>

      {/* Card Stack */}
      <View style={styles.cardStack}>
        {!currentBet ? (
          <EmptyState
            icon="checkmark-circle"
            title="All Done!"
            message="You've reviewed all available value bets. Check back later for new opportunities."
            actionText="Refresh"
            onAction={handleRefresh}
          />
        ) : (
          <>
            {/* Next Card (background) */}
            {nextBet && (
              <View style={[styles.cardContainer, styles.nextCard]}>
                <ValueBetCard
                  valueBet={nextBet}
                  onQuickAnalysis={() => {}}
                  onViewDetails={() => {}}
                  compactMode={false}
                  showProbabilities={true}
                  oddsFormat={betting.defaultOddsFormat || 'american'}
                />
              </View>
            )}

            {/* Current Card */}
            <View style={styles.cardContainer}>
              <SwipeableCard
                cardId={currentBet.id}
                leftAction={swipeActions.left}
                rightAction={swipeActions.right}
                upAction={swipeActions.up}
                onSwipeLeft={handleSwipeLeft}
                onSwipeRight={handleSwipeRight}
                onSwipeUp={handleSwipeUp}
              >
                <ValueBetCard
                  valueBet={currentBet}
                  onQuickAnalysis={() => handleSwipeUp(currentBet.id)}
                  onViewDetails={() => {
                    navigation.navigate('BetDetails' as never, { betId: currentBet.id } as never);
                  }}
                  compactMode={false}
                  showProbabilities={true}
                  oddsFormat={betting.defaultOddsFormat || 'american'}
                />
              </SwipeableCard>
            </View>
          </>
        )}
      </View>

      {/* Action Buttons */}
      {currentBet && (
        <View style={styles.actionButtons}>
          <TouchableOpacity
            style={[styles.actionButton, styles.passButton]}
            onPress={() => handleActionButton('pass')}
          >
            <Icon name="close" size={30} color="#FFFFFF" />
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.actionButton, styles.superLikeButton]}
            onPress={() => handleActionButton('super_like')}
          >
            <Icon name="flash" size={28} color="#FFFFFF" />
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.actionButton, styles.likeButton]}
            onPress={() => handleActionButton('like')}
          >
            <Icon name="heart" size={28} color="#FFFFFF" />
          </TouchableOpacity>
        </View>
      )}

      {/* Tutorial Overlay */}
      {tutorial && (
        <Animated.View 
          style={[
            styles.tutorialOverlay,
            {
              opacity: fadeAnim,
              transform: [{ scale: scaleAnim }],
            }
          ]}
        >
          <View style={styles.tutorialCard}>
            <Text style={styles.tutorialTitle}>How to Discover Bets</Text>
            <Text style={styles.tutorialText}>
              Swipe left to pass on a bet{'\n'}
              Swipe right to add to your betslip{'\n'}
              Swipe up for quick analysis{'\n\n'}
              Or use the buttons below
            </Text>
            <View style={styles.tutorialActions}>
              <TouchableOpacity 
                style={[styles.tutorialButton, styles.primaryTutorialButton]}
                onPress={hideTutorial}
              >
                <Text style={[styles.tutorialButtonText, styles.primaryTutorialButtonText]}>
                  Got It
                </Text>
              </TouchableOpacity>
            </View>
          </View>
        </Animated.View>
      )}
    </SafeAreaView>
  );
};

export default SwipeDiscoveryScreen;