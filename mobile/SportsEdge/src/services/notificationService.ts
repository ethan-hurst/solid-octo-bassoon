/**
 * Push Notification Service for Sports Edge mobile app
 */
import messaging, { FirebaseMessagingTypes } from '@react-native-firebase/messaging';
import notifee, { AndroidImportance, AndroidStyle } from '@notifee/react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Platform, PermissionsAndroid } from 'react-native';

import { store } from '../store';
import { addNotification, registerDevice } from '../store/slices/notificationsSlice';
import { apiClient } from './apiClient';

export interface NotificationPayload {
  id: string;
  title: string;
  body: string;
  type: 'value_bet' | 'game_starting' | 'social' | 'system';
  data?: any;
  image?: string;
  priority?: 'high' | 'normal' | 'low';
}

class NotificationService {
  private isInitialized = false;
  private fcmToken: string | null = null;

  /**
   * Initialize notification service
   */
  async initialize(): Promise<void> {
    try {
      if (this.isInitialized) {
        console.log('Notification service already initialized');
        return;
      }

      // Request permission
      const hasPermission = await this.requestPermission();
      if (!hasPermission) {
        console.log('Notification permission denied');
        return;
      }

      // Get FCM token
      await this.getFCMToken();

      // Register with backend
      await this.registerWithBackend();

      // Setup listeners
      this.setupListeners();

      // Initialize notifee
      await this.initializeNotifee();

      this.isInitialized = true;
      console.log('Notification service initialized successfully');
    } catch (error) {
      console.error('Error initializing notification service:', error);
    }
  }

  /**
   * Request notification permissions
   */
  private async requestPermission(): Promise<boolean> {
    try {
      if (Platform.OS === 'android') {
        if (Platform.Version >= 33) {
          const granted = await PermissionsAndroid.request(
            PermissionsAndroid.PERMISSIONS.POST_NOTIFICATIONS
          );
          return granted === PermissionsAndroid.RESULTS.GRANTED;
        }
        return true; // Android < 13 doesn't need runtime permission
      }

      // iOS permission
      const authStatus = await messaging().requestPermission({
        alert: true,
        announcement: false,
        badge: true,
        carPlay: false,
        provisional: false,
        sound: true,
      });

      const enabled = authStatus === messaging.AuthorizationStatus.AUTHORIZED ||
                     authStatus === messaging.AuthorizationStatus.PROVISIONAL;

      console.log('iOS notification permission:', enabled);
      return enabled;
    } catch (error) {
      console.error('Error requesting notification permission:', error);
      return false;
    }
  }

  /**
   * Get FCM token
   */
  private async getFCMToken(): Promise<string | null> {
    try {
      const token = await messaging().getToken();
      this.fcmToken = token;
      console.log('FCM Token:', token);

      // Store token locally
      await AsyncStorage.setItem('fcmToken', token);

      return token;
    } catch (error) {
      console.error('Error getting FCM token:', error);
      return null;
    }
  }

  /**
   * Register device with backend
   */
  private async registerWithBackend(): Promise<void> {
    try {
      if (!this.fcmToken) {
        console.log('No FCM token available for registration');
        return;
      }

      const deviceInfo = {
        token: this.fcmToken,
        platform: Platform.OS,
        app_version: '1.0.0', // TODO: Get from app config
        device_id: await this.getDeviceId(),
      };

      await store.dispatch(registerDevice(deviceInfo) as any);
      console.log('Device registered with backend');
    } catch (error) {
      console.error('Error registering device with backend:', error);
    }
  }

  /**
   * Get unique device ID
   */
  private async getDeviceId(): Promise<string> {
    try {
      let deviceId = await AsyncStorage.getItem('deviceId');
      if (!deviceId) {
        deviceId = `${Platform.OS}_${Date.now()}_${Math.random().toString(36)}`;
        await AsyncStorage.setItem('deviceId', deviceId);
      }
      return deviceId;
    } catch (error) {
      console.error('Error getting device ID:', error);
      return `${Platform.OS}_fallback_${Date.now()}`;
    }
  }

