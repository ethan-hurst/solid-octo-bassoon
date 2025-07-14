/**
 * Swipeable Card Component - Core swipe interaction for bet discovery
 */
import React, { useRef, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Animated,
  PanGestureHandler,
  State,
  Dimensions,
} from 'react-native';
import { useSelector } from 'react-redux';
import Icon from 'react-native-vector-icons/Ionicons';

import { RootState } from '../store';

const { width: SCREEN_WIDTH } = Dimensions.get('window');
const SWIPE_THRESHOLD = SCREEN_WIDTH * 0.25;
const ROTATION_FACTOR = 0.1;

export interface SwipeAction {
  id: string;
  label: string;
  icon: string;
  color: string;
  backgroundColor: string;
}

interface SwipeableCardProps {
  children: React.ReactNode;
  onSwipeLeft?: (cardId: string) => void;
  onSwipeRight?: (cardId: string) => void;
  onSwipeUp?: (cardId: string) => void;
  leftAction?: SwipeAction;
  rightAction?: SwipeAction;
  upAction?: SwipeAction;
  cardId: string;
  disabled?: boolean;
}

const SwipeableCard: React.FC<SwipeableCardProps> = ({
  children,
  onSwipeLeft,
  onSwipeRight,
  onSwipeUp,
  leftAction,
  rightAction,
  upAction,
  cardId,
  disabled = false,
}) => {
  const theme = useSelector((state: RootState) => state.userPreferences.theme);
  
  const translateX = useRef(new Animated.Value(0)).current;
  const translateY = useRef(new Animated.Value(0)).current;
  const rotate = useRef(new Animated.Value(0)).current;
  const scale = useRef(new Animated.Value(1)).current;

  const [isActive, setIsActive] = useState(false);
  const [swipeDirection, setSwipeDirection] = useState<'left' | 'right' | 'up' | null>(null);

  const isDark = theme.theme === 'dark' || 
    (theme.theme === 'auto' && new Date().getHours() > 18);

  const colors = {
    background: isDark ? '#1E293B' : '#FFFFFF',
    surface: isDark ? '#334155' : '#F8FAFC',
    text: isDark ? '#F1F5F9' : '#1E293B',
    border: isDark ? '#475569' : '#E2E8F0',
    shadow: isDark ? 'rgba(0,0,0,0.3)' : 'rgba(0,0,0,0.1)',
  };

  const styles = StyleSheet.create({
    container: {
      position: 'relative',
    },
    card: {
      backgroundColor: colors.background,
      borderRadius: 16,
      borderWidth: 1,
      borderColor: colors.border,
      shadowColor: colors.shadow,
      shadowOffset: { width: 0, height: 4 },
      shadowOpacity: 0.15,
      shadowRadius: 8,
      elevation: 5,
    },
    activeCard: {
      shadowOpacity: 0.25,
      shadowRadius: 12,
      elevation: 8,
    },
    overlayContainer: {
      position: 'absolute',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      justifyContent: 'center',
      alignItems: 'center',
      borderRadius: 16,
    },
    overlay: {
      backgroundColor: 'rgba(0,0,0,0.7)',
      paddingHorizontal: 20,
      paddingVertical: 12,
      borderRadius: 12,
      flexDirection: 'row',
      alignItems: 'center',
    },
    overlayText: {
      color: '#FFFFFF',
      fontSize: 18,
      fontWeight: 'bold',
      marginLeft: 8,
      textTransform: 'uppercase',
    },
    actionIndicator: {
      position: 'absolute',
      top: 20,
      paddingHorizontal: 16,
      paddingVertical: 8,
      borderRadius: 20,
      flexDirection: 'row',
      alignItems: 'center',
    },
    leftIndicator: {
      left: 20,
    },
    rightIndicator: {
      right: 20,
    },
    upIndicator: {
      top: 20,
      left: '50%',
      transform: [{ translateX: -50 }],
    },
    indicatorText: {
      fontSize: 14,
      fontWeight: '600',
      marginLeft: 6,
    },
  });

  const onGestureEvent = Animated.event(
    [
      {
        nativeEvent: {
          translationX: translateX,
          translationY: translateY,
        },
      },
    ],
    { useNativeDriver: false }
  );

  const onHandlerStateChange = (event: any) => {
    if (disabled) return;

    const { state, translationX: tx, translationY: ty } = event.nativeEvent;

    if (state === State.BEGAN) {
      setIsActive(true);
    } else if (state === State.ACTIVE) {
      // Update rotation based on horizontal movement
      const rotation = tx * ROTATION_FACTOR;
      rotate.setValue(rotation);

      // Determine swipe direction for visual feedback
      const absX = Math.abs(tx);
      const absY = Math.abs(ty);

      if (absY > absX && ty < -SWIPE_THRESHOLD / 2 && upAction) {
        setSwipeDirection('up');
      } else if (absX > absY) {
        if (tx > SWIPE_THRESHOLD / 2 && rightAction) {
          setSwipeDirection('right');
        } else if (tx < -SWIPE_THRESHOLD / 2 && leftAction) {
          setSwipeDirection('left');
        } else {
          setSwipeDirection(null);
        }
      } else {
        setSwipeDirection(null);
      }

      // Scale effect for up swipe
      if (swipeDirection === 'up') {
        const scaleValue = 1 + Math.abs(ty) / (SCREEN_WIDTH * 2);
        scale.setValue(Math.min(scaleValue, 1.1));
      } else {
        scale.setValue(1);
      }
    } else if (state === State.END || state === State.CANCELLED) {
      setIsActive(false);
      setSwipeDirection(null);

      const absX = Math.abs(tx);
      const absY = Math.abs(ty);

      // Determine if swipe threshold was met
      let shouldSwipe = false;
      let swipeAction: (() => void) | undefined;

      if (absY > absX && ty < -SWIPE_THRESHOLD && upAction && onSwipeUp) {
        shouldSwipe = true;
        swipeAction = () => onSwipeUp(cardId);
      } else if (absX > absY) {
        if (tx > SWIPE_THRESHOLD && rightAction && onSwipeRight) {
          shouldSwipe = true;
          swipeAction = () => onSwipeRight(cardId);
        } else if (tx < -SWIPE_THRESHOLD && leftAction && onSwipeLeft) {
          shouldSwipe = true;
          swipeAction = () => onSwipeLeft(cardId);
        }
      }

      if (shouldSwipe && swipeAction) {
        // Animate off screen
        const toX = tx > 0 ? SCREEN_WIDTH : -SCREEN_WIDTH;
        const toY = ty < 0 ? -SCREEN_WIDTH : 0;

        Animated.parallel([
          Animated.timing(translateX, {
            toValue: absY > absX ? 0 : toX,
            duration: 300,
            useNativeDriver: false,
          }),
          Animated.timing(translateY, {
            toValue: absY > absX ? toY : 0,
            duration: 300,
            useNativeDriver: false,
          }),
          Animated.timing(rotate, {
            toValue: tx * ROTATION_FACTOR * 2,
            duration: 300,
            useNativeDriver: false,
          }),
          Animated.timing(scale, {
            toValue: 0.8,
            duration: 300,
            useNativeDriver: false,
          }),
        ]).start(() => {
          swipeAction?.();
          // Reset transforms
          translateX.setValue(0);
          translateY.setValue(0);
          rotate.setValue(0);
          scale.setValue(1);
        });
      } else {
        // Spring back to center
        Animated.parallel([
          Animated.spring(translateX, {
            toValue: 0,
            useNativeDriver: false,
            tension: 100,
            friction: 8,
          }),
          Animated.spring(translateY, {
            toValue: 0,
            useNativeDriver: false,
            tension: 100,
            friction: 8,
          }),
          Animated.spring(rotate, {
            toValue: 0,
            useNativeDriver: false,
            tension: 100,
            friction: 8,
          }),
          Animated.spring(scale, {
            toValue: 1,
            useNativeDriver: false,
            tension: 100,
            friction: 8,
          }),
        ]).start();
      }
    }
  };

  const cardStyle = {
    transform: [
      { translateX },
      { translateY },
      { rotate: rotate.interpolate({
        inputRange: [-1, 1],
        outputRange: ['-1deg', '1deg'],
      }) },
      { scale },
    ],
  };

  const renderActionIndicator = (action: SwipeAction, position: 'left' | 'right' | 'up') => {
    if (!action || swipeDirection !== position) return null;

    return (
      <View style={[
        styles.actionIndicator,
        { backgroundColor: action.backgroundColor },
        position === 'left' && styles.leftIndicator,
        position === 'right' && styles.rightIndicator,
        position === 'up' && styles.upIndicator,
      ]}>
        <Icon name={action.icon} size={20} color={action.color} />
        <Text style={[styles.indicatorText, { color: action.color }]}>
          {action.label}
        </Text>
      </View>
    );
  };

  return (
    <View style={styles.container}>
      <PanGestureHandler
        onGestureEvent={onGestureEvent}
        onHandlerStateChange={onHandlerStateChange}
        enabled={!disabled}
      >
        <Animated.View
          style={[
            styles.card,
            isActive && styles.activeCard,
            cardStyle,
          ]}
        >
          {children}
          
          {/* Action indicators */}
          {renderActionIndicator(leftAction!, 'left')}
          {renderActionIndicator(rightAction!, 'right')}
          {renderActionIndicator(upAction!, 'up')}
        </Animated.View>
      </PanGestureHandler>
    </View>
  );
};

export default SwipeableCard;