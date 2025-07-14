/**
 * Mobile Analytics Service for Sports Edge
 */
import AsyncStorage from '@react-native-async-storage/async-storage';
import DeviceInfo from 'react-native-device-info';
import { Platform } from 'react-native';

import { offlineService } from './offlineService';
import { apiClient } from './apiClient';
import { store } from '../store';

export interface AnalyticsEvent {
  id: string;
  event_type: string;
  properties: Record<string, any>;
  timestamp: number;
  session_id: string;
  user_id?: string;
  device_info: DeviceInfo;
}

export interface DeviceInfo {
  platform: string;
  os_version: string;
  app_version: string;
  device_model: string;
  device_id: string;
  screen_width: number;
  screen_height: number;
  timezone: string;
  locale: string;
}

export interface SessionInfo {
  session_id: string;
  start_time: number;
  last_activity: number;
  screen_count: number;
  event_count: number;
}

class AnalyticsService {
  private isInitialized = false;
  private sessionInfo: SessionInfo | null = null;
  private deviceInfo: DeviceInfo | null = null;
  private eventQueue: AnalyticsEvent[] = [];
  private flushTimer: NodeJS.Timeout | null = null;

  // Configuration
  private config = {
    flushInterval: 30000, // 30 seconds
    batchSize: 50,
    maxQueueSize: 1000,
    sessionTimeout: 30 * 60 * 1000, // 30 minutes
  };

  /**
   * Initialize analytics service
   */
  async initialize(): Promise<void> {
    try {
      if (this.isInitialized) {
        console.log('Analytics service already initialized');
        return;
      }

      // Collect device information
      await this.collectDeviceInfo();

      // Initialize or resume session
      await this.initializeSession();

      // Start auto-flush timer
      this.startFlushTimer();

      // Track app start
      await this.trackEvent('app_start', {
        is_first_launch: await this.isFirstLaunch(),
        previous_session_duration: await this.getPreviousSessionDuration(),
      });

      this.isInitialized = true;
      console.log('Analytics service initialized successfully');
    } catch (error) {
      console.error('Error initializing analytics service:', error);
    }
  }

  /**
   * Collect device and app information
   */
  private async collectDeviceInfo(): Promise<void> {
    try {
      const [
        appVersion,
        deviceModel,
        systemVersion,
        uniqueId,
        timezone,
        locale,
      ] = await Promise.all([
        DeviceInfo.getVersion(),
        DeviceInfo.getModel(),
        DeviceInfo.getSystemVersion(),
        DeviceInfo.getUniqueId(),
        DeviceInfo.getTimezone(),
        DeviceInfo.getDeviceLocale(),
      ]);

      const { width, height } = require('react-native').Dimensions.get('window');

      this.deviceInfo = {
        platform: Platform.OS,
        os_version: systemVersion,
        app_version: appVersion,
        device_model: deviceModel,
        device_id: uniqueId,
        screen_width: width,
        screen_height: height,
        timezone,
        locale,
      };

      console.log('Device info collected:', this.deviceInfo);
    } catch (error) {
      console.error('Error collecting device info:', error);
      
      // Fallback device info
      this.deviceInfo = {
        platform: Platform.OS,
        os_version: 'unknown',
        app_version: '1.0.0',
        device_model: 'unknown',
        device_id: 'unknown',
        screen_width: 375,
        screen_height: 667,
        timezone: 'UTC',
        locale: 'en-US',
      };
    }
  }

  /**
   * Initialize or resume analytics session
   */
  private async initializeSession(): Promise<void> {
    try {
      const storedSession = await AsyncStorage.getItem('analytics_session');
      const now = Date.now();

      if (storedSession) {
        const session: SessionInfo = JSON.parse(storedSession);
        
        // Check if session is still valid (not timed out)
        if (now - session.last_activity < this.config.sessionTimeout) {
          // Resume existing session
          this.sessionInfo = {
            ...session,
            last_activity: now,
          };
          
          await this.trackEvent('session_resume', {
            session_duration: now - session.start_time,
            time_since_last_activity: now - session.last_activity,
          });
        } else {
          // Session timed out, end it and start new one
          await this.trackEvent('session_timeout', {
            session_duration: session.last_activity - session.start_time,
            timeout_duration: now - session.last_activity,
          });
          
          await this.startNewSession();
        }
      } else {
        // No existing session, start new one
        await this.startNewSession();
      }

      // Save updated session
      await this.saveSession();
    } catch (error) {
      console.error('Error initializing session:', error);
      await this.startNewSession();
    }
  }

