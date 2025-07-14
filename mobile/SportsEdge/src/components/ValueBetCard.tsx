/**
 * Value Bet Card Component
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

interface ValueBetCardProps {
  valueBet: {
    id: string;
    sport: string;
    event: string;
    market: string;
    selection: string;
    odds: number;
    fair_odds: number;
    edge: number;
    bookmaker: string;
    stake_suggestion: number;
    confidence: number;
    created_at: string;
    expires_at?: string;
  };
  onQuickAnalysis: () => void;
  onViewDetails: () => void;
  compactMode?: boolean;
  showProbabilities?: boolean;
  oddsFormat?: 'american' | 'decimal' | 'fractional';
}

const { width } = Dimensions.get('window');

const ValueBetCard: React.FC<ValueBetCardProps> = ({
  valueBet,
  onQuickAnalysis,
  onViewDetails,
  compactMode = false,
  showProbabilities = true,
  oddsFormat = 'american',
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
    compactCard: {
      padding: 12,
    },
    header: {
      flexDirection: 'row',
      justifyContent: 'space-between',
      alignItems: 'flex-start',
      marginBottom: 12,
    },
    eventInfo: {
      flex: 1,
      marginRight: 12,
    },
    eventText: {
      fontSize: compactMode ? 14 : 16,
      fontWeight: '600',
      color: colors.text,
      marginBottom: 4,
    },
    marketText: {
      fontSize: compactMode ? 12 : 14,
      color: colors.textSecondary,
      marginBottom: 2,
    },
    selectionText: {
      fontSize: compactMode ? 12 : 14,
      fontWeight: '500',
      color: colors.text,
    },
    edgeContainer: {
      alignItems: 'center',
      backgroundColor: colors.success,
      borderRadius: 8,
      paddingHorizontal: 12,
      paddingVertical: 6,
      minWidth: 60,
    },
    edgeText: {
      fontSize: compactMode ? 14 : 16,
      fontWeight: 'bold',
      color: '#FFFFFF',
    },
    edgeLabel: {
      fontSize: 10,
      color: '#FFFFFF',
      opacity: 0.9,
    },
    oddsContainer: {
      flexDirection: 'row',
      justifyContent: 'space-between',
      marginBottom: 12,
    },
    oddsItem: {
      flex: 1,
      alignItems: 'center',
      paddingVertical: 8,
      paddingHorizontal: 12,
      backgroundColor: colors.surface,
      borderRadius: 8,
      marginHorizontal: 4,
    },
    oddsLabel: {
      fontSize: 11,
      color: colors.textSecondary,
      marginBottom: 2,
    },
    oddsValue: {
      fontSize: compactMode ? 14 : 16,
      fontWeight: '600',
      color: colors.text,
    },
    fairOddsValue: {
      color: colors.accent,
    },
    metaContainer: {
      flexDirection: 'row',
      justifyContent: 'space-between',
      alignItems: 'center',
      marginBottom: 12,
    },
    bookmakerContainer: {
      flexDirection: 'row',
      alignItems: 'center',
    },
    bookmakerText: {
      fontSize: 12,
      fontWeight: '500',
      color: colors.text,
      marginLeft: 4,
    },
    confidenceContainer: {
      flexDirection: 'row',
      alignItems: 'center',
    },
    confidenceText: {
      fontSize: 11,
      color: colors.textSecondary,
      marginLeft: 4,
    },
    stakeContainer: {
      backgroundColor: colors.surface,
      borderRadius: 8,
      padding: 8,
      marginBottom: 12,
    },
    stakeText: {
      fontSize: 12,
      color: colors.textSecondary,
      textAlign: 'center',
    },
    stakeValue: {
      fontSize: 14,
      fontWeight: '600',
      color: colors.accent,
      textAlign: 'center',
    },
    actionsContainer: {
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
    sportIcon: {
      position: 'absolute',
      top: 8,
      right: 8,
      opacity: 0.3,
    },
    timeContainer: {
      flexDirection: 'row',
      alignItems: 'center',
      marginTop: 4,
    },
    timeText: {
      fontSize: 10,
      color: colors.textSecondary,
      marginLeft: 4,
    },
  });

  const formatOdds = (odds: number): string => {
    switch (oddsFormat) {
      case 'decimal':
        return odds.toFixed(2);
      case 'fractional':
        const decimal = odds - 1;
        const gcd = (a: number, b: number): number => b === 0 ? a : gcd(b, a % b);
        const numerator = Math.round(decimal * 100);
        const denominator = 100;
        const divisor = gcd(numerator, denominator);
        return `${numerator / divisor}/${denominator / divisor}`;
      case 'american':
      default:
        return odds >= 2.0 ? `+${Math.round((odds - 1) * 100)}` : `-${Math.round(100 / (odds - 1))}`;
    }
  };

  const getSportIcon = (sport: string): string => {
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

  const getConfidenceColor = (confidence: number): string => {
    if (confidence >= 0.8) return colors.success;
    if (confidence >= 0.6) return colors.warning;
    return colors.error;
  };

  const getTimeRemaining = (): string => {
    if (!valueBet.expires_at) return '';
    
    const now = new Date();
    const expires = new Date(valueBet.expires_at);
    const diff = expires.getTime() - now.getTime();
    
    if (diff <= 0) return 'Expired';
    
    const hours = Math.floor(diff / (1000 * 60 * 60));
    const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
    
    if (hours > 0) return `${hours}h ${minutes}m`;
    return `${minutes}m`;
  };

  return (
    <TouchableOpacity 
      style={[styles.card, compactMode && styles.compactCard]}
      onPress={onViewDetails}
      activeOpacity={0.8}
    >
      {/* Sport Icon */}
      <Icon 
        name={getSportIcon(valueBet.sport)} 
        size={24} 
        color={colors.border}
        style={styles.sportIcon}
      />

      {/* Header */}
      <View style={styles.header}>
        <View style={styles.eventInfo}>
          <Text style={styles.eventText} numberOfLines={1}>
            {valueBet.event}
          </Text>
          <Text style={styles.marketText} numberOfLines={1}>
            {valueBet.market}
          </Text>
          <Text style={styles.selectionText} numberOfLines={1}>
            {valueBet.selection}
          </Text>
        </View>
        
        <View style={styles.edgeContainer}>
          <Text style={styles.edgeText}>
            {(valueBet.edge * 100).toFixed(1)}%
          </Text>
          <Text style={styles.edgeLabel}>EDGE</Text>
        </View>
      </View>

      {/* Odds Comparison */}
      <View style={styles.oddsContainer}>
        <View style={styles.oddsItem}>
          <Text style={styles.oddsLabel}>Bookmaker</Text>
          <Text style={styles.oddsValue}>
            {formatOdds(valueBet.odds)}
          </Text>
        </View>
        <View style={styles.oddsItem}>
          <Text style={styles.oddsLabel}>Fair Value</Text>
          <Text style={[styles.oddsValue, styles.fairOddsValue]}>
            {formatOdds(valueBet.fair_odds)}
          </Text>
        </View>
        {showProbabilities && (
          <View style={styles.oddsItem}>
            <Text style={styles.oddsLabel}>Probability</Text>
            <Text style={styles.oddsValue}>
              {(1 / valueBet.fair_odds * 100).toFixed(1)}%
            </Text>
          </View>
        )}
      </View>

      {/* Meta Information */}
      <View style={styles.metaContainer}>
        <View style={styles.bookmakerContainer}>
          <Icon name="storefront-outline" size={14} color={colors.textSecondary} />
          <Text style={styles.bookmakerText}>{valueBet.bookmaker}</Text>
        </View>
        
        <View style={styles.confidenceContainer}>
          <Icon 
            name="shield-checkmark" 
            size={14} 
            color={getConfidenceColor(valueBet.confidence)} 
          />
          <Text style={styles.confidenceText}>
            {(valueBet.confidence * 100).toFixed(0)}% confidence
          </Text>
        </View>
      </View>

      {/* Suggested Stake */}
      {!compactMode && (
        <View style={styles.stakeContainer}>
          <Text style={styles.stakeText}>Suggested Stake</Text>
          <Text style={styles.stakeValue}>
            ${valueBet.stake_suggestion.toFixed(0)}
          </Text>
        </View>
      )}

      {/* Time Information */}
      {valueBet.expires_at && (
        <View style={styles.timeContainer}>
          <Icon name="time-outline" size={12} color={colors.textSecondary} />
          <Text style={styles.timeText}>
            Expires in {getTimeRemaining()}
          </Text>
        </View>
      )}

      {/* Action Buttons */}
      <View style={styles.actionsContainer}>
        <TouchableOpacity 
          style={[styles.actionButton, styles.primaryAction]}
          onPress={onQuickAnalysis}
          activeOpacity={0.8}
        >
          <Icon name="flash" size={16} color="#FFFFFF" />
          <Text style={[styles.actionText, styles.primaryActionText]}>
            Quick Analysis
          </Text>
        </TouchableOpacity>
        
        <TouchableOpacity 
          style={[styles.actionButton, styles.secondaryAction]}
          onPress={onViewDetails}
          activeOpacity={0.8}
        >
          <Icon name="information-circle-outline" size={16} color={colors.text} />
          <Text style={[styles.actionText, styles.secondaryActionText]}>
            Details
          </Text>
        </TouchableOpacity>
      </View>
    </TouchableOpacity>
  );
};

export default ValueBetCard;