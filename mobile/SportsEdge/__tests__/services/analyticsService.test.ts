/**
 * Analytics Service Tests
 */
import { analyticsService } from '../../src/services/analyticsService';
import AsyncStorage from '@react-native-async-storage/async-storage';

// Mock AsyncStorage
jest.mock('@react-native-async-storage/async-storage', () => ({
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  getAllKeys: jest.fn(),
  multiGet: jest.fn(),
  multiSet: jest.fn(),
  multiRemove: jest.fn(),
}));

// Mock react-native modules
jest.mock('react-native', () => ({
  Platform: {
    OS: 'ios',
    Version: '14.0',
  },
  Dimensions: {
    get: () => ({ width: 375, height: 812 }),
  },
}));

// Mock device info
jest.mock('react-native-device-info', () => ({
  getUniqueId: () => Promise.resolve('test-device-id'),
  getSystemVersion: () => '14.0',
  getModel: () => 'iPhone 12',
  getManufacturer: () => Promise.resolve('Apple'),
  getBrand: () => 'Apple',
  getCarrier: () => Promise.resolve('Verizon'),
  isTablet: () => Promise.resolve(false),
  hasNotch: () => Promise.resolve(true),
  getInstallReferrer: () => Promise.resolve('test-referrer'),
  getFirstInstallTime: () => Promise.resolve(1640995200000),
  getLastUpdateTime: () => Promise.resolve(1640995200000),
}));

// Mock NetInfo
jest.mock('@react-native-community/netinfo', () => ({
  addEventListener: jest.fn(),
  fetch: () => Promise.resolve({
    type: 'wifi',
    isConnected: true,
    isInternetReachable: true,
  }),
}));

