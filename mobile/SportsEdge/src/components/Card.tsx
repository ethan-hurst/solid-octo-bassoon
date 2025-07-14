/**
 * Card Component - Mobile-optimized content container
 */
import React from 'react';
import {
  View,
  StyleSheet,
  TouchableOpacity,
  ViewStyle,
} from 'react-native';
import { useSelector } from 'react-redux';

import { RootState } from '../store';

interface CardProps {
  children: React.ReactNode;
  variant?: 'default' | 'elevated' | 'outlined' | 'filled';
  padding?: 'none' | 'small' | 'medium' | 'large';
  margin?: 'none' | 'small' | 'medium' | 'large';
  onPress?: () => void;
  disabled?: boolean;
  style?: ViewStyle;
}

const Card: React.FC<CardProps> = ({
  children,
  variant = 'default',
  padding = 'medium',
  margin = 'none',
  onPress,
  disabled = false,
  style,
}) => {
  const theme = useSelector((state: RootState) => state.userPreferences.theme);

  const isDark = theme.theme === 'dark' || 
    (theme.theme === 'auto' && new Date().getHours() > 18);

  const colors = {
    background: isDark ? '#1E293B' : '#FFFFFF',
    surface: isDark ? '#334155' : '#F8FAFC',
    border: isDark ? '#475569' : '#E2E8F0',
    shadow: isDark ? '#000000' : '#64748B',
  };

  const getPaddingConfig = () => {
    switch (padding) {
      case 'none':
        return { paddingHorizontal: 0, paddingVertical: 0 };
      case 'small':
        return { paddingHorizontal: 12, paddingVertical: 8 };
      case 'large':
        return { paddingHorizontal: 24, paddingVertical: 20 };
      case 'medium':
      default:
        return { paddingHorizontal: 16, paddingVertical: 12 };
    }
  };

  const getMarginConfig = () => {
    switch (margin) {
      case 'none':
        return { marginHorizontal: 0, marginVertical: 0 };
      case 'small':
        return { marginHorizontal: 8, marginVertical: 4 };
      case 'large':
        return { marginHorizontal: 20, marginVertical: 16 };
      case 'medium':
      default:
        return { marginHorizontal: 16, marginVertical: 8 };
    }
  };

  const getVariantStyles = () => {
    const baseStyle = {
      borderRadius: 12,
      ...getPaddingConfig(),
      ...getMarginConfig(),
    };

    switch (variant) {
      case 'elevated':
        return {
          ...baseStyle,
          backgroundColor: colors.background,
          shadowColor: colors.shadow,
          shadowOffset: { width: 0, height: 4 },
          shadowOpacity: isDark ? 0.3 : 0.1,
          shadowRadius: 8,
          elevation: 8,
        };
      case 'outlined':
        return {
          ...baseStyle,
          backgroundColor: colors.background,
          borderWidth: 1,
          borderColor: colors.border,
        };
      case 'filled':
        return {
          ...baseStyle,
          backgroundColor: colors.surface,
        };
      case 'default':
      default:
        return {
          ...baseStyle,
          backgroundColor: colors.background,
          shadowColor: colors.shadow,
          shadowOffset: { width: 0, height: 2 },
          shadowOpacity: isDark ? 0.2 : 0.05,
          shadowRadius: 4,
          elevation: 2,
        };
    }
  };

  const styles = StyleSheet.create({
    card: {
      ...getVariantStyles(),
      opacity: disabled ? 0.6 : 1,
    },
    pressable: {
      ...getVariantStyles(),
      opacity: disabled ? 0.6 : 1,
    },
  });

  if (onPress) {
    return (
      <TouchableOpacity
        style={[styles.pressable, style]}
        onPress={onPress}
        disabled={disabled}
        activeOpacity={0.8}
      >
        {children}
      </TouchableOpacity>
    );
  }

  return (
    <View style={[styles.card, style]}>
      {children}
    </View>
  );
};

export default Card;