/**
 * Custom hooks exports
 */
export {
  useWebSocket,
  useWebSocketEvent,
  useWebSocketRoom,
  useValueBetsWebSocket,
  useLiveGamesWebSocket,
  useSocialWebSocket,
} from './useWebSocket';

export {
  useNotifications,
  useNotificationPreferences,
  useNotificationAnalytics,
} from './useNotifications';

export {
  useOffline,
  useOfflineData,
  useOfflineAnalytics,
} from './useOffline';

export {
  useAnalytics,
  useScreenAnalytics,
  useInteractionAnalytics,
  useBettingAnalytics,
  usePerformanceAnalytics,
  useSessionAnalytics,
  useRenderPerformance,
  useABTestAnalytics,
  useErrorAnalytics,
} from './useAnalytics';

export {
  usePerformanceTracking,
  useMemoryWarning,
  useAppStatePerformance,
  useOptimizedCallback,
  useInteractionManager,
  useRenderOptimization,
  useLazyLoading,
  useImagePreloader,
  useMemoryOptimization,
  useBatchedUpdates,
} from './usePerformance';