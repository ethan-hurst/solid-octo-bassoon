/**
 * Avatar Component - Mobile-optimized user profile display
 */
import React, { useState } from 'react';
import {
  View,
  Text,
  Image,
  StyleSheet,
  TouchableOpacity,
} from 'react-native';
import { useSelector } from 'react-redux';
import Icon from 'react-native-vector-icons/Ionicons';

import { RootState } from '../store';

interface AvatarProps {
  source?: { uri: string } | number;
  name?: string;
  size?: number | 'small' | 'medium' | 'large' | 'xlarge';
  shape?: 'circle' | 'square' | 'rounded';
  onPress?: () => void;
  showBadge?: boolean;
  badgeColor?: string;
  badgePosition?: 'top-right' | 'bottom-right';
  placeholder?: string;
  backgroundColor?: string;
  textColor?: string;
  borderWidth?: number;
  borderColor?: string;
  style?: any;
}

const Avatar: React.FC<AvatarProps> = ({
  source,
  name,
  size = 'medium',
  shape = 'circle',
  onPress,
  showBadge = false,
  badgeColor,
  badgePosition = 'bottom-right',
  placeholder,
  backgroundColor,
  textColor,
  borderWidth = 0,
  borderColor,
  style,
}) => {
  const theme = useSelector((state: RootState) => state.userPreferences.theme);
  const [imageError, setImageError] = useState(false);

  const isDark = theme.theme === 'dark' || 
    (theme.theme === 'auto' && new Date().getHours() > 18);

  const colors = {
    background: backgroundColor || (isDark ? '#475569' : '#E2E8F0'),
    text: textColor || (isDark ? '#F1F5F9' : '#1E293B'),
    badge: badgeColor || '#10B981',
    border: borderColor || theme.accentColor,
    placeholder: isDark ? '#64748B' : '#9CA3AF',
  };

  const getSizeValue = () => {
    if (typeof size === 'number') return size;
    
    switch (size) {
      case 'small':
        return 32;
      case 'large':
        return 64;
      case 'xlarge':
        return 80;
      case 'medium':
      default:
        return 48;
    }
  };

  const sizeValue = getSizeValue();
  const badgeSize = Math.max(sizeValue * 0.25, 8);
  const fontSize = sizeValue * 0.4;

  const getBorderRadius = () => {
    switch (shape) {
      case 'square':
        return 0;
      case 'rounded':
        return sizeValue * 0.2;
      case 'circle':
      default:
        return sizeValue / 2;
    }
  };

  const getInitials = () => {
    if (!name) return placeholder || '?';
    
    const names = name.trim().split(' ');
    if (names.length >= 2) {
      return `${names[0][0]}${names[names.length - 1][0]}`.toUpperCase();
    }
    return names[0][0].toUpperCase();
  };

  const getBadgePosition = () => {
    const badgeOffset = badgeSize / 2;
    
    switch (badgePosition) {
      case 'top-right':
        return {
          position: 'absolute' as const,
          top: -badgeOffset,
          right: -badgeOffset,
        };
      case 'bottom-right':
      default:
        return {
          position: 'absolute' as const,
          bottom: -badgeOffset,
          right: -badgeOffset,
        };
    }
  };

  const styles = StyleSheet.create({
    container: {
      position: 'relative',
    },
    avatar: {
      width: sizeValue,
      height: sizeValue,
      borderRadius: getBorderRadius(),
      backgroundColor: colors.background,
      borderWidth,
      borderColor: colors.border,
      justifyContent: 'center',
      alignItems: 'center',
      overflow: 'hidden',
    },
    image: {
      width: '100%',
      height: '100%',
      borderRadius: getBorderRadius(),
    },
    text: {
      fontSize,
      fontWeight: '600',
      color: colors.text,
      textAlign: 'center',
    },
    placeholder: {
      justifyContent: 'center',
      alignItems: 'center',
    },
    badge: {
      width: badgeSize,
      height: badgeSize,
      borderRadius: badgeSize / 2,
      backgroundColor: colors.badge,
      ...getBadgePosition(),
      borderWidth: 2,
      borderColor: '#FFFFFF',
    },
    pressable: {
      opacity: 0.8,
    },
  });

  const renderContent = () => {
    // Show image if source is provided and no error
    if (source && !imageError) {
      return (
        <Image
          source={source}
          style={styles.image}
          onError={() => setImageError(true)}
          resizeMode="cover"
        />
      );
    }

    // Show initials or placeholder
    if (name || placeholder) {
      return (
        <Text style={styles.text}>
          {getInitials()}
        </Text>
      );
    }

    // Show default icon
    return (
      <View style={styles.placeholder}>
        <Icon
          name="person"
          size={fontSize}
          color={colors.placeholder}
        />
      </View>
    );
  };

  const avatarElement = (
    <View style={[styles.container, style]}>
      <View style={styles.avatar}>
        {renderContent()}
      </View>
      {showBadge && <View style={styles.badge} />}
    </View>
  );

  if (onPress) {
    return (
      <TouchableOpacity
        onPress={onPress}
        style={styles.pressable}
        activeOpacity={0.8}
      >
        {avatarElement}
      </TouchableOpacity>
    );
  }

  return avatarElement;
};

export default Avatar;