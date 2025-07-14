/**
 * Biometric Service Tests
 */
import { biometricService } from '../../src/services/biometricService';

// Mock React Native Biometrics
jest.mock('react-native-biometrics', () => ({
  __esModule: true,
  default: jest.fn().mockImplementation(() => ({
    isSensorAvailable: jest.fn(),
    createKeys: jest.fn(),
    createSignature: jest.fn(),
    deleteKeys: jest.fn(),
    biometryType: jest.fn(),
  })),
  BiometryTypes: {
    TouchID: 'TouchID',
    FaceID: 'FaceID',
    Biometrics: 'Biometrics',
  },
}));

// Mock AsyncStorage
jest.mock('@react-native-async-storage/async-storage', () => ({
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
}));

// Mock react-native modules
jest.mock('react-native', () => ({
  Platform: {
    OS: 'ios',
  },
  Alert: {
    alert: jest.fn(),
  },
}));

import ReactNativeBiometrics, { BiometryTypes } from 'react-native-biometrics';
import AsyncStorage from '@react-native-async-storage/async-storage';

describe('Biometric Service', () => {
  let mockRNBiometrics: any;

  beforeEach(() => {
    jest.clearAllMocks();
    mockRNBiometrics = {
      isSensorAvailable: jest.fn(),
      createKeys: jest.fn(),
      createSignature: jest.fn(),
      deleteKeys: jest.fn(),
      biometryType: jest.fn(),
    };
    (ReactNativeBiometrics as jest.Mock).mockReturnValue(mockRNBiometrics);
    (AsyncStorage.getItem as jest.Mock).mockResolvedValue(null);
    (AsyncStorage.setItem as jest.Mock).mockResolvedValue(void 0);
  });

  describe('initialization', () => {
    it('should initialize successfully', async () => {
      await expect(biometricService.initialize()).resolves.not.toThrow();
    });

    it('should detect available biometric types', async () => {
      mockRNBiometrics.isSensorAvailable.mockResolvedValue({
        available: true,
        biometryType: BiometryTypes.FaceID,
      });

      await biometricService.initialize();
      const availability = await biometricService.checkAvailability();

      expect(availability.isAvailable).toBe(true);
      expect(availability.biometryType).toBe('FaceID');
    });

    it('should handle unavailable biometrics', async () => {
      mockRNBiometrics.isSensorAvailable.mockResolvedValue({
        available: false,
        error: 'BiometryNotAvailable',
      });

      await biometricService.initialize();
      const availability = await biometricService.checkAvailability();

      expect(availability.isAvailable).toBe(false);
      expect(availability.error).toBe('BiometryNotAvailable');
    });
  });

  describe('key management', () => {
    beforeEach(async () => {
      await biometricService.initialize();
    });

    it('should create biometric keys successfully', async () => {
      mockRNBiometrics.createKeys.mockResolvedValue({
        publicKey: 'mock-public-key',
      });

      const result = await biometricService.createKeys();

      expect(result.success).toBe(true);
      expect(result.publicKey).toBe('mock-public-key');
      expect(mockRNBiometrics.createKeys).toHaveBeenCalled();
    });

    it('should handle key creation failure', async () => {
      mockRNBiometrics.createKeys.mockRejectedValue(new Error('Key creation failed'));

      const result = await biometricService.createKeys();

      expect(result.success).toBe(false);
      expect(result.error).toBe('Key creation failed');
    });

    it('should delete biometric keys successfully', async () => {
      mockRNBiometrics.deleteKeys.mockResolvedValue({
        keysDeleted: true,
      });

      const result = await biometricService.deleteKeys();

      expect(result.success).toBe(true);
      expect(mockRNBiometrics.deleteKeys).toHaveBeenCalled();
    });
  });

  describe('authentication', () => {
    beforeEach(async () => {
      await biometricService.initialize();
      mockRNBiometrics.createKeys.mockResolvedValue({
        publicKey: 'mock-public-key',
      });
      await biometricService.createKeys();
    });

    it('should authenticate successfully with biometrics', async () => {
      mockRNBiometrics.createSignature.mockResolvedValue({
        success: true,
        signature: 'mock-signature',
      });

      const result = await biometricService.authenticate('Please authenticate');

      expect(result.success).toBe(true);
      expect(result.signature).toBe('mock-signature');
      expect(mockRNBiometrics.createSignature).toHaveBeenCalledWith({
        promptMessage: 'Please authenticate',
        payload: expect.any(String),
      });
    });

    it('should handle authentication failure', async () => {
      mockRNBiometrics.createSignature.mockResolvedValue({
        success: false,
        error: 'UserCancel',
      });

      const result = await biometricService.authenticate('Please authenticate');

      expect(result.success).toBe(false);
      expect(result.error).toBe('UserCancel');
    });

    it('should handle authentication with custom options', async () => {
      mockRNBiometrics.createSignature.mockResolvedValue({
        success: true,
        signature: 'mock-signature',
      });

      const result = await biometricService.authenticate('Custom prompt', {
        fallbackPrompt: 'Use passcode',
        disableDeviceFallback: false,
      });

      expect(result.success).toBe(true);
      expect(mockRNBiometrics.createSignature).toHaveBeenCalledWith({
        promptMessage: 'Custom prompt',
        payload: expect.any(String),
        fallbackPrompt: 'Use passcode',
        disableDeviceFallback: false,
      });
    });
  });

  describe('settings management', () => {
    beforeEach(async () => {
      await biometricService.initialize();
    });

    it('should enable biometric authentication', async () => {
      mockRNBiometrics.createKeys.mockResolvedValue({
        publicKey: 'mock-public-key',
      });

      const result = await biometricService.enableBiometricAuth();

      expect(result.success).toBe(true);
      expect(AsyncStorage.setItem).toHaveBeenCalledWith(
        '@SportsEdge:biometric_enabled',
        'true'
      );
    });

    it('should disable biometric authentication', async () => {
      mockRNBiometrics.deleteKeys.mockResolvedValue({
        keysDeleted: true,
      });

      const result = await biometricService.disableBiometricAuth();

      expect(result.success).toBe(true);
      expect(AsyncStorage.setItem).toHaveBeenCalledWith(
        '@SportsEdge:biometric_enabled',
        'false'
      );
    });

    it('should check if biometric auth is enabled', async () => {
      (AsyncStorage.getItem as jest.Mock).mockResolvedValue('true');

      const isEnabled = await biometricService.isBiometricEnabled();

      expect(isEnabled).toBe(true);
      expect(AsyncStorage.getItem).toHaveBeenCalledWith(
        '@SportsEdge:biometric_enabled'
      );
    });

    it('should return false when biometric setting not found', async () => {
      (AsyncStorage.getItem as jest.Mock).mockResolvedValue(null);

      const isEnabled = await biometricService.isBiometricEnabled();

      expect(isEnabled).toBe(false);
    });
  });

  describe('error handling', () => {
    beforeEach(async () => {
      await biometricService.initialize();
    });

    it('should handle biometric hardware errors', async () => {
      mockRNBiometrics.isSensorAvailable.mockResolvedValue({
        available: false,
        error: 'BiometryNotAvailable',
      });

      const availability = await biometricService.checkAvailability();

      expect(availability.isAvailable).toBe(false);
      expect(availability.error).toBe('BiometryNotAvailable');
    });

    it('should handle network-related errors gracefully', async () => {
      mockRNBiometrics.createSignature.mockRejectedValue(
        new Error('Network error')
      );

      const result = await biometricService.authenticate('Test prompt');

      expect(result.success).toBe(false);
      expect(result.error).toContain('Network error');
    });

    it('should handle storage errors', async () => {
      (AsyncStorage.setItem as jest.Mock).mockRejectedValue(
        new Error('Storage error')
      );

      const result = await biometricService.enableBiometricAuth();

      expect(result.success).toBe(false);
    });
  });

  describe('platform-specific behavior', () => {
    it('should handle iOS-specific biometric types', async () => {
      mockRNBiometrics.isSensorAvailable.mockResolvedValue({
        available: true,
        biometryType: BiometryTypes.FaceID,
      });

      await biometricService.initialize();
      const availability = await biometricService.checkAvailability();

      expect(availability.biometryType).toBe('FaceID');
    });

    it('should handle Android-specific biometric types', async () => {
      // Mock Android platform
      require('react-native').Platform.OS = 'android';

      mockRNBiometrics.isSensorAvailable.mockResolvedValue({
        available: true,
        biometryType: BiometryTypes.Biometrics,
      });

      await biometricService.initialize();
      const availability = await biometricService.checkAvailability();

      expect(availability.biometryType).toBe('Biometrics');
    });
  });
});