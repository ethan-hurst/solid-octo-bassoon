/**
 * Loading Spinner Component - Mobile-optimized loading indicator
 */
import React from 'react';
import {
  View,
  ActivityIndicator,
  Text,
  StyleSheet,
  Animated,
} from 'react-native';
import { useSelector } from 'react-redux';

import { RootState } from '../store';

interface LoadingSpinnerProps {
  size?: 'small' | 'large';
  color?: string;
  text?: string;
  overlay?: boolean;
  visible?: boolean;
}

const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  size = 'large',
  color,
  text,
  overlay = false,
  visible = true,
}) => {
  const theme = useSelector((state: RootState) => state.userPreferences.theme);
  const fadeAnim = React.useRef(new Animated.Value(0)).current;

  const isDark = theme.theme === 'dark' || 
    (theme.theme === 'auto' && new Date().getHours() > 18);

  const colors = {
    background: isDark ? '#0F172A' : '#FFFFFF',
    text: isDark ? '#F1F5F9' : '#1E293B',
    accent: color || theme.accentColor,
    overlay: isDark ? 'rgba(15, 23, 42, 0.8)' : 'rgba(255, 255, 255, 0.8)',
  };

  const styles = StyleSheet.create({
    container: {
      justifyContent: 'center',
      alignItems: 'center',
      padding: 20,
    },
    overlayContainer: {
      position: 'absolute',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      justifyContent: 'center',
      alignItems: 'center',
      backgroundColor: colors.overlay,
      zIndex: 1000,
    },
    content: {
      backgroundColor: colors.background,
      borderRadius: 12,
      padding: 24,
      alignItems: 'center',
      shadowColor: colors.text,
      shadowOffset: { width: 0, height: 4 },
      shadowOpacity: 0.1,
      shadowRadius: 8,
      elevation: 8,
    },
    text: {
      fontSize: 16,
      color: colors.text,
      marginTop: 12,
      textAlign: 'center',
    },
  });

  React.useEffect(() => {
    if (visible) {
      Animated.timing(fadeAnim, {
        toValue: 1,
        duration: 200,
        useNativeDriver: true,
      }).start();
    } else {
      Animated.timing(fadeAnim, {
        toValue: 0,
        duration: 200,
        useNativeDriver: true,
      }).start();
    }
  }, [visible, fadeAnim]);

  if (!visible) return null;

  const content = (
    <View style={overlay ? styles.content : styles.container}>
      <ActivityIndicator size={size} color={colors.accent} />
      {text && <Text style={styles.text}>{text}</Text>}
    </View>
  );

  if (overlay) {
    return (
      <Animated.View style={[styles.overlayContainer, { opacity: fadeAnim }]}>
        {content}
      </Animated.View>
    );
  }

  return <Animated.View style={{ opacity: fadeAnim }}>{content}</Animated.View>;
};

export default LoadingSpinner;