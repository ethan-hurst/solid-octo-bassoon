/**
 * Custom hook for offline functionality
 */
import { useEffect, useState, useCallback } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import NetInfo from '@react-native-community/netinfo';

import { offlineService } from '../services/offlineService';
import { apiClient } from '../services';
import { RootState } from '../store';
import { 
  setOnlineStatus, 
  setSyncInProgress, 
  removePendingAction,
  incrementRetryCount,
} from '../store/slices/offlineSlice';

interface UseOfflineReturn {
  isOnline: boolean;
  isSyncInProgress: boolean;
  pendingActionsCount: number;
  cachedData: any;
  syncPendingActions: () => Promise<void>;
  storeOfflineAction: (type: string, payload: any) => Promise<void>;
  getCachedValueBets: () => Promise<any[]>;
  getCachedLiveGames: () => Promise<any[]>;
  clearOfflineData: () => Promise<void>;
  getStorageStats: () => Promise<any>;
}

export const useOffline = (): UseOfflineReturn => {
  const dispatch = useDispatch();
  const { 
    isOnline, 
    pendingActions, 
    syncInProgress, 
    cachedData 
  } = useSelector((state: RootState) => state.offline);

  const [isInitialized, setIsInitialized] = useState(false);

  // Initialize offline service
  useEffect(() => {
    const initializeOfflineService = async () => {
      try {
        await offlineService.initialize();
        setIsInitialized(true);
        console.log('Offline service initialized');
      } catch (error) {
        console.error('Failed to initialize offline service:', error);
      }
    };

    initializeOfflineService();
  }, []);

  // Monitor network connectivity
  useEffect(() => {
    const unsubscribe = NetInfo.addEventListener(state => {
      const online = state.isConnected && state.isInternetReachable;
      dispatch(setOnlineStatus(online || false));
      
      console.log('Network status changed:', {
        isConnected: state.isConnected,
        isInternetReachable: state.isInternetReachable,
        type: state.type,
      });

      // Auto-sync when coming back online
      if (online && pendingActions.length > 0 && !syncInProgress) {
        syncPendingActions();
      }
    });

    return unsubscribe;
  }, [pendingActions.length, syncInProgress]);

  // Sync pending actions with server
  const syncPendingActions = useCallback(async () => {
    if (!isInitialized || syncInProgress || !isOnline) {
      return;
    }

    try {
      dispatch(setSyncInProgress(true));
      
      const pendingActions = await offlineService.getPendingActions();
      console.log(`Syncing ${pendingActions.length} pending actions`);

      for (const action of pendingActions) {
        try {
          await processAction(action);
          await offlineService.removePendingAction(action.id);
          dispatch(removePendingAction(action.id));
          
          console.log(`Synced action: ${action.type}`);
        } catch (error: any) {
          console.error(`Failed to sync action ${action.type}:`, error);
          
          // Increment retry count
          await offlineService.incrementRetryCount(action.id);
          dispatch(incrementRetryCount(action.id));
          
          // Remove action if too many retries
          if (action.retry_count >= 3) {
            console.log(`Removing action after ${action.retry_count} retries: ${action.type}`);
            await offlineService.removePendingAction(action.id);
            dispatch(removePendingAction(action.id));
          }
        }
      }

      // Sync analytics events
      await syncAnalyticsEvents();
      
    } catch (error) {
      console.error('Error syncing pending actions:', error);
    } finally {
      dispatch(setSyncInProgress(false));
    }
  }, [isInitialized, syncInProgress, isOnline, dispatch]);

  // Process individual action
  const processAction = async (action: any) => {
    const { type, payload } = action;

    switch (type) {
      case 'add_to_betslip':
        await apiClient.quickAddToBetslip(
          payload.betId, 
          payload.action, 
          payload.sourceScreen
        );
        break;
        
      case 'user_preference_update':
        await apiClient.put('/user/preferences', payload);
        break;
        
      case 'notification_settings_update':
        await apiClient.put('/user/notification-settings', payload);
        break;
        
      case 'bet_interaction':
        await apiClient.post('/analytics/bet-interaction', payload);
        break;
        
      case 'screen_view':
        await apiClient.post('/analytics/screen-view', payload);
        break;
        
      default:
        console.warn(`Unknown action type: ${type}`);
    }
  };

  // Sync analytics events
  const syncAnalyticsEvents = async () => {
    try {
      const events = await offlineService.getUnsyncedAnalyticsEvents();
      if (events.length === 0) return;

      console.log(`Syncing ${events.length} analytics events`);
      
      // Send events in batches
      const batchSize = 50;
      for (let i = 0; i < events.length; i += batchSize) {
        const batch = events.slice(i, i + batchSize);
        
        try {
          await apiClient.post('/analytics/events/batch', { events: batch });
          
          // Mark as synced
          const eventIds = batch.map(event => event.id);
          await offlineService.markAnalyticsEventsSynced(eventIds);
          
          console.log(`Synced ${batch.length} analytics events`);
        } catch (error) {
          console.error('Failed to sync analytics batch:', error);
          break; // Stop syncing if batch fails
        }
      }
    } catch (error) {
      console.error('Error syncing analytics events:', error);
    }
  };

  // Store action for later sync
  const storeOfflineAction = useCallback(async (type: string, payload: any) => {
    if (!isInitialized) {
      console.warn('Offline service not initialized, cannot store action');
      return;
    }

    try {
      await offlineService.addPendingAction(type, payload);
      console.log(`Stored offline action: ${type}`);
    } catch (error) {
      console.error('Error storing offline action:', error);
    }
  }, [isInitialized]);

  // Get cached value bets
  const getCachedValueBets = useCallback(async () => {
    if (!isInitialized) return [];
    
    try {
      return await offlineService.getCachedValueBets();
    } catch (error) {
      console.error('Error getting cached value bets:', error);
      return [];
    }
  }, [isInitialized]);

  // Get cached live games
  const getCachedLiveGames = useCallback(async () => {
    if (!isInitialized) return [];
    
    try {
      return await offlineService.getCachedLiveGames();
    } catch (error) {
      console.error('Error getting cached live games:', error);
      return [];
    }
  }, [isInitialized]);

  // Clear offline data
  const clearOfflineData = useCallback(async () => {
    if (!isInitialized) return;
    
    try {
      await offlineService.clearAllData();
      console.log('Offline data cleared');
    } catch (error) {
      console.error('Error clearing offline data:', error);
    }
  }, [isInitialized]);

  // Get storage statistics
  const getStorageStats = useCallback(async () => {
    if (!isInitialized) return {};
    
    try {
      return await offlineService.getStorageStats();
    } catch (error) {
      console.error('Error getting storage stats:', error);
      return {};
    }
  }, [isInitialized]);

  return {
    isOnline,
    isSyncInProgress: syncInProgress,
    pendingActionsCount: pendingActions.length,
    cachedData,
    syncPendingActions,
    storeOfflineAction,
    getCachedValueBets,
    getCachedLiveGames,
    clearOfflineData,
    getStorageStats,
  };
};

