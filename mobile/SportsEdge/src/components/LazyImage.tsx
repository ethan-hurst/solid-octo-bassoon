/**
 * Lazy Image Component - Optimized image loading with caching and placeholders
 */
import React, { useState, useCallback, useMemo } from 'react';
import {
  View,
  Image,
  ImageProps,
  StyleSheet,
  Animated,
  ImageSourcePropType,
} from 'react-native';
import { useSelector } from 'react-redux';

import { RootState } from '../store';
import { getOptimalImageSize } from '../utils/performance';
import LoadingSpinner from './LoadingSpinner';

interface LazyImageProps extends Omit<ImageProps, 'source'> {
  source: ImageSourcePropType;
  placeholder?: ImageSourcePropType;
  placeholderColor?: string;
  fadeInDuration?: number;
  cachePolicy?: 'memory' | 'disk' | 'reload';
  optimizeSize?: boolean;
  maxWidth?: number;
  maxHeight?: number;
  quality?: 'low' | 'medium' | 'high';
  onLoadStart?: () => void;
  onLoadEnd?: () => void;
  onError?: (error: any) => void;
  showLoadingIndicator?: boolean;
  retryCount?: number;
  retryDelay?: number;
  style?: any;
}

const LazyImage: React.FC<LazyImageProps> = ({
  source,
  placeholder,
  placeholderColor,
  fadeInDuration = 300,
  cachePolicy = 'memory',
  optimizeSize = true,
  maxWidth = 400,
  maxHeight = 400,
  quality = 'medium',
  onLoadStart,
  onLoadEnd,
  onError,
  showLoadingIndicator = true,
  retryCount = 2,
  retryDelay = 1000,
  style,
  ...props
}) => {
  const theme = useSelector((state: RootState) => state.userPreferences.theme);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [retries, setRetries] = useState(0);
  const fadeAnim = React.useRef(new Animated.Value(0)).current;

  const isDark = theme.theme === 'dark' || 
    (theme.theme === 'auto' && new Date().getHours() > 18);

  const colors = {
    placeholder: placeholderColor || (isDark ? '#475569' : '#E2E8F0'),
    background: isDark ? '#1E293B' : '#F8FAFC',
  };

  // Optimize image source based on quality and size
  const optimizedSource = useMemo(() => {
    if (typeof source === 'object' && source.uri && optimizeSize) {
      const uri = source.uri;
      
      // Add quality and size parameters if the image service supports them
      if (uri.includes('cloudinary.com') || uri.includes('imgix.com')) {
        const separator = uri.includes('?') ? '&' : '?';
        const qualityParam = quality === 'low' ? 'q_30' : quality === 'medium' ? 'q_70' : 'q_90';
        const sizeParam = `w_${maxWidth},h_${maxHeight},c_limit`;
        
        return {
          ...source,
          uri: `${uri}${separator}${qualityParam}&${sizeParam}`,
        };
      }
    }
    
    return source;
  }, [source, optimizeSize, quality, maxWidth, maxHeight]);

  // Handle image loading start
  const handleLoadStart = useCallback(() => {
    setLoading(true);
    setError(false);
    onLoadStart?.();
  }, [onLoadStart]);

  // Handle image loading success
  const handleLoadEnd = useCallback(() => {
    setLoading(false);
    
    // Fade in animation
    Animated.timing(fadeAnim, {
      toValue: 1,
      duration: fadeInDuration,
      useNativeDriver: true,
    }).start();
    
    onLoadEnd?.();
  }, [fadeAnim, fadeInDuration, onLoadEnd]);

  // Handle image loading error with retry logic
  const handleError = useCallback((errorEvent: any) => {
    setLoading(false);
    
    if (retries < retryCount) {
      setTimeout(() => {
        setRetries(prev => prev + 1);
        setError(false);
        setLoading(true);
      }, retryDelay);
    } else {
      setError(true);
      onError?.(errorEvent);
    }
  }, [retries, retryCount, retryDelay, onError]);

  // Get container style
  const containerStyle = useMemo(() => {
    const flattenedStyle = StyleSheet.flatten([style]) || {};
    
    return {
      ...flattenedStyle,
      backgroundColor: colors.background,
      overflow: 'hidden' as const,
    };
  }, [style, colors.background]);

  // Calculate optimal dimensions
  const dimensions = useMemo(() => {
    const flattenedStyle = StyleSheet.flatten([style]) || {};
    const styleWidth = flattenedStyle.width as number;
    const styleHeight = flattenedStyle.height as number;
    
    if (styleWidth && styleHeight && optimizeSize) {
      return getOptimalImageSize(
        styleWidth,
        styleHeight,
        maxWidth,
        maxHeight
      );
    }
    
    return null;
  }, [style, optimizeSize, maxWidth, maxHeight]);

  const styles = StyleSheet.create({
    container: {
      position: 'relative',
      ...containerStyle,
    },
    image: {
      width: '100%',
      height: '100%',
      ...dimensions,
    },
    placeholder: {
      position: 'absolute',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      backgroundColor: colors.placeholder,
      justifyContent: 'center',
      alignItems: 'center',
    },
    loadingContainer: {
      position: 'absolute',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      justifyContent: 'center',
      alignItems: 'center',
      backgroundColor: 'rgba(0, 0, 0, 0.1)',
    },
    errorContainer: {
      position: 'absolute',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      justifyContent: 'center',
      alignItems: 'center',
      backgroundColor: colors.placeholder,
    },
  });

  return (
    <View style={styles.container}>
      {/* Placeholder */}
      {placeholder && (
        <View style={styles.placeholder}>
          <Image
            source={placeholder}
            style={styles.image}
            resizeMode="cover"
          />
        </View>
      )}
      
      {/* Main Image */}
      {!error && (
        <Animated.View style={{ opacity: fadeAnim }}>
          <Image
            {...props}
            source={optimizedSource}
            style={styles.image}
            onLoadStart={handleLoadStart}
            onLoadEnd={handleLoadEnd}
            onError={handleError}
            resizeMode="cover"
          />
        </Animated.View>
      )}
      
      {/* Loading Indicator */}
      {loading && showLoadingIndicator && (
        <View style={styles.loadingContainer}>
          <LoadingSpinner
            size="small"
            visible={true}
          />
        </View>
      )}
      
      {/* Error State */}
      {error && (
        <View style={styles.errorContainer}>
          {/* You could add an error icon here */}
        </View>
      )}
    </View>
  );
};

export default React.memo(LazyImage);