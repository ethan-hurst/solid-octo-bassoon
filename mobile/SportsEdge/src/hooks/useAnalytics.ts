/**
 * Custom hooks for analytics functionality
 */
import { useEffect, useCallback, useRef } from 'react';
import { useNavigation, useRoute } from '@react-navigation/native';
import { AppState, AppStateStatus } from 'react-native';

import { analyticsService } from '../services/analyticsService';

/**
 * Hook for basic analytics functionality
 */
export const useAnalytics = () => {
  const trackEvent = useCallback(async (eventType: string, properties?: Record<string, any>) => {
    await analyticsService.trackEvent(eventType, properties);
  }, []);

  const trackScreenView = useCallback(async (screenName: string, params?: Record<string, any>) => {
    await analyticsService.trackScreenView(screenName, params);
  }, []);

  const trackInteraction = useCallback(async (
    elementType: string,
    elementId: string,
    action: string,
    context?: Record<string, any>
  ) => {
    await analyticsService.trackInteraction(elementType, elementId, action, context);
  }, []);

  const trackBetEvent = useCallback(async (eventType: string, betData: Record<string, any>) => {
    await analyticsService.trackBetEvent(eventType, betData);
  }, []);

  const trackPerformance = useCallback(async (
    metricName: string,
    value: number,
    context?: Record<string, any>
  ) => {
    await analyticsService.trackPerformance(metricName, value, context);
  }, []);

  const trackError = useCallback(async (error: Error, context?: Record<string, any>) => {
    await analyticsService.trackError(error, context);
  }, []);

  const setUserProperties = useCallback(async (properties: Record<string, any>) => {
    await analyticsService.setUserProperties(properties);
  }, []);

  return {
    trackEvent,
    trackScreenView,
    trackInteraction,
    trackBetEvent,
    trackPerformance,
    trackError,
    setUserProperties,
  };
};

/**
 * Hook for automatic screen view tracking
 */
export const useScreenAnalytics = (screenName?: string, params?: Record<string, any>) => {
  const navigation = useNavigation();
  const route = useRoute();
  const { trackScreenView } = useAnalytics();
  
  const finalScreenName = screenName || route.name;
  const finalParams = params || route.params;

  useEffect(() => {
    trackScreenView(finalScreenName, finalParams as Record<string, any>);
  }, [finalScreenName, finalParams, trackScreenView]);

  useEffect(() => {
    const unsubscribe = navigation.addListener('focus', () => {
      trackScreenView(finalScreenName, finalParams as Record<string, any>);
    });

    return unsubscribe;
  }, [navigation, finalScreenName, finalParams, trackScreenView]);
};

/**
 * Hook for tracking user interactions with components
 */
export const useInteractionAnalytics = (elementType: string, elementId: string) => {
  const { trackInteraction } = useAnalytics();

  const trackPress = useCallback((context?: Record<string, any>) => {
    trackInteraction(elementType, elementId, 'press', context);
  }, [elementType, elementId, trackInteraction]);

  const trackLongPress = useCallback((context?: Record<string, any>) => {
    trackInteraction(elementType, elementId, 'long_press', context);
  }, [elementType, elementId, trackInteraction]);

  const trackSwipe = useCallback((direction: string, context?: Record<string, any>) => {
    trackInteraction(elementType, elementId, 'swipe', { direction, ...context });
  }, [elementType, elementId, trackInteraction]);

  const trackScroll = useCallback((context?: Record<string, any>) => {
    trackInteraction(elementType, elementId, 'scroll', context);
  }, [elementType, elementId, trackInteraction]);

  const trackCustomAction = useCallback((action: string, context?: Record<string, any>) => {
    trackInteraction(elementType, elementId, action, context);
  }, [elementType, elementId, trackInteraction]);

  return {
    trackPress,
    trackLongPress,
    trackSwipe,
    trackScroll,
    trackCustomAction,
  };
};

/**
 * Hook for betting-specific analytics
 */
export const useBettingAnalytics = () => {
  const { trackBetEvent } = useAnalytics();

  const trackBetView = useCallback((betData: Record<string, any>) => {
    trackBetEvent('view', betData);
  }, [trackBetEvent]);

  const trackBetAnalysis = useCallback((betData: Record<string, any>, analysisData?: Record<string, any>) => {
    trackBetEvent('analysis', { ...betData, analysis: analysisData });
  }, [trackBetEvent]);

  const trackBetAdd = useCallback((betData: Record<string, any>, source: string) => {
    trackBetEvent('add_to_betslip', { ...betData, source });
  }, [trackBetEvent]);

  const trackBetPlace = useCallback((betData: Record<string, any>) => {
    trackBetEvent('place', betData);
  }, [trackBetEvent]);

  const trackBetShare = useCallback((betData: Record<string, any>, platform: string) => {
    trackBetEvent('share', { ...betData, platform });
  }, [trackBetEvent]);

  const trackBetResult = useCallback((betData: Record<string, any>, result: 'won' | 'lost' | 'void') => {
    trackBetEvent('result', { ...betData, result });
  }, [trackBetEvent]);

  return {
    trackBetView,
    trackBetAnalysis,
    trackBetAdd,
    trackBetPlace,
    trackBetShare,
    trackBetResult,
  };
};