/**
 * Hook for offline-aware data fetching
 */
export const useOfflineData = <T>(
  fetchFunction: () => Promise<T>,
  cacheKey: string,
  fallbackData: T
) => {
  const [data, setData] = useState<T>(fallbackData);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  const { isOnline, getCachedValueBets, getCachedLiveGames } = useOffline();

  const fetchData = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);

      if (isOnline) {
        // Fetch from network
        const result = await fetchFunction();
        setData(result);
        
        // Cache the result
        if (cacheKey === 'valueBets' && Array.isArray(result)) {
          await offlineService.storeValueBets(result as any);
        } else if (cacheKey === 'liveGames' && Array.isArray(result)) {
          await offlineService.storeLiveGames(result as any);
        }
      } else {
        // Load from cache
        let cachedData: T;
        if (cacheKey === 'valueBets') {
          cachedData = (await getCachedValueBets()) as T;
        } else if (cacheKey === 'liveGames') {
          cachedData = (await getCachedLiveGames()) as T;
        } else {
          cachedData = fallbackData;
        }
        
        setData(cachedData);
      }
    } catch (err: any) {
      console.error(`Error fetching ${cacheKey}:`, err);
      setError(err.message || 'Failed to fetch data');
      
      // Try to load cached data on error
      if (!isOnline) {
        try {
          let cachedData: T;
          if (cacheKey === 'valueBets') {
            cachedData = (await getCachedValueBets()) as T;
          } else if (cacheKey === 'liveGames') {
            cachedData = (await getCachedLiveGames()) as T;
          } else {
            cachedData = fallbackData;
          }
          setData(cachedData);
        } catch (cacheError) {
          console.error('Error loading cached data:', cacheError);
        }
      }
    } finally {
      setIsLoading(false);
    }
  }, [fetchFunction, cacheKey, isOnline, fallbackData, getCachedValueBets, getCachedLiveGames]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return {
    data,
    isLoading,
    error,
    refetch: fetchData,
    isOffline: !isOnline,
  };
};

/**
 * Hook for offline analytics tracking
 */
export const useOfflineAnalytics = () => {
  const { storeOfflineAction } = useOffline();

  const trackEvent = useCallback(async (eventType: string, data: any) => {
    try {
      await offlineService.storeAnalyticsEvent(eventType, {
        ...data,
        timestamp: Date.now(),
        session_id: await offlineService.getUserData('session_id'),
      });
    } catch (error) {
      console.error('Error tracking analytics event:', error);
    }
  }, []);

  const trackScreenView = useCallback(async (screenName: string, params?: any) => {
    await trackEvent('screen_view', {
      screen_name: screenName,
      params: params || {},
    });
  }, [trackEvent]);

  const trackBetInteraction = useCallback(async (
    betId: string, 
    action: string, 
    source: string
  ) => {
    await trackEvent('bet_interaction', {
      bet_id: betId,
      action,
      source,
    });
  }, [trackEvent]);

  const trackUserAction = useCallback(async (action: string, data?: any) => {
    await trackEvent('user_action', {
      action,
      data: data || {},
    });
  }, [trackEvent]);

  return {
    trackEvent,
    trackScreenView,
    trackBetInteraction,
    trackUserAction,
  };
};