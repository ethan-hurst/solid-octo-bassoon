/**
 * Custom Button Component - Mobile-optimized with haptic feedback
 */
import React from 'react';
import {
  TouchableOpacity,
  Text,
  StyleSheet,
  ActivityIndicator,
  View,
  Haptics,
  Platform,
} from 'react-native';
import { useSelector } from 'react-redux';
import Icon from 'react-native-vector-icons/Ionicons';

import { RootState } from '../store';

interface ButtonProps {
  title: string;
  onPress: () => void;
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger';
  size?: 'small' | 'medium' | 'large';
  loading?: boolean;
  disabled?: boolean;
  icon?: string;
  iconPosition?: 'left' | 'right';
  fullWidth?: boolean;
  hapticFeedback?: boolean;
  style?: any;
  textStyle?: any;
}

const Button: React.FC<ButtonProps> = ({
  title,
  onPress,
  variant = 'primary',
  size = 'medium',
  loading = false,
  disabled = false,
  icon,
  iconPosition = 'left',
  fullWidth = false,
  hapticFeedback = true,
  style,
  textStyle,
}) => {
  const theme = useSelector((state: RootState) => state.userPreferences.theme);

  const isDark = theme.theme === 'dark' || 
    (theme.theme === 'auto' && new Date().getHours() > 18);

  const colors = {
    primary: theme.accentColor,
    secondary: isDark ? '#334155' : '#E2E8F0',
    outline: 'transparent',
    ghost: 'transparent',
    danger: '#EF4444',
    text: isDark ? '#F1F5F9' : '#1E293B',
    textSecondary: isDark ? '#94A3B8' : '#64748B',
    white: '#FFFFFF',
    border: isDark ? '#475569' : '#D1D5DB',
  };

  const getButtonColors = () => {
    switch (variant) {
      case 'primary':
        return {
          background: colors.primary,
          text: colors.white,
          border: colors.primary,
        };
      case 'secondary':
        return {
          background: colors.secondary,
          text: colors.text,
          border: colors.secondary,
        };
      case 'outline':
        return {
          background: colors.outline,
          text: colors.primary,
          border: colors.primary,
        };
      case 'ghost':
        return {
          background: colors.ghost,
          text: colors.text,
          border: 'transparent',
        };
      case 'danger':
        return {
          background: colors.danger,
          text: colors.white,
          border: colors.danger,
        };
      default:
        return {
          background: colors.primary,
          text: colors.white,
          border: colors.primary,
        };
    }
  };

  const getSizeConfig = () => {
    switch (size) {
      case 'small':
        return {
          paddingVertical: 8,
          paddingHorizontal: 16,
          fontSize: 14,
          iconSize: 16,
          borderRadius: 8,
        };
      case 'large':
        return {
          paddingVertical: 16,
          paddingHorizontal: 32,
          fontSize: 18,
          iconSize: 24,
          borderRadius: 12,
        };
      case 'medium':
      default:
        return {
          paddingVertical: 12,
          paddingHorizontal: 24,
          fontSize: 16,
          iconSize: 20,
          borderRadius: 10,
        };
    }
  };

  const buttonColors = getButtonColors();
  const sizeConfig = getSizeConfig();

  const styles = StyleSheet.create({
    button: {
      flexDirection: 'row',
      alignItems: 'center',
      justifyContent: 'center',
      backgroundColor: buttonColors.background,
      borderColor: buttonColors.border,
      borderWidth: variant === 'outline' ? 1 : 0,
      borderRadius: sizeConfig.borderRadius,
      paddingVertical: sizeConfig.paddingVertical,
      paddingHorizontal: sizeConfig.paddingHorizontal,
      opacity: disabled || loading ? 0.6 : 1,
      width: fullWidth ? '100%' : undefined,
      shadowColor: variant === 'primary' || variant === 'danger' ? buttonColors.background : 'transparent',
      shadowOffset: { width: 0, height: 2 },
      shadowOpacity: variant === 'primary' || variant === 'danger' ? 0.2 : 0,
      shadowRadius: 4,
      elevation: variant === 'primary' || variant === 'danger' ? 3 : 0,
    },
    text: {
      fontSize: sizeConfig.fontSize,
      fontWeight: '600',
      color: buttonColors.text,
      textAlign: 'center',
    },
    iconLeft: {
      marginRight: 8,
    },
    iconRight: {
      marginLeft: 8,
    },
    loadingContainer: {
      flexDirection: 'row',
      alignItems: 'center',
    },
    loadingText: {
      marginLeft: 8,
    },
  });

  const handlePress = () => {
    if (disabled || loading) return;

    // Haptic feedback
    if (hapticFeedback && Platform.OS === 'ios') {
      Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    }

    onPress();
  };

  const renderContent = () => {
    if (loading) {
      return (
        <View style={styles.loadingContainer}>
          <ActivityIndicator 
            size="small" 
            color={buttonColors.text} 
          />
          <Text style={[styles.text, styles.loadingText, textStyle]}>
            Loading...
          </Text>
        </View>
      );
    }

    return (
      <>
        {icon && iconPosition === 'left' && (
          <Icon 
            name={icon} 
            size={sizeConfig.iconSize} 
            color={buttonColors.text}
            style={styles.iconLeft}
          />
        )}
        <Text style={[styles.text, textStyle]}>{title}</Text>
        {icon && iconPosition === 'right' && (
          <Icon 
            name={icon} 
            size={sizeConfig.iconSize} 
            color={buttonColors.text}
            style={styles.iconRight}
          />
        )}
      </>
    );
  };

  return (
    <TouchableOpacity
      style={[styles.button, style]}
      onPress={handlePress}
      disabled={disabled || loading}
      activeOpacity={0.8}
    >
      {renderContent()}
    </TouchableOpacity>
  );
};

export default Button;