/**
 * Hook for performance monitoring
 */
export const usePerformanceAnalytics = () => {
  const { trackPerformance } = useAnalytics();

  const trackApiCall = useCallback((endpoint: string, duration: number, success: boolean) => {
    trackPerformance('api_call', duration, {
      endpoint,
      success,
      status: success ? 'success' : 'error',
    });
  }, [trackPerformance]);

  const trackScreenLoad = useCallback((screenName: string, duration: number) => {
    trackPerformance('screen_load', duration, { screen_name: screenName });
  }, [trackPerformance]);

  const trackImageLoad = useCallback((imageUrl: string, duration: number, success: boolean) => {
    trackPerformance('image_load', duration, {
      image_url: imageUrl,
      success,
    });
  }, [trackPerformance]);

  const trackCustomMetric = useCallback((metricName: string, value: number, context?: Record<string, any>) => {
    trackPerformance(metricName, value, context);
  }, [trackPerformance]);

  return {
    trackApiCall,
    trackScreenLoad,
    trackImageLoad,
    trackCustomMetric,
  };
};

/**
 * Hook for session and app lifecycle analytics
 */
export const useSessionAnalytics = () => {
  const { trackEvent } = useAnalytics();
  const appStateRef = useRef(AppState.currentState);

  useEffect(() => {
    const handleAppStateChange = (nextAppState: AppStateStatus) => {
      if (
        appStateRef.current.match(/inactive|background/) &&
        nextAppState === 'active'
      ) {
        trackEvent('app_foreground', {
          previous_state: appStateRef.current,
        });
      } else if (
        appStateRef.current === 'active' &&
        nextAppState.match(/inactive|background/)
      ) {
        trackEvent('app_background', {
          next_state: nextAppState,
        });
      }

      appStateRef.current = nextAppState;
    };

    const subscription = AppState.addEventListener('change', handleAppStateChange);
    return () => subscription?.remove();
  }, [trackEvent]);

  return {
    trackSessionStart: useCallback(() => trackEvent('session_start'), [trackEvent]),
    trackSessionEnd: useCallback(() => trackEvent('session_end'), [trackEvent]),
    trackAppCrash: useCallback((error: Error) => trackEvent('app_crash', {
      error_message: error.message,
      error_stack: error.stack,
    }), [trackEvent]),
  };
};

/**
 * Hook for measuring component render performance
 */
export const useRenderPerformance = (componentName: string) => {
  const { trackPerformance } = useAnalytics();
  const renderStartTime = useRef<number>(Date.now());

  useEffect(() => {
    renderStartTime.current = Date.now();
  });

  useEffect(() => {
    const renderDuration = Date.now() - renderStartTime.current;
    if (renderDuration > 16) { // Only track slow renders (>16ms)
      trackPerformance('component_render', renderDuration, {
        component_name: componentName,
      });
    }
  });

  const trackCustomRender = useCallback((action: string) => {
    const duration = Date.now() - renderStartTime.current;
    trackPerformance('component_action', duration, {
      component_name: componentName,
      action,
    });
  }, [componentName, trackPerformance]);

  return { trackCustomRender };
};

/**
 * Hook for A/B testing analytics
 */
export const useABTestAnalytics = () => {
  const { trackEvent } = useAnalytics();

  const trackExperimentView = useCallback((experimentName: string, variant: string) => {
    trackEvent('experiment_view', {
      experiment_name: experimentName,
      variant,
    });
  }, [trackEvent]);

  const trackExperimentConversion = useCallback((
    experimentName: string,
    variant: string,
    conversionType: string,
    value?: number
  ) => {
    trackEvent('experiment_conversion', {
      experiment_name: experimentName,
      variant,
      conversion_type: conversionType,
      value,
    });
  }, [trackEvent]);

  return {
    trackExperimentView,
    trackExperimentConversion,
  };
};

/**
 * Hook for error boundary analytics
 */
export const useErrorAnalytics = () => {
  const { trackError } = useAnalytics();

  const trackComponentError = useCallback((
    error: Error,
    errorInfo: { componentStack: string },
    componentName?: string
  ) => {
    trackError(error, {
      component_stack: errorInfo.componentStack,
      component_name: componentName,
      error_boundary: true,
    });
  }, [trackError]);

  const trackJSError = useCallback((error: Error, source?: string) => {
    trackError(error, {
      source,
      error_type: 'javascript',
    });
  }, [trackError]);

  const trackNetworkError = useCallback((error: Error, url?: string, method?: string) => {
    trackError(error, {
      url,
      method,
      error_type: 'network',
    });
  }, [trackError]);

  return {
    trackComponentError,
    trackJSError,
    trackNetworkError,
  };
};