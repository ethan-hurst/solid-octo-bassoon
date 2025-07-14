/**
 * Custom hook for notification functionality
 */
import { useEffect, useState, useCallback } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { AppState, AppStateStatus } from 'react-native';

import { notificationService } from '../services/notificationService';
import { RootState } from '../store';
import { updateSettings, clearError } from '../store/slices/notificationsSlice';

interface UseNotificationsReturn {
  isInitialized: boolean;
  hasPermission: boolean;
  unreadCount: number;
  notifications: any[];
  settings: any;
  initialize: () => Promise<void>;
  updateNotificationSettings: (settings: any) => Promise<void>;
  markAsRead: (notificationId: string) => void;
  markAllAsRead: () => void;
  clearAllNotifications: () => Promise<void>;
}

export const useNotifications = (): UseNotificationsReturn => {
  const dispatch = useDispatch();
  const { 
    notifications, 
    unreadCount, 
    settings, 
    deviceRegistered,
    error 
  } = useSelector((state: RootState) => state.notifications);

  const [isInitialized, setIsInitialized] = useState(false);
  const [hasPermission, setHasPermission] = useState(false);

  // Initialize notification service
  const initialize = useCallback(async () => {
    try {
      await notificationService.initialize();
      setIsInitialized(notificationService.isServiceInitialized());
      setHasPermission(deviceRegistered);
    } catch (error) {
      console.error('Failed to initialize notifications:', error);
    }
  }, [deviceRegistered]);

  // Update notification settings
  const updateNotificationSettings = useCallback(async (newSettings: any) => {
    try {
      await notificationService.updateNotificationSettings(newSettings);
      dispatch(updateSettings(newSettings));
    } catch (error) {
      console.error('Failed to update notification settings:', error);
    }
  }, [dispatch]);

  // Mark notification as read
  const markAsRead = useCallback((notificationId: string) => {
    // This will be handled by the Redux slice
    // dispatch(markAsRead(notificationId));
  }, []);

  // Mark all notifications as read
  const markAllAsRead = useCallback(() => {
    // This will be handled by the Redux slice
    // dispatch(markAllAsRead());
  }, []);

  // Clear all notifications
  const clearAllNotifications = useCallback(async () => {
    try {
      await notificationService.cancelAllNotifications();
    } catch (error) {
      console.error('Failed to clear notifications:', error);
    }
  }, []);

  // Initialize on mount
  useEffect(() => {
    initialize();
  }, [initialize]);

  // Handle app state changes
  useEffect(() => {
    const handleAppStateChange = async (nextAppState: AppStateStatus) => {
      if (nextAppState === 'active') {
        // Process pending notifications when app becomes active
        await notificationService.processPendingNotifications();
      }
    };

    const subscription = AppState.addEventListener('change', handleAppStateChange);
    return () => subscription?.remove();
  }, []);

  // Clear errors automatically
  useEffect(() => {
    if (error) {
      const timer = setTimeout(() => {
        dispatch(clearError());
      }, 5000);
      return () => clearTimeout(timer);
    }
  }, [error, dispatch]);

  return {
    isInitialized,
    hasPermission,
    unreadCount,
    notifications,
    settings,
    initialize,
    updateNotificationSettings,
    markAsRead,
    markAllAsRead,
    clearAllNotifications,
  };
};

/**
 * Hook for managing notification preferences
 */
export const useNotificationPreferences = () => {
  const { settings } = useSelector((state: RootState) => state.notifications);
  const { updateNotificationSettings } = useNotifications();

  const toggleNotificationType = useCallback(async (type: string) => {
    const newSettings = {
      ...settings,
      [type]: !settings[type],
    };
    await updateNotificationSettings(newSettings);
  }, [settings, updateNotificationSettings]);

  const updateQuietHours = useCallback(async (start: string, end: string) => {
    const newSettings = {
      ...settings,
      quiet_hours_start: start,
      quiet_hours_end: end,
    };
    await updateNotificationSettings(newSettings);
  }, [settings, updateNotificationSettings]);

  const updateMinEdgeThreshold = useCallback(async (threshold: number) => {
    const newSettings = {
      ...settings,
      min_edge_threshold: threshold,
    };
    await updateNotificationSettings(newSettings);
  }, [settings, updateNotificationSettings]);

  return {
    settings,
    toggleNotificationType,
    updateQuietHours,
    updateMinEdgeThreshold,
  };
};

/**
 * Hook for notification analytics
 */
export const useNotificationAnalytics = () => {
  const { notifications } = useSelector((state: RootState) => state.notifications);

  const analytics = {
    total: notifications.length,
    unread: notifications.filter(n => !n.read).length,
    byType: notifications.reduce((acc, notification) => {
      acc[notification.type] = (acc[notification.type] || 0) + 1;
      return acc;
    }, {} as Record<string, number>),
    recent: notifications.filter(n => {
      const notificationDate = new Date(n.created_at);
      const oneDayAgo = new Date(Date.now() - 24 * 60 * 60 * 1000);
      return notificationDate > oneDayAgo;
    }).length,
  };

  return analytics;
};