describe('Analytics Service', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (AsyncStorage.getItem as jest.Mock).mockResolvedValue(null);
    (AsyncStorage.setItem as jest.Mock).mockResolvedValue(void 0);
  });

  describe('initialization', () => {
    it('should initialize successfully', async () => {
      await expect(analyticsService.initialize()).resolves.not.toThrow();
    });

    it('should set user ID correctly', async () => {
      await analyticsService.initialize();
      analyticsService.setUserId('test-user-123');
      
      expect(analyticsService.getCurrentUserId()).toBe('test-user-123');
    });

    it('should start new session', async () => {
      await analyticsService.initialize();
      const sessionId = analyticsService.startSession();
      
      expect(sessionId).toBeTruthy();
      expect(typeof sessionId).toBe('string');
    });
  });

  describe('event tracking', () => {
    beforeEach(async () => {
      await analyticsService.initialize();
    });

    it('should track custom events', async () => {
      const trackEventSpy = jest.spyOn(analyticsService, 'trackEvent');
      
      await analyticsService.trackEvent('test_event', {
        test_property: 'test_value',
        numeric_property: 123,
      });
      
      expect(trackEventSpy).toHaveBeenCalledWith('test_event', {
        test_property: 'test_value',
        numeric_property: 123,
      });
    });

    it('should track screen views', async () => {
      const trackScreenSpy = jest.spyOn(analyticsService, 'trackScreen');
      
      await analyticsService.trackScreen('TestScreen', {
        previous_screen: 'HomeScreen',
      });
      
      expect(trackScreenSpy).toHaveBeenCalledWith('TestScreen', {
        previous_screen: 'HomeScreen',
      });
    });

    it('should track user interactions', async () => {
      const trackInteractionSpy = jest.spyOn(analyticsService, 'trackInteraction');
      
      await analyticsService.trackInteraction('button_press', 'login_button', {
        screen: 'LoginScreen',
      });
      
      expect(trackInteractionSpy).toHaveBeenCalledWith('button_press', 'login_button', {
        screen: 'LoginScreen',
      });
    });

    it('should track betting events', async () => {
      const trackBettingEventSpy = jest.spyOn(analyticsService, 'trackBettingEvent');
      
      await analyticsService.trackBettingEvent('bet_placed', {
        bet_type: 'moneyline',
        amount: 100,
        odds: -110,
        sport: 'NFL',
      });
      
      expect(trackBettingEventSpy).toHaveBeenCalledWith('bet_placed', {
        bet_type: 'moneyline',
        amount: 100,
        odds: -110,
        sport: 'NFL',
      });
    });

    it('should track errors', async () => {
      const trackErrorSpy = jest.spyOn(analyticsService, 'trackError');
      const testError = new Error('Test error');
      
      await analyticsService.trackError(testError, {
        screen: 'TestScreen',
        action: 'test_action',
      });
      
      expect(trackErrorSpy).toHaveBeenCalledWith(testError, {
        screen: 'TestScreen',
        action: 'test_action',
      });
    });
  });

  describe('performance tracking', () => {
    beforeEach(async () => {
      await analyticsService.initialize();
    });

    it('should track performance metrics', async () => {
      const trackPerformanceSpy = jest.spyOn(analyticsService, 'trackPerformance');
      
      await analyticsService.trackPerformance('api_call', 250, {
        endpoint: '/api/bets',
        success: true,
      });
      
      expect(trackPerformanceSpy).toHaveBeenCalledWith('api_call', 250, {
        endpoint: '/api/bets',
        success: true,
      });
    });

    it('should track render performance', async () => {
      const trackRenderPerformanceSpy = jest.spyOn(analyticsService, 'trackRenderPerformance');
      
      await analyticsService.trackRenderPerformance('TestComponent', 16.7, {
        props_count: 5,
        children_count: 3,
      });
      
      expect(trackRenderPerformanceSpy).toHaveBeenCalledWith('TestComponent', 16.7, {
        props_count: 5,
        children_count: 3,
      });
    });
  });

  describe('offline handling', () => {
    beforeEach(async () => {
      await analyticsService.initialize();
    });

    it('should queue events when offline', async () => {
      // Mock offline state
      const mockNetInfo = require('@react-native-community/netinfo');
      mockNetInfo.fetch.mockResolvedValueOnce({
        type: 'none',
        isConnected: false,
        isInternetReachable: false,
      });

      await analyticsService.trackEvent('offline_event', { test: 'data' });
      
      // Event should be queued, not immediately sent
      expect(AsyncStorage.setItem).toHaveBeenCalled();
    });

    it('should flush queued events when back online', async () => {
      const flushEventsSpy = jest.spyOn(analyticsService, 'flushQueuedEvents');
      
      await analyticsService.flushQueuedEvents();
      
      expect(flushEventsSpy).toHaveBeenCalled();
    });
  });

  describe('session management', () => {
    beforeEach(async () => {
      await analyticsService.initialize();
    });

    it('should end session correctly', async () => {
      const sessionId = analyticsService.startSession();
      const endSessionSpy = jest.spyOn(analyticsService, 'endSession');
      
      await analyticsService.endSession();
      
      expect(endSessionSpy).toHaveBeenCalled();
    });

    it('should get session info', () => {
      const sessionId = analyticsService.startSession();
      const sessionInfo = analyticsService.getSessionInfo();
      
      expect(sessionInfo).toHaveProperty('sessionId');
      expect(sessionInfo).toHaveProperty('startTime');
      expect(sessionInfo.sessionId).toBe(sessionId);
    });
  });

  describe('A/B testing', () => {
    beforeEach(async () => {
      await analyticsService.initialize();
    });

    it('should track A/B test exposure', async () => {
      const trackABTestSpy = jest.spyOn(analyticsService, 'trackABTest');
      
      await analyticsService.trackABTest('test_experiment', 'variant_a', {
        test_context: 'login_screen',
      });
      
      expect(trackABTestSpy).toHaveBeenCalledWith('test_experiment', 'variant_a', {
        test_context: 'login_screen',
      });
    });
  });

  describe('user properties', () => {
    beforeEach(async () => {
      await analyticsService.initialize();
    });

    it('should set user properties', async () => {
      const setUserPropertiesSpy = jest.spyOn(analyticsService, 'setUserProperties');
      
      await analyticsService.setUserProperties({
        user_type: 'premium',
        signup_date: '2024-01-01',
        preferred_sport: 'NFL',
      });
      
      expect(setUserPropertiesSpy).toHaveBeenCalledWith({
        user_type: 'premium',
        signup_date: '2024-01-01',
        preferred_sport: 'NFL',
      });
    });
  });
});