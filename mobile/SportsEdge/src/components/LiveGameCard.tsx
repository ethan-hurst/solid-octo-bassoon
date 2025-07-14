/**
 * Live Game Card Component
 */
import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Dimensions,
} from 'react-native';
import { useSelector } from 'react-redux';
import Icon from 'react-native-vector-icons/Ionicons';

import { RootState } from '../store';

interface LiveGameCardProps {
  game: {
    id: string;
    sport: string;
    home_team: string;
    away_team: string;
    home_score?: number;
    away_score?: number;
    status: 'upcoming' | 'live' | 'finished';
    start_time: string;
    game_time?: string;
    period?: string;
    odds?: {
      home: number;
      away: number;
      draw?: number;
    };
    last_update?: string;
  };
  onPress: () => void;
  onLiveBetting?: () => void;
  isOffline?: boolean;
}

const { width } = Dimensions.get('window');

const LiveGameCard: React.FC<LiveGameCardProps> = ({
  game,
  onPress,
  onLiveBetting,
  isOffline = false,
}) => {
  const theme = useSelector((state: RootState) => state.userPreferences.theme);

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
    live: '#EF4444',
    upcoming: '#F59E0B',
    finished: '#6B7280',
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'live':
        return colors.live;
      case 'upcoming':
        return colors.upcoming;
      case 'finished':
        return colors.finished;
      default:
        return colors.textSecondary;
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'live':
        return 'radio-button-on';
      case 'upcoming':
        return 'time';
      case 'finished':
        return 'checkmark-circle';
      default:
        return 'help-circle';
    }
  };

  const getSportIcon = (sport: string) => {
    const sportIcons: { [key: string]: string } = {
      'NFL': 'american-football',
      'NBA': 'basketball',
      'MLB': 'baseball',
      'NHL': 'hockey-puck',
      'EPL': 'football',
      'UEFA': 'football',
      'Tennis': 'tennis',
      'MMA': 'fitness',
      'Boxing': 'fitness',
    };
    return sportIcons[sport] || 'trophy';
  };

  const formatTime = (timeString: string) => {
    const date = new Date(timeString);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const formatDate = (timeString: string) => {
    const date = new Date(timeString);
    const today = new Date();
    const tomorrow = new Date(today);
    tomorrow.setDate(tomorrow.getDate() + 1);

    if (date.toDateString() === today.toDateString()) {
      return 'Today';
    } else if (date.toDateString() === tomorrow.toDateString()) {
      return 'Tomorrow';
    } else {
      return date.toLocaleDateString([], { month: 'short', day: 'numeric' });
    }
  };

  const styles = StyleSheet.create({
    card: {
      backgroundColor: colors.background,
      borderRadius: 12,
      padding: 16,
      borderWidth: 1,
      borderColor: colors.border,
      shadowColor: colors.text,
      shadowOffset: { width: 0, height: 2 },
      shadowOpacity: 0.1,
      shadowRadius: 4,
      elevation: 3,
    },
    header: {
      flexDirection: 'row',
      justifyContent: 'space-between',
      alignItems: 'center',
      marginBottom: 12,
    },
    sportInfo: {
      flexDirection: 'row',
      alignItems: 'center',
    },
    sportIcon: {
      marginRight: 8,
    },
    sportText: {
      fontSize: 14,
      fontWeight: '500',
      color: colors.text,
    },
    statusContainer: {
      flexDirection: 'row',
      alignItems: 'center',
      paddingHorizontal: 8,
      paddingVertical: 4,
      borderRadius: 12,
    },
    statusIcon: {
      marginRight: 4,
    },
    statusText: {
      fontSize: 12,
      fontWeight: '600',
      textTransform: 'uppercase',
    },
    matchup: {
      marginBottom: 12,
    },
    teamRow: {
      flexDirection: 'row',
      justifyContent: 'space-between',
      alignItems: 'center',
      marginBottom: 8,
    },
    teamName: {
      fontSize: 16,
      fontWeight: '600',
      color: colors.text,
      flex: 1,
    },
    score: {
      fontSize: 18,
      fontWeight: 'bold',
      color: colors.accent,
      minWidth: 30,
      textAlign: 'center',
    },
    separator: {
      alignSelf: 'center',
      fontSize: 14,
      color: colors.textSecondary,
      marginVertical: 4,
    },
    gameInfo: {
      flexDirection: 'row',
      justifyContent: 'space-between',
      alignItems: 'center',
      marginBottom: 12,
    },
    timeInfo: {
      flexDirection: 'row',
      alignItems: 'center',
    },
    timeText: {
      fontSize: 14,
      color: colors.textSecondary,
      marginLeft: 4,
    },
    gameTime: {
      fontSize: 14,
      fontWeight: '500',
      color: colors.accent,
    },
    oddsContainer: {
      flexDirection: 'row',
      justifyContent: 'space-between',
      marginBottom: 12,
    },
    oddsItem: {
      flex: 1,
      alignItems: 'center',
      paddingVertical: 6,
      paddingHorizontal: 8,
      backgroundColor: colors.surface,
      borderRadius: 6,
      marginHorizontal: 2,
    },
    oddsLabel: {
      fontSize: 10,
      color: colors.textSecondary,
      marginBottom: 2,
    },
    oddsValue: {
      fontSize: 14,
      fontWeight: '600',
      color: colors.text,
    },
    actions: {
      flexDirection: 'row',
      justifyContent: 'space-between',
    },
    actionButton: {
      flex: 1,
      flexDirection: 'row',
      alignItems: 'center',
      justifyContent: 'center',
      paddingVertical: 10,
      borderRadius: 8,
      marginHorizontal: 4,
    },
    primaryAction: {
      backgroundColor: colors.accent,
    },
    secondaryAction: {
      backgroundColor: colors.surface,
      borderWidth: 1,
      borderColor: colors.border,
    },
    disabledAction: {
      opacity: 0.5,
    },
    actionText: {
      fontSize: 13,
      fontWeight: '600',
      marginLeft: 4,
    },
    primaryActionText: {
      color: '#FFFFFF',
    },
    secondaryActionText: {
      color: colors.text,
    },
    offlineIndicator: {
      position: 'absolute',
      top: 8,
      right: 8,
      backgroundColor: colors.warning,
      borderRadius: 8,
      paddingHorizontal: 6,
      paddingVertical: 2,
    },
    offlineText: {
      fontSize: 10,
      color: '#FFFFFF',
      fontWeight: '600',
    },
    liveIndicator: {
      position: 'absolute',
      top: 8,
      right: 8,
      backgroundColor: colors.live,
      borderRadius: 8,
      paddingHorizontal: 6,
      paddingVertical: 2,
      flexDirection: 'row',
      alignItems: 'center',
    },
    liveText: {
      fontSize: 10,
      color: '#FFFFFF',
      fontWeight: '600',
      marginLeft: 2,
    },
  });

  const statusColor = getStatusColor(game.status);

  return (
    <TouchableOpacity 
      style={styles.card}
      onPress={onPress}
      activeOpacity={0.8}
    >
      {/* Offline Indicator */}
      {isOffline && (
        <View style={styles.offlineIndicator}>
          <Text style={styles.offlineText}>OFFLINE</Text>
        </View>
      )}

      {/* Live Indicator */}
      {game.status === 'live' && !isOffline && (
        <View style={styles.liveIndicator}>
          <View style={{
            width: 6,
            height: 6,
            borderRadius: 3,
            backgroundColor: '#FFFFFF',
          }} />
          <Text style={styles.liveText}>LIVE</Text>
        </View>
      )}

      {/* Header */}
      <View style={styles.header}>
        <View style={styles.sportInfo}>
          <Icon 
            name={getSportIcon(game.sport)} 
            size={18} 
            color={colors.accent}
            style={styles.sportIcon}
          />
          <Text style={styles.sportText}>{game.sport}</Text>
        </View>
        
        <View style={[styles.statusContainer, { backgroundColor: statusColor + '20' }]}>
          <Icon 
            name={getStatusIcon(game.status)} 
            size={12} 
            color={statusColor}
            style={styles.statusIcon}
          />
          <Text style={[styles.statusText, { color: statusColor }]}>
            {game.status}
          </Text>
        </View>
      </View>

      {/* Matchup */}
      <View style={styles.matchup}>
        <View style={styles.teamRow}>
          <Text style={styles.teamName}>{game.away_team}</Text>
          {game.away_score !== undefined && (
            <Text style={styles.score}>{game.away_score}</Text>
          )}
        </View>
        
        <Text style={styles.separator}>vs</Text>
        
        <View style={styles.teamRow}>
          <Text style={styles.teamName}>{game.home_team}</Text>
          {game.home_score !== undefined && (
            <Text style={styles.score}>{game.home_score}</Text>
          )}
        </View>
      </View>

      {/* Game Info */}
      <View style={styles.gameInfo}>
        <View style={styles.timeInfo}>
          <Icon name="calendar" size={14} color={colors.textSecondary} />
          <Text style={styles.timeText}>
            {formatDate(game.start_time)} at {formatTime(game.start_time)}
          </Text>
        </View>
        
        {game.game_time && game.status === 'live' && (
          <Text style={styles.gameTime}>
            {game.game_time} {game.period && `- ${game.period}`}
          </Text>
        )}
      </View>

      {/* Odds */}
      {game.odds && (
        <View style={styles.oddsContainer}>
          <View style={styles.oddsItem}>
            <Text style={styles.oddsLabel}>Away</Text>
            <Text style={styles.oddsValue}>
              {game.odds.away > 0 ? `+${game.odds.away}` : game.odds.away}
            </Text>
          </View>
          
          {game.odds.draw && (
            <View style={styles.oddsItem}>
              <Text style={styles.oddsLabel}>Draw</Text>
              <Text style={styles.oddsValue}>
                {game.odds.draw > 0 ? `+${game.odds.draw}` : game.odds.draw}
              </Text>
            </View>
          )}
          
          <View style={styles.oddsItem}>
            <Text style={styles.oddsLabel}>Home</Text>
            <Text style={styles.oddsValue}>
              {game.odds.home > 0 ? `+${game.odds.home}` : game.odds.home}
            </Text>
          </View>
        </View>
      )}

      {/* Actions */}
      <View style={styles.actions}>
        <TouchableOpacity 
          style={[styles.actionButton, styles.secondaryAction]}
          onPress={onPress}
          activeOpacity={0.8}
        >
          <Icon name="information-circle-outline" size={16} color={colors.text} />
          <Text style={[styles.actionText, styles.secondaryActionText]}>
            Details
          </Text>
        </TouchableOpacity>
        
        {game.status === 'live' && onLiveBetting && (
          <TouchableOpacity 
            style={[
              styles.actionButton, 
              styles.primaryAction,
              isOffline && styles.disabledAction,
            ]}
            onPress={onLiveBetting}
            disabled={isOffline}
            activeOpacity={0.8}
          >
            <Icon name="flash" size={16} color="#FFFFFF" />
            <Text style={[styles.actionText, styles.primaryActionText]}>
              Live Bet
            </Text>
          </TouchableOpacity>
        )}
      </View>
    </TouchableOpacity>
  );
};

export default LiveGameCard;