  /**
   * Setup Firebase messaging listeners
   */
  private setupListeners(): void {
    // Handle token refresh
    messaging().onTokenRefresh(async (token) => {
      console.log('FCM token refreshed:', token);
      this.fcmToken = token;
      await AsyncStorage.setItem('fcmToken', token);
      await this.registerWithBackend();
    });

    // Handle foreground messages
    messaging().onMessage(async (remoteMessage) => {
      console.log('Foreground message received:', remoteMessage);
      await this.handleForegroundMessage(remoteMessage);
    });

    // Handle background/quit state messages
    messaging().setBackgroundMessageHandler(async (remoteMessage) => {
      console.log('Background message received:', remoteMessage);
      await this.handleBackgroundMessage(remoteMessage);
    });

    // Handle notification opened app
    messaging().onNotificationOpenedApp((remoteMessage) => {
      console.log('Notification opened app:', remoteMessage);
      this.handleNotificationOpened(remoteMessage);
    });

    // Check if app was opened from a notification
    messaging()
      .getInitialNotification()
      .then((remoteMessage) => {
        if (remoteMessage) {
          console.log('App opened from notification:', remoteMessage);
          this.handleNotificationOpened(remoteMessage);
        }
      });
  }

  /**
   * Initialize Notifee for advanced notification features
   */
  private async initializeNotifee(): Promise<void> {
    try {
      // Create notification channels for Android
      if (Platform.OS === 'android') {
        await notifee.createChannels([
          {
            id: 'value_bets',
            name: 'Value Bet Alerts',
            importance: AndroidImportance.HIGH,
            description: 'Notifications for new value betting opportunities',
            sound: 'default',
            vibration: true,
          },
          {
            id: 'live_games',
            name: 'Live Game Updates',
            importance: AndroidImportance.DEFAULT,
            description: 'Updates for live games and odds changes',
            sound: 'default',
          },
          {
            id: 'social',
            name: 'Social Updates',
            importance: AndroidImportance.DEFAULT,
            description: 'Social notifications and interactions',
            sound: 'default',
          },
          {
            id: 'system',
            name: 'System Notifications',
            importance: AndroidImportance.LOW,
            description: 'System updates and maintenance notifications',
          },
        ]);
      }

      console.log('Notifee initialized successfully');
    } catch (error) {
      console.error('Error initializing Notifee:', error);
    }
  }

  /**
   * Handle foreground messages
   */
  private async handleForegroundMessage(
    remoteMessage: FirebaseMessagingTypes.RemoteMessage
  ): Promise<void> {
    try {
      const notification = this.parseRemoteMessage(remoteMessage);
      
      // Add to Redux store
      store.dispatch(addNotification(notification));

      // Show local notification
      await this.showLocalNotification(notification);
    } catch (error) {
      console.error('Error handling foreground message:', error);
    }
  }

  /**
   * Handle background messages
   */
  private async handleBackgroundMessage(
    remoteMessage: FirebaseMessagingTypes.RemoteMessage
  ): Promise<void> {
    try {
      const notification = this.parseRemoteMessage(remoteMessage);
      
      // Store notification locally for when app opens
      const storedNotifications = await AsyncStorage.getItem('pendingNotifications');
      const notifications = storedNotifications ? JSON.parse(storedNotifications) : [];
      notifications.push(notification);
      await AsyncStorage.setItem('pendingNotifications', JSON.stringify(notifications));

      console.log('Background message processed');
    } catch (error) {
      console.error('Error handling background message:', error);
    }
  }

  /**
   * Handle notification opened
   */
  private handleNotificationOpened(
    remoteMessage: FirebaseMessagingTypes.RemoteMessage
  ): void {
    try {
      const data = remoteMessage.data;
      
      // Navigate based on notification type
      if (data?.type === 'value_bet' && data?.bet_id) {
        // TODO: Navigate to quick analysis screen
        console.log('Navigate to value bet:', data.bet_id);
      } else if (data?.type === 'game_starting' && data?.game_id) {
        // TODO: Navigate to live game screen
        console.log('Navigate to live game:', data.game_id);
      } else if (data?.type === 'social' && data?.post_id) {
        // TODO: Navigate to social post
        console.log('Navigate to social post:', data.post_id);
      }
    } catch (error) {
      console.error('Error handling notification opened:', error);
    }
  }

