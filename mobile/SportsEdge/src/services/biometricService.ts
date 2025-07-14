/**
 * Biometric Authentication Service for Sports Edge mobile app
 */
import ReactNativeBiometrics, { BiometryTypes } from 'react-native-biometrics';
import AsyncStorage from '@react-native-async-storage/async-storage';

const BIOMETRIC_STORAGE_KEY = 'biometric_enabled';
const BIOMETRIC_TOKEN_KEY = 'biometric_token';

export interface BiometricResult {
  success: boolean;
  error?: string;
  signature?: string;
}

export interface BiometricCapabilities {
  available: boolean;
  biometryType: BiometryTypes | undefined;
  error?: string;
}

class BiometricService {
  private rnBiometrics: ReactNativeBiometrics;

  constructor() {
    this.rnBiometrics = new ReactNativeBiometrics({
      allowDeviceCredentials: true,
    });
  }

  /**
   * Check if biometric authentication is available on the device
   */
  async isBiometricAvailable(): Promise<boolean> {
    try {
      const { available } = await this.rnBiometrics.isSensorAvailable();
      return available;
    } catch (error) {
      console.error('Error checking biometric availability:', error);
      return false;
    }
  }

  /**
   * Get detailed biometric capabilities
   */
  async getBiometricCapabilities(): Promise<BiometricCapabilities> {
    try {
      const { available, biometryType, error } = await this.rnBiometrics.isSensorAvailable();
      
      return {
        available,
        biometryType,
        error,
      };
    } catch (error: any) {
      return {
        available: false,
        biometryType: undefined,
        error: error.message || 'Unknown error',
      };
    }
  }

  /**
   * Create biometric keys for secure authentication
   */
  async createBiometricKeys(): Promise<BiometricResult> {
    try {
      const { available } = await this.rnBiometrics.isSensorAvailable();
      
      if (!available) {
        return {
          success: false,
          error: 'Biometric authentication is not available on this device',
        };
      }

      const { keysExist } = await this.rnBiometrics.biometricKeysExist();
      
      if (!keysExist) {
        const { publicKey } = await this.rnBiometrics.createKeys();
        console.log('Created biometric keys with public key:', publicKey);
      }

      return { success: true };
    } catch (error: any) {
      console.error('Error creating biometric keys:', error);
      return {
        success: false,
        error: error.message || 'Failed to create biometric keys',
      };
    }
  }

  /**
   * Authenticate user using biometric
   */
  async authenticate(
    promptMessage: string = 'Authenticate to access Sports Edge',
    cancelButtonText: string = 'Cancel'
  ): Promise<BiometricResult> {
    try {
      const { available } = await this.rnBiometrics.isSensorAvailable();
      
      if (!available) {
        return {
          success: false,
          error: 'Biometric authentication is not available',
        };
      }

      const epochTimeSeconds = Math.round((new Date()).getTime() / 1000).toString();
      const payload = epochTimeSeconds + 'sportsedge_auth';

      const { success, signature, error } = await this.rnBiometrics.createSignature({
        promptMessage,
        cancelButtonText,
        payload,
      });

      if (success && signature) {
        return {
          success: true,
          signature,
        };
      } else {
        return {
          success: false,
          error: error || 'Authentication failed',
        };
      }
    } catch (error: any) {
      console.error('Biometric authentication error:', error);
      
      // Handle specific error cases
      if (error.message?.includes('UserCancel')) {
        return {
          success: false,
          error: 'Authentication was cancelled',
        };
      }
      
      if (error.message?.includes('UserFallback')) {
        return {
          success: false,
          error: 'User chose to use device passcode',
        };
      }
      
      return {
        success: false,
        error: error.message || 'Biometric authentication failed',
      };
    }
  }

  /**
   * Enable biometric authentication for the user
   */
  async enableBiometric(): Promise<BiometricResult> {
    try {
      // First create keys if they don't exist
      const keyResult = await this.createBiometricKeys();
      if (!keyResult.success) {
        return keyResult;
      }

      // Test authentication
      const authResult = await this.authenticate(
        'Enable biometric login for Sports Edge',
        'Cancel'
      );

      if (authResult.success) {
        await AsyncStorage.setItem(BIOMETRIC_STORAGE_KEY, 'true');
        return { success: true };
      } else {
        return authResult;
      }
    } catch (error: any) {
      console.error('Error enabling biometric:', error);
      return {
        success: false,
        error: error.message || 'Failed to enable biometric authentication',
      };
    }
  }

  /**
   * Disable biometric authentication
   */
  async disableBiometric(): Promise<BiometricResult> {
    try {
      await AsyncStorage.removeItem(BIOMETRIC_STORAGE_KEY);
      await AsyncStorage.removeItem(BIOMETRIC_TOKEN_KEY);
      
      // Optionally delete biometric keys
      const { keysExist } = await this.rnBiometrics.biometricKeysExist();
      if (keysExist) {
        await this.rnBiometrics.deleteKeys();
      }

      return { success: true };
    } catch (error: any) {
      console.error('Error disabling biometric:', error);
      return {
        success: false,
        error: error.message || 'Failed to disable biometric authentication',
      };
    }
  }

  /**
   * Check if biometric is enabled for the user
   */
  async isBiometricEnabled(): Promise<boolean> {
    try {
      const enabled = await AsyncStorage.getItem(BIOMETRIC_STORAGE_KEY);
      return enabled === 'true';
    } catch (error) {
      console.error('Error checking biometric enabled status:', error);
      return false;
    }
  }

  /**
   * Store biometric credentials securely
   */
  async storeBiometricCredentials(token: string): Promise<BiometricResult> {
    try {
      await AsyncStorage.setItem(BIOMETRIC_TOKEN_KEY, token);
      return { success: true };
    } catch (error: any) {
      console.error('Error storing biometric credentials:', error);
      return {
        success: false,
        error: error.message || 'Failed to store biometric credentials',
      };
    }
  }

  /**
   * Get stored biometric credentials
   */
  async getBiometricCredentials(): Promise<string | null> {
    try {
      return await AsyncStorage.getItem(BIOMETRIC_TOKEN_KEY);
    } catch (error) {
      console.error('Error getting biometric credentials:', error);
      return null;
    }
  }

  /**
   * Clear all biometric data
   */
  async clearBiometricData(): Promise<void> {
    try {
      await AsyncStorage.multiRemove([BIOMETRIC_STORAGE_KEY, BIOMETRIC_TOKEN_KEY]);
      
      const { keysExist } = await this.rnBiometrics.biometricKeysExist();
      if (keysExist) {
        await this.rnBiometrics.deleteKeys();
      }
    } catch (error) {
      console.error('Error clearing biometric data:', error);
    }
  }

  /**
   * Get user-friendly biometric type name
   */
  getBiometricTypeName(biometryType: BiometryTypes | undefined): string {
    switch (biometryType) {
      case BiometryTypes.TouchID:
        return 'Touch ID';
      case BiometryTypes.FaceID:
        return 'Face ID';
      case BiometryTypes.Biometrics:
        return 'Biometric Authentication';
      default:
        return 'Biometric Authentication';
    }
  }
}

// Create and export singleton instance
export const biometricService = new BiometricService();