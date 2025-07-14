/**
 * Modal Component - Mobile-optimized overlay modal
 */
import React, { useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Animated,
  BackHandler,
  Platform,
  StatusBar,
  Dimensions,
} from 'react-native';
import { useSelector } from 'react-redux';
import Icon from 'react-native-vector-icons/Ionicons';

import { RootState } from '../store';

interface ModalProps {
  visible: boolean;
  onClose: () => void;
  title?: string;
  children: React.ReactNode;
  size?: 'small' | 'medium' | 'large' | 'fullscreen';
  position?: 'center' | 'bottom' | 'top';
  showCloseButton?: boolean;
  closeOnBackdrop?: boolean;
  animationType?: 'fade' | 'slide' | 'scale';
  statusBarTranslucent?: boolean;
}

const Modal: React.FC<ModalProps> = ({
  visible,
  onClose,
  title,
  children,
  size = 'medium',
  position = 'center',
  showCloseButton = true,
  closeOnBackdrop = true,
  animationType = 'fade',
  statusBarTranslucent = false,
}) => {
  const theme = useSelector((state: RootState) => state.userPreferences.theme);
  const backdropOpacity = React.useRef(new Animated.Value(0)).current;
  const modalScale = React.useRef(new Animated.Value(0.8)).current;
  const modalTranslateY = React.useRef(new Animated.Value(50)).current;

  const { width: screenWidth, height: screenHeight } = Dimensions.get('window');

  const isDark = theme.theme === 'dark' || 
    (theme.theme === 'auto' && new Date().getHours() > 18);

  const colors = {
    background: isDark ? '#1E293B' : '#FFFFFF',
    text: isDark ? '#F1F5F9' : '#1E293B',
    textSecondary: isDark ? '#94A3B8' : '#64748B',
    border: isDark ? '#475569' : '#E2E8F0',
    backdrop: 'rgba(0, 0, 0, 0.5)',
    accent: theme.accentColor,
  };

  const getSizeConfig = () => {
    switch (size) {
      case 'small':
        return {
          width: Math.min(screenWidth * 0.8, 320),
          maxHeight: screenHeight * 0.4,
        };
      case 'large':
        return {
          width: Math.min(screenWidth * 0.95, 600),
          maxHeight: screenHeight * 0.8,
        };
      case 'fullscreen':
        return {
          width: screenWidth,
          height: screenHeight,
        };
      case 'medium':
      default:
        return {
          width: Math.min(screenWidth * 0.9, 400),
          maxHeight: screenHeight * 0.6,
        };
    }
  };

  const getPositionStyles = () => {
    const sizeConfig = getSizeConfig();
    
    if (size === 'fullscreen') {
      return {
        position: 'absolute' as const,
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
      };
    }

    switch (position) {
      case 'bottom':
        return {
          position: 'absolute' as const,
          bottom: 0,
          left: 0,
          right: 0,
          borderTopLeftRadius: 20,
          borderTopRightRadius: 20,
          borderBottomLeftRadius: 0,
          borderBottomRightRadius: 0,
        };
      case 'top':
        return {
          position: 'absolute' as const,
          top: statusBarTranslucent ? 0 : StatusBar.currentHeight || 44,
          left: (screenWidth - sizeConfig.width) / 2,
          borderTopLeftRadius: 0,
          borderTopRightRadius: 0,
          borderBottomLeftRadius: 20,
          borderBottomRightRadius: 20,
        };
      case 'center':
      default:
        return {
          alignSelf: 'center' as const,
          borderRadius: 16,
        };
    }
  };

  const styles = StyleSheet.create({
    overlay: {
      position: 'absolute',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      backgroundColor: colors.backdrop,
      justifyContent: position === 'center' ? 'center' : 'flex-end',
      alignItems: position === 'center' ? 'center' : 'stretch',
      zIndex: 1000,
    },
    modal: {
      backgroundColor: colors.background,
      ...getSizeConfig(),
      ...getPositionStyles(),
      shadowColor: '#000000',
      shadowOffset: { width: 0, height: 8 },
      shadowOpacity: 0.3,
      shadowRadius: 16,
      elevation: 16,
    },
    header: {
      flexDirection: 'row',
      alignItems: 'center',
      justifyContent: 'space-between',
      paddingHorizontal: 20,
      paddingVertical: 16,
      borderBottomWidth: 1,
      borderBottomColor: colors.border,
    },
    title: {
      fontSize: 18,
      fontWeight: '600',
      color: colors.text,
      flex: 1,
    },
    closeButton: {
      padding: 4,
      marginLeft: 16,
    },
    content: {
      flex: 1,
      padding: 20,
    },
    contentFullscreen: {
      flex: 1,
      paddingTop: statusBarTranslucent ? (StatusBar.currentHeight || 44) + 20 : 20,
      paddingHorizontal: 20,
      paddingBottom: 20,
    },
  });

  useEffect(() => {
    if (visible) {
      // Animate in
      Animated.parallel([
        Animated.timing(backdropOpacity, {
          toValue: 1,
          duration: 200,
          useNativeDriver: true,
        }),
        animationType === 'scale' ? 
          Animated.spring(modalScale, {
            toValue: 1,
            tension: 300,
            friction: 20,
            useNativeDriver: true,
          }) :
          Animated.timing(modalTranslateY, {
            toValue: 0,
            duration: 250,
            useNativeDriver: true,
          }),
      ]).start();
    } else {
      // Animate out
      Animated.parallel([
        Animated.timing(backdropOpacity, {
          toValue: 0,
          duration: 150,
          useNativeDriver: true,
        }),
        animationType === 'scale' ?
          Animated.timing(modalScale, {
            toValue: 0.8,
            duration: 150,
            useNativeDriver: true,
          }) :
          Animated.timing(modalTranslateY, {
            toValue: 50,
            duration: 150,
            useNativeDriver: true,
          }),
      ]).start();
    }
  }, [visible, backdropOpacity, modalScale, modalTranslateY, animationType]);

  useEffect(() => {
    const backHandler = BackHandler.addEventListener('hardwareBackPress', () => {
      if (visible) {
        onClose();
        return true;
      }
      return false;
    });

    return () => backHandler.remove();
  }, [visible, onClose]);

  if (!visible) return null;

  const getModalTransform = () => {
    if (animationType === 'scale') {
      return [{ scale: modalScale }];
    }
    return [{ translateY: modalTranslateY }];
  };

  const handleBackdropPress = () => {
    if (closeOnBackdrop) {
      onClose();
    }
  };

  return (
    <View style={styles.overlay}>
      <Animated.View 
        style={[StyleSheet.absoluteFill, { opacity: backdropOpacity }]}
      >
        <TouchableOpacity 
          style={StyleSheet.absoluteFill}
          onPress={handleBackdropPress}
          activeOpacity={1}
        />
      </Animated.View>
      
      <Animated.View 
        style={[
          styles.modal,
          {
            transform: getModalTransform(),
          },
        ]}
      >
        {(title || showCloseButton) && (
          <View style={styles.header}>
            {title && <Text style={styles.title}>{title}</Text>}
            {showCloseButton && (
              <TouchableOpacity 
                style={styles.closeButton}
                onPress={onClose}
              >
                <Icon 
                  name="close" 
                  size={24} 
                  color={colors.textSecondary} 
                />
              </TouchableOpacity>
            )}
          </View>
        )}
        
        <View style={size === 'fullscreen' ? styles.contentFullscreen : styles.content}>
          {children}
        </View>
      </Animated.View>
    </View>
  );
};

export default Modal;