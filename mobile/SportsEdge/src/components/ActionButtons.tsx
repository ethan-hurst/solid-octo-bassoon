/**
 * Action Buttons Component - Quick actions for betting decisions
 */
import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Alert,
} from 'react-native';
import { useSelector, useDispatch } from 'react-redux';
import Icon from 'react-native-vector-icons/Ionicons';

import { RootState } from '../store';
import { apiClient } from '../services';

interface ActionButtonsProps {
  betId: string;
  recommendation: {
    action: 'strong_bet' | 'bet' | 'pass' | 'avoid';
    suggested_stake: number;
    max_stake: number;
  };
  onClose: () => void;
}

const ActionButtons: React.FC<ActionButtonsProps> = ({
  betId,
  recommendation,
  onClose,
}) => {
  const dispatch = useDispatch();
  const theme = useSelector((state: RootState) => state.userPreferences.theme);
  const [isLoading, setIsLoading] = useState(false);

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
      paddingTop: 20,
      paddingBottom: 10,
      gap: 12,
    },
    buttonRow: {
      flexDirection: 'row',
      gap: 12,
    },
    button: {
      flex: 1,
      flexDirection: 'row',
      alignItems: 'center',
      justifyContent: 'center',
      paddingVertical: 14,
      paddingHorizontal: 16,
      borderRadius: 12,
      borderWidth: 1,
    },
    primaryButton: {
      backgroundColor: colors.success,
      borderColor: colors.success,
    },
    secondaryButton: {
      backgroundColor: colors.accent,
      borderColor: colors.accent,
    },
    outlineButton: {
      backgroundColor: 'transparent',
      borderColor: colors.border,
    },
    warningButton: {
      backgroundColor: colors.warning,
      borderColor: colors.warning,
    },
    buttonText: {
      fontSize: 16,
      fontWeight: '600',
      marginLeft: 8,
    },
    primaryButtonText: {
      color: '#FFFFFF',
    },
    secondaryButtonText: {
      color: '#FFFFFF',
    },
    outlineButtonText: {
      color: colors.text,
    },
    warningButtonText: {
      color: '#FFFFFF',
    },
    disabledButton: {
      opacity: 0.5,
    },
    quickActionContainer: {
      backgroundColor: colors.surface,
      borderRadius: 12,
      padding: 16,
      borderWidth: 1,
      borderColor: colors.border,
    },
    quickActionTitle: {
      fontSize: 14,
      fontWeight: '600',
      color: colors.text,
      marginBottom: 12,
      textAlign: 'center',
    },
    stakeButtons: {
      flexDirection: 'row',
      justifyContent: 'space-between',
      gap: 8,
    },
    stakeButton: {
      flex: 1,
      backgroundColor: colors.background,
      borderRadius: 8,
      paddingVertical: 10,
      paddingHorizontal: 12,
      alignItems: 'center',
      borderWidth: 1,
      borderColor: colors.border,
    },
    selectedStakeButton: {
      backgroundColor: colors.accent,
      borderColor: colors.accent,
    },
    stakeButtonText: {
      fontSize: 12,
      fontWeight: '600',
      color: colors.textSecondary,
    },
    selectedStakeButtonText: {
      color: '#FFFFFF',
    },
    stakeAmount: {
      fontSize: 14,
      fontWeight: 'bold',
      color: colors.text,
      marginTop: 2,
    },
    selectedStakeAmount: {
      color: '#FFFFFF',
    },
  });

  const handleQuickBet = async (stakeAmount: number) => {
    try {
      setIsLoading(true);
      
      await apiClient.quickAddToBetslip(betId, 'add_with_stake', 'quick_analysis');
      
      Alert.alert(
        'Added to Betslip',
        `Bet added with $${stakeAmount} stake`,
        [
          { text: 'Continue Betting', onPress: onClose },
          { text: 'View Betslip', onPress: () => {
            // TODO: Navigate to betslip
            onClose();
          }},
        ]
      );
    } catch (error: any) {
      Alert.alert('Error', error.message || 'Failed to add bet to betslip');
    } finally {
      setIsLoading(false);
    }
  };

  const handleAddToBetslip = async () => {
    try {
      setIsLoading(true);
      
      await apiClient.quickAddToBetslip(betId, 'add', 'quick_analysis');
      
      Alert.alert(
        'Added to Betslip',
        'Bet has been added to your betslip',
        [{ text: 'OK', onPress: onClose }]
      );
    } catch (error: any) {
      Alert.alert('Error', error.message || 'Failed to add bet to betslip');
    } finally {
      setIsLoading(false);
    }
  };

  const handleShare = () => {
    // TODO: Implement share functionality
    Alert.alert('Share', 'Share functionality coming soon!');
  };

  const handleBookmark = () => {
    // TODO: Implement bookmark functionality
    Alert.alert('Bookmark', 'Bookmark functionality coming soon!');
  };

  const shouldShowQuickBet = recommendation.action === 'strong_bet' || recommendation.action === 'bet';
  const suggestedStake = recommendation.suggested_stake;
  const maxStake = recommendation.max_stake;

  return (
    <View style={styles.container}>
      {/* Quick Bet Options */}
      {shouldShowQuickBet && (
        <View style={styles.quickActionContainer}>
          <Text style={styles.quickActionTitle}>Quick Bet</Text>
          <View style={styles.stakeButtons}>
            <TouchableOpacity
              style={styles.stakeButton}
              onPress={() => handleQuickBet(suggestedStake * 0.5)}
              disabled={isLoading}
            >
              <Text style={styles.stakeButtonText}>Conservative</Text>
              <Text style={styles.stakeAmount}>
                ${(suggestedStake * 0.5).toFixed(0)}
              </Text>
            </TouchableOpacity>
            
            <TouchableOpacity
              style={[styles.stakeButton, styles.selectedStakeButton]}
              onPress={() => handleQuickBet(suggestedStake)}
              disabled={isLoading}
            >
              <Text style={[styles.stakeButtonText, styles.selectedStakeButtonText]}>
                Suggested
              </Text>
              <Text style={[styles.stakeAmount, styles.selectedStakeAmount]}>
                ${suggestedStake.toFixed(0)}
              </Text>
            </TouchableOpacity>
            
            <TouchableOpacity
              style={styles.stakeButton}
              onPress={() => handleQuickBet(maxStake)}
              disabled={isLoading}
            >
              <Text style={styles.stakeButtonText}>Aggressive</Text>
              <Text style={styles.stakeAmount}>
                ${maxStake.toFixed(0)}
              </Text>
            </TouchableOpacity>
          </View>
        </View>
      )}

      {/* Primary Actions */}
      <View style={styles.buttonRow}>
        {shouldShowQuickBet ? (
          <TouchableOpacity
            style={[
              styles.button,
              styles.secondaryButton,
              isLoading && styles.disabledButton,
            ]}
            onPress={handleAddToBetslip}
            disabled={isLoading}
          >
            <Icon name="add-circle" size={20} color="#FFFFFF" />
            <Text style={[styles.buttonText, styles.secondaryButtonText]}>
              Add to Betslip
            </Text>
          </TouchableOpacity>
        ) : (
          <TouchableOpacity
            style={[
              styles.button,
              styles.warningButton,
              isLoading && styles.disabledButton,
            ]}
            onPress={onClose}
            disabled={isLoading}
          >
            <Icon name="close-circle" size={20} color="#FFFFFF" />
            <Text style={[styles.buttonText, styles.warningButtonText]}>
              Pass on Bet
            </Text>
          </TouchableOpacity>
        )}
      </View>

      {/* Secondary Actions */}
      <View style={styles.buttonRow}>
        <TouchableOpacity
          style={[styles.button, styles.outlineButton]}
          onPress={handleShare}
        >
          <Icon name="share" size={18} color={colors.text} />
          <Text style={[styles.buttonText, styles.outlineButtonText]}>
            Share
          </Text>
        </TouchableOpacity>
        
        <TouchableOpacity
          style={[styles.button, styles.outlineButton]}
          onPress={handleBookmark}
        >
          <Icon name="bookmark" size={18} color={colors.text} />
          <Text style={[styles.buttonText, styles.outlineButtonText]}>
            Save
          </Text>
        </TouchableOpacity>
        
        <TouchableOpacity
          style={[styles.button, styles.outlineButton]}
          onPress={onClose}
        >
          <Icon name="close" size={18} color={colors.text} />
          <Text style={[styles.buttonText, styles.outlineButtonText]}>
            Close
          </Text>
        </TouchableOpacity>
      </View>
    </View>
  );
};

export default ActionButtons;