  /**
   * Start a new analytics session
   */
  private async startNewSession(): Promise<void> {
    const now = Date.now();
    const sessionId = `${now}_${Math.random().toString(36).substr(2, 9)}`;

    this.sessionInfo = {
      session_id: sessionId,
      start_time: now,
      last_activity: now,
      screen_count: 0,
      event_count: 0,
    };

    await this.trackEvent('session_start', {
      is_new_session: true,
    });

    console.log('New analytics session started:', sessionId);
  }

  /**
   * Save session to storage
   */
  private async saveSession(): Promise<void> {
    if (this.sessionInfo) {
      await AsyncStorage.setItem('analytics_session', JSON.stringify(this.sessionInfo));
    }
  }

  /**
   * Track analytics event
   */
  async trackEvent(eventType: string, properties: Record<string, any> = {}): Promise<void> {
    try {
      if (!this.isInitialized || !this.sessionInfo || !this.deviceInfo) {
        console.warn('Analytics service not initialized, queuing event');
        return;
      }

      // Update session activity
      this.sessionInfo.last_activity = Date.now();
      this.sessionInfo.event_count++;

      // Get current user ID
      const state = store.getState();
      const userId = state.auth.user?.id;

      // Create analytics event
      const event: AnalyticsEvent = {
        id: `${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
        event_type: eventType,
        properties: {
          ...properties,
          timestamp: Date.now(),
        },
        timestamp: Date.now(),
        session_id: this.sessionInfo.session_id,
        user_id: userId,
        device_info: this.deviceInfo,
      };

      // Add to queue
      this.eventQueue.push(event);

      // Store in offline storage for persistence
      await offlineService.storeAnalyticsEvent(eventType, event);

      console.log(`Analytics event tracked: ${eventType}`, properties);

      // Auto-flush if queue is getting large
      if (this.eventQueue.length >= this.config.batchSize) {
        await this.flushEvents();
      }

      // Save session
      await this.saveSession();
    } catch (error) {
      console.error('Error tracking analytics event:', error);
    }
  }

  /**
   * Track screen view
   */
  async trackScreenView(screenName: string, params?: Record<string, any>): Promise<void> {
    if (this.sessionInfo) {
      this.sessionInfo.screen_count++;
    }

    await this.trackEvent('screen_view', {
      screen_name: screenName,
      screen_params: params || {},
      previous_screen: await this.getPreviousScreen(),
    });

    // Store current screen for next view
    await AsyncStorage.setItem('current_screen', screenName);
  }

  /**
   * Track user interaction
   */
  async trackInteraction(elementType: string, elementId: string, action: string, context?: Record<string, any>): Promise<void> {
    await this.trackEvent('user_interaction', {
      element_type: elementType,
      element_id: elementId,
      action,
      context: context || {},
    });
  }

  /**
   * Track bet-related events
   */
  async trackBetEvent(eventType: string, betData: Record<string, any>): Promise<void> {
    await this.trackEvent(`bet_${eventType}`, {
      bet_id: betData.id,
      sport: betData.sport,
      odds: betData.odds,
      stake: betData.stake,
      edge: betData.edge,
      ...betData,
    });
  }

  /**
   * Track performance metrics
   */
  async trackPerformance(metricName: string, value: number, context?: Record<string, any>): Promise<void> {
    await this.trackEvent('performance_metric', {
      metric_name: metricName,
      value,
      context: context || {},
    });
  }

  /**
   * Track errors and crashes
   */
  async trackError(error: Error, context?: Record<string, any>): Promise<void> {
    await this.trackEvent('error', {
      error_message: error.message,
      error_stack: error.stack,
      error_name: error.name,
      context: context || {},
    });
  }

  /**
   * Track user properties
   */
  async setUserProperties(properties: Record<string, any>): Promise<void> {
    await this.trackEvent('user_properties_updated', {
      properties,
    });

    // Store user properties locally
    await AsyncStorage.setItem('user_properties', JSON.stringify(properties));
  }

  /**
   * Flush events to server
   */
  async flushEvents(): Promise<void> {
    if (this.eventQueue.length === 0) {
      return;
    }

    try {
      const events = [...this.eventQueue];
      this.eventQueue = [];

      console.log(`Flushing ${events.length} analytics events`);

      // Send to server
      await apiClient.post('/analytics/events/batch', { events });

      console.log('Analytics events flushed successfully');
    } catch (error) {
      console.error('Error flushing analytics events:', error);
      
      // Re-add events to queue if they failed to send
      // but limit queue size to prevent memory issues
      if (this.eventQueue.length < this.config.maxQueueSize - events.length) {
        this.eventQueue.unshift(...events);
      }
    }
  }

  /**
   * Start auto-flush timer
   */
  private startFlushTimer(): void {
    if (this.flushTimer) {
      clearInterval(this.flushTimer);
    }

    this.flushTimer = setInterval(() => {
      this.flushEvents();
    }, this.config.flushInterval);
  }

  /**
   * End current session
   */
  async endSession(): Promise<void> {
    if (!this.sessionInfo) return;

    const sessionDuration = Date.now() - this.sessionInfo.start_time;

    await this.trackEvent('session_end', {
      session_duration: sessionDuration,
      screen_count: this.sessionInfo.screen_count,
      event_count: this.sessionInfo.event_count,
    });

    // Flush remaining events
    await this.flushEvents();

    // Clear session
    await AsyncStorage.removeItem('analytics_session');
    this.sessionInfo = null;

    // Stop flush timer
    if (this.flushTimer) {
      clearInterval(this.flushTimer);
      this.flushTimer = null;
    }

    console.log('Analytics session ended');
  }

  /**
   * Get analytics summary
   */
  async getAnalyticsSummary(): Promise<Record<string, any>> {
    try {
      const [
        totalEvents,
        sessionCount,
        userProperties,
        currentScreen,
      ] = await Promise.all([
        this.getTotalEventsCount(),
        this.getSessionCount(),
        AsyncStorage.getItem('user_properties'),
        AsyncStorage.getItem('current_screen'),
      ]);

      return {
        total_events: totalEvents,
        session_count: sessionCount,
        current_session: this.sessionInfo,
        user_properties: userProperties ? JSON.parse(userProperties) : {},
        current_screen,
        device_info: this.deviceInfo,
        queue_size: this.eventQueue.length,
        is_initialized: this.isInitialized,
      };
    } catch (error) {
      console.error('Error getting analytics summary:', error);
      return {};
    }
  }

  /**
   * Helper methods
   */
  private async isFirstLaunch(): Promise<boolean> {
    const hasLaunched = await AsyncStorage.getItem('has_launched');
    if (!hasLaunched) {
      await AsyncStorage.setItem('has_launched', 'true');
      return true;
    }
    return false;
  }

  private async getPreviousSessionDuration(): Promise<number> {
    const lastSession = await AsyncStorage.getItem('last_session_duration');
    return lastSession ? parseInt(lastSession, 10) : 0;
  }

  private async getPreviousScreen(): Promise<string | null> {
    return await AsyncStorage.getItem('current_screen');
  }

  private async getTotalEventsCount(): Promise<number> {
    try {
      const stats = await offlineService.getStorageStats();
      return stats.analytics_events || 0;
    } catch (error) {
      return 0;
    }
  }

  private async getSessionCount(): Promise<number> {
    const count = await AsyncStorage.getItem('session_count');
    return count ? parseInt(count, 10) : 0;
  }

  /**
   * Update configuration
   */
  updateConfig(newConfig: Partial<typeof this.config>): void {
    this.config = { ...this.config, ...newConfig };
    
    if (newConfig.flushInterval && this.flushTimer) {
      this.startFlushTimer();
    }
  }

  /**
   * Check if service is initialized
   */
  isServiceInitialized(): boolean {
    return this.isInitialized;
  }

  /**
   * Get current session info
   */
  getCurrentSession(): SessionInfo | null {
    return this.sessionInfo;
  }
}

// Create and export singleton instance
export const analyticsService = new AnalyticsService();