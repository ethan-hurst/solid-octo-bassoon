/**
 * Badge Component - Mobile-optimized status and notification badge
 */
import React from 'react';
import {
  View,
  Text,
  StyleSheet,
} from 'react-native';
import { useSelector } from 'react-redux';
import Icon from 'react-native-vector-icons/Ionicons';

import { RootState } from '../store';

interface BadgeProps {
  children?: React.ReactNode;
  text?: string;
  count?: number;
  variant?: 'default' | 'primary' | 'secondary' | 'success' | 'warning' | 'error' | 'info';
  size?: 'small' | 'medium' | 'large';
  shape?: 'rounded' | 'square' | 'circle';
  icon?: string;
  showZero?: boolean;
  maxCount?: number;
  position?: 'top-right' | 'top-left' | 'bottom-right' | 'bottom-left' | 'inline';
  offset?: { x: number; y: number };
  style?: any;
}

const Badge: React.FC<BadgeProps> = ({
  children,
  text,
  count,
  variant = 'default',
  size = 'medium',
  shape = 'rounded',
  icon,
  showZero = false,
  maxCount = 99,
  position = 'inline',
  offset = { x: 0, y: 0 },
  style,
}) => {
  const theme = useSelector((state: RootState) => state.userPreferences.theme);

  const isDark = theme.theme === 'dark' || 
    (theme.theme === 'auto' && new Date().getHours() > 18);

  const colors = {
    default: isDark ? '#475569' : '#64748B',
    primary: theme.accentColor,
    secondary: isDark ? '#334155' : '#E2E8F0',
    success: '#10B981',
    warning: '#F59E0B',
    error: '#EF4444',
    info: '#3B82F6',
    text: '#FFFFFF',
    textSecondary: isDark ? '#F1F5F9' : '#1E293B',
  };

  const getSizeConfig = () => {
    switch (size) {
      case 'small':
        return {
          minHeight: 16,
          minWidth: 16,
          paddingHorizontal: 4,
          paddingVertical: 2,
          fontSize: 10,
          iconSize: 10,
          borderRadius: shape === 'circle' ? 8 : 4,
        };
      case 'large':
        return {
          minHeight: 28,
          minWidth: 28,
          paddingHorizontal: 8,
          paddingVertical: 4,
          fontSize: 14,
          iconSize: 16,
          borderRadius: shape === 'circle' ? 14 : 8,
        };
      case 'medium':
      default:
        return {
          minHeight: 20,
          minWidth: 20,
          paddingHorizontal: 6,
          paddingVertical: 2,
          fontSize: 12,
          iconSize: 12,
          borderRadius: shape === 'circle' ? 10 : 6,
        };
    }
  };

  const sizeConfig = getSizeConfig();

  const getVariantColors = () => {
    const textColor = variant === 'secondary' ? colors.textSecondary : colors.text;
    
    return {
      backgroundColor: colors[variant],
      textColor,
    };
  };

  const variantColors = getVariantColors();

  const getDisplayText = () => {
    if (text) return text;
    if (typeof count === 'number') {
      if (count === 0 && !showZero) return '';
      return count > maxCount ? `${maxCount}+` : count.toString();
    }
    return '';
  };

  const displayText = getDisplayText();
  const shouldRender = displayText !== '' || icon || children;

  if (!shouldRender) return null;

  const getPositionStyles = () => {
    if (position === 'inline') return {};

    const basePosition = {
      position: 'absolute' as const,
      zIndex: 1,
    };

    switch (position) {
      case 'top-right':
        return {
          ...basePosition,
          top: -sizeConfig.minHeight / 2 + offset.y,
          right: -sizeConfig.minWidth / 2 + offset.x,
        };
      case 'top-left':
        return {
          ...basePosition,
          top: -sizeConfig.minHeight / 2 + offset.y,
          left: -sizeConfig.minWidth / 2 + offset.x,
        };
      case 'bottom-right':
        return {
          ...basePosition,
          bottom: -sizeConfig.minHeight / 2 + offset.y,
          right: -sizeConfig.minWidth / 2 + offset.x,
        };
      case 'bottom-left':
        return {
          ...basePosition,
          bottom: -sizeConfig.minHeight / 2 + offset.y,
          left: -sizeConfig.minWidth / 2 + offset.x,
        };
      default:
        return basePosition;
    }
  };

  const styles = StyleSheet.create({
    container: {
      position: 'relative',
    },
    badge: {
      backgroundColor: variantColors.backgroundColor,
      minHeight: sizeConfig.minHeight,
      minWidth: sizeConfig.minWidth,
      borderRadius: shape === 'square' ? 4 : sizeConfig.borderRadius,
      paddingHorizontal: displayText || icon ? sizeConfig.paddingHorizontal : 0,
      paddingVertical: sizeConfig.paddingVertical,
      justifyContent: 'center',
      alignItems: 'center',
      flexDirection: 'row',
      ...getPositionStyles(),
    },
    text: {
      color: variantColors.textColor,
      fontSize: sizeConfig.fontSize,
      fontWeight: '600',
      textAlign: 'center',
      lineHeight: sizeConfig.fontSize + 2,
    },
    icon: {
      marginRight: displayText ? 2 : 0,
    },
  });

  const badgeContent = (
    <View style={[styles.badge, style]}>
      {icon && (
        <Icon
          name={icon}
          size={sizeConfig.iconSize}
          color={variantColors.textColor}
          style={styles.icon}
        />
      )}
      {displayText && (
        <Text style={styles.text} numberOfLines={1}>
          {displayText}
        </Text>
      )}
    </View>
  );

  if (position === 'inline') {
    return badgeContent;
  }

  return (
    <View style={styles.container}>
      {children}
      {badgeContent}
    </View>
  );
};

export default Badge;