  /**
   * Parse remote message to notification format
   */
  private parseRemoteMessage(
    remoteMessage: FirebaseMessagingTypes.RemoteMessage
  ): any {
    return {
      id: remoteMessage.messageId || Date.now().toString(),
      title: remoteMessage.notification?.title || 'Sports Edge',
      body: remoteMessage.notification?.body || '',
      type: remoteMessage.data?.type || 'system',
      data: remoteMessage.data,
      read: false,
      created_at: new Date().toISOString(),
    };
  }

  /**
   * Show local notification using Notifee
   */
  private async showLocalNotification(notification: NotificationPayload): Promise<void> {
    try {
      const channelId = this.getChannelId(notification.type);
      
      await notifee.displayNotification({
        id: notification.id,
        title: notification.title,
        body: notification.body,
        data: notification.data,
        android: {
          channelId,
          importance: AndroidImportance.HIGH,
          style: notification.image ? {
            type: AndroidStyle.BIGPICTURE,
            picture: notification.image,
          } : undefined,
          actions: this.getNotificationActions(notification.type),
        },
        ios: {
          sound: 'default',
          badge: true,
          categoryId: notification.type,
        },
      });
    } catch (error) {
      console.error('Error showing local notification:', error);
    }
  }

  /**
   * Get channel ID for notification type
   */
  private getChannelId(type: string): string {
    switch (type) {
      case 'value_bet':
        return 'value_bets';
      case 'game_starting':
        return 'live_games';
      case 'social':
        return 'social';
      default:
        return 'system';
    }
  }

  /**
   * Get notification actions based on type
   */
  private getNotificationActions(type: string) {
    switch (type) {
      case 'value_bet':
        return [
          {
            title: 'Quick Analysis',
            pressAction: { id: 'quick_analysis' },
          },
          {
            title: 'Add to Betslip',
            pressAction: { id: 'add_betslip' },
          },
        ];
      case 'game_starting':
        return [
          {
            title: 'View Game',
            pressAction: { id: 'view_game' },
          },
        ];
      case 'social':
        return [
          {
            title: 'View Post',
            pressAction: { id: 'view_post' },
          },
        ];
      default:
        return [];
    }
  }

  /**
   * Process pending notifications when app opens
   */
  async processPendingNotifications(): Promise<void> {
    try {
      const storedNotifications = await AsyncStorage.getItem('pendingNotifications');
      if (storedNotifications) {
        const notifications = JSON.parse(storedNotifications);
        
        for (const notification of notifications) {
          store.dispatch(addNotification(notification));
        }
        
        // Clear pending notifications
        await AsyncStorage.removeItem('pendingNotifications');
        console.log(`Processed ${notifications.length} pending notifications`);
      }
    } catch (error) {
      console.error('Error processing pending notifications:', error);
    }
  }

  /**
   * Update notification settings
   */
  async updateNotificationSettings(settings: any): Promise<void> {
    try {
      // TODO: Send settings to backend
      console.log('Notification settings updated:', settings);
    } catch (error) {
      console.error('Error updating notification settings:', error);
    }
  }

  /**
   * Cancel all notifications
   */
  async cancelAllNotifications(): Promise<void> {
    try {
      await notifee.cancelAllNotifications();
      console.log('All notifications cancelled');
    } catch (error) {
      console.error('Error cancelling notifications:', error);
    }
  }

  /**
   * Get current FCM token
   */
  getFCMToken(): string | null {
    return this.fcmToken;
  }

  /**
   * Check if service is initialized
   */
  isServiceInitialized(): boolean {
    return this.isInitialized;
  }
}

// Create and export singleton instance
export const notificationService = new NotificationService();