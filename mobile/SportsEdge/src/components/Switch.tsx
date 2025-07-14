/**
 * Switch Component - Mobile-optimized toggle switch
 */
import React, { useRef, useEffect } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  Animated,
  StyleSheet,
  Haptics,
  Platform,
} from 'react-native';
import { useSelector } from 'react-redux';

import { RootState } from '../store';

interface SwitchProps {
  value: boolean;
  onValueChange: (value: boolean) => void;
  disabled?: boolean;
  size?: 'small' | 'medium' | 'large';
  color?: string;
  label?: string;
  description?: string;
  hapticFeedback?: boolean;
  style?: any;
}

const Switch: React.FC<SwitchProps> = ({
  value,
  onValueChange,
  disabled = false,
  size = 'medium',
  color,
  label,
  description,
  hapticFeedback = true,
  style,
}) => {
  const theme = useSelector((state: RootState) => state.userPreferences.theme);
  const animatedValue = useRef(new Animated.Value(value ? 1 : 0)).current;
  const scaleValue = useRef(new Animated.Value(1)).current;

  const isDark = theme.theme === 'dark' || 
    (theme.theme === 'auto' && new Date().getHours() > 18);

  const colors = {
    background: isDark ? '#1E293B' : '#FFFFFF',
    text: isDark ? '#F1F5F9' : '#1E293B',
    textSecondary: isDark ? '#94A3B8' : '#64748B',
    switchOff: isDark ? '#475569' : '#D1D5DB',
    switchOn: color || theme.accentColor,
    thumbOff: isDark ? '#CBD5E1' : '#FFFFFF',
    thumbOn: '#FFFFFF',
    disabled: isDark ? '#374151' : '#F3F4F6',
  };

  const getSizeConfig = () => {
    switch (size) {
      case 'small':
        return {
          width: 40,
          height: 24,
          thumbSize: 18,
          padding: 3,
          borderRadius: 12,
        };
      case 'large':
        return {
          width: 60,
          height: 36,
          thumbSize: 28,
          padding: 4,
          borderRadius: 18,
        };
      case 'medium':
      default:
        return {
          width: 50,
          height: 30,
          thumbSize: 22,
          padding: 4,
          borderRadius: 15,
        };
    }
  };

  const sizeConfig = getSizeConfig();

  useEffect(() => {
    Animated.spring(animatedValue, {
      toValue: value ? 1 : 0,
      useNativeDriver: false,
      tension: 300,
      friction: 20,
    }).start();
  }, [value, animatedValue]);

  const handlePress = () => {
    if (disabled) return;

    // Haptic feedback
    if (hapticFeedback && Platform.OS === 'ios') {
      Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    }

    // Scale animation for press feedback
    Animated.sequence([
      Animated.timing(scaleValue, {
        toValue: 0.95,
        duration: 50,
        useNativeDriver: true,
      }),
      Animated.timing(scaleValue, {
        toValue: 1,
        duration: 50,
        useNativeDriver: true,
      }),
    ]).start();

    onValueChange(!value);
  };

  const thumbPosition = animatedValue.interpolate({
    inputRange: [0, 1],
    outputRange: [sizeConfig.padding, sizeConfig.width - sizeConfig.thumbSize - sizeConfig.padding],
  });

  const trackColor = animatedValue.interpolate({
    inputRange: [0, 1],
    outputRange: [colors.switchOff, colors.switchOn],
  });

  const thumbScale = animatedValue.interpolate({
    inputRange: [0, 0.5, 1],
    outputRange: [1, 1.1, 1],
  });

  const styles = StyleSheet.create({
    container: {
      flexDirection: 'row',
      alignItems: 'center',
      opacity: disabled ? 0.5 : 1,
    },
    labelContainer: {
      flex: 1,
      marginRight: 12,
    },
    label: {
      fontSize: 16,
      fontWeight: '500',
      color: colors.text,
      marginBottom: description ? 2 : 0,
    },
    description: {
      fontSize: 14,
      color: colors.textSecondary,
      lineHeight: 18,
    },
    switchContainer: {
      width: sizeConfig.width,
      height: sizeConfig.height,
      borderRadius: sizeConfig.borderRadius,
      justifyContent: 'center',
      shadowColor: colors.text,
      shadowOffset: { width: 0, height: 2 },
      shadowOpacity: 0.1,
      shadowRadius: 2,
      elevation: 2,
    },
    track: {
      width: sizeConfig.width,
      height: sizeConfig.height,
      borderRadius: sizeConfig.borderRadius,
      position: 'absolute',
    },
    thumb: {
      width: sizeConfig.thumbSize,
      height: sizeConfig.thumbSize,
      borderRadius: sizeConfig.thumbSize / 2,
      backgroundColor: value ? colors.thumbOn : colors.thumbOff,
      position: 'absolute',
      shadowColor: '#000000',
      shadowOffset: { width: 0, height: 2 },
      shadowOpacity: 0.2,
      shadowRadius: 3,
      elevation: 3,
    },
  });

  return (
    <View style={[styles.container, style]}>
      {(label || description) && (
        <View style={styles.labelContainer}>
          {label && <Text style={styles.label}>{label}</Text>}
          {description && <Text style={styles.description}>{description}</Text>}
        </View>
      )}
      
      <TouchableOpacity
        onPress={handlePress}
        disabled={disabled}
        activeOpacity={1}
      >
        <Animated.View 
          style={[
            styles.switchContainer,
            { transform: [{ scale: scaleValue }] }
          ]}
        >
          <Animated.View 
            style={[
              styles.track,
              { backgroundColor: trackColor }
            ]} 
          />
          <Animated.View 
            style={[
              styles.thumb,
              {
                transform: [
                  { translateX: thumbPosition },
                  { scale: thumbScale }
                ]
              }
            ]} 
          />
        </Animated.View>
      </TouchableOpacity>
    </View>
  );
};

export default Switch;