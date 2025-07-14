/**
 * Jest Setup Configuration
 */

import 'react-native-gesture-handler/jestSetup';

// Mock react-native modules that don't work well in Jest
jest.mock('react-native-reanimated', () => {
  const Reanimated = require('react-native-reanimated/mock');
  Reanimated.default.call = () => {};
  return Reanimated;
});

// Mock AsyncStorage
jest.mock('@react-native-async-storage/async-storage', () =>
  require('@react-native-async-storage/async-storage/jest/async-storage-mock')
);

// Mock NetInfo
jest.mock('@react-native-community/netinfo', () => ({
  addEventListener: jest.fn(),
  fetch: jest.fn(() =>
    Promise.resolve({
      type: 'wifi',
      isConnected: true,
      isInternetReachable: true,
    })
  ),
}));

// Mock react-native-device-info
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

// Mock react-native-vector-icons
jest.mock('react-native-vector-icons/Ionicons', () => 'Icon');

// Mock react-native-biometrics
jest.mock('react-native-biometrics', () => ({
  __esModule: true,
  default: jest.fn(),
  BiometryTypes: {
    TouchID: 'TouchID',
    FaceID: 'FaceID',
    Biometrics: 'Biometrics',
  },
}));

// Mock Socket.IO
jest.mock('socket.io-client', () => ({
  io: jest.fn(() => ({
    on: jest.fn(),
    off: jest.fn(),
    emit: jest.fn(),
    connect: jest.fn(),
    disconnect: jest.fn(),
    connected: true,
  })),
}));

// Mock Firebase
jest.mock('@react-native-firebase/app', () => ({
  default: () => ({
    crashlytics: () => ({
      recordError: jest.fn(),
      crash: jest.fn(),
      log: jest.fn(),
      setUserId: jest.fn(),
      setCustomAttribute: jest.fn(),
      setCrashlyticsCollectionEnabled: jest.fn(),
    }),
  }),
}));

jest.mock('@react-native-firebase/crashlytics', () => ({
  default: () => ({
    recordError: jest.fn(),
    crash: jest.fn(),
    log: jest.fn(),
    setUserId: jest.fn(),
    setCustomAttribute: jest.fn(),
    setCrashlyticsCollectionEnabled: jest.fn(),
  }),
}));

// Mock react-native-exception-handler
jest.mock('react-native-exception-handler', () => ({
  setJSExceptionHandler: jest.fn(),
  setNativeExceptionHandler: jest.fn(),
}));

// Mock Linking
jest.mock('react-native/Libraries/Linking/Linking', () => ({
  openURL: jest.fn(() => Promise.resolve()),
  canOpenURL: jest.fn(() => Promise.resolve(true)),
  getInitialURL: jest.fn(() => Promise.resolve()),
  addEventListener: jest.fn(),
  removeEventListener: jest.fn(),
}));

// Mock Alert
jest.mock('react-native/Libraries/Alert/Alert', () => ({
  alert: jest.fn(),
}));

// Mock Dimensions
jest.mock('react-native/Libraries/Utilities/Dimensions', () => ({
  get: jest.fn(() => ({ width: 375, height: 812 })),
  addEventListener: jest.fn(),
  removeEventListener: jest.fn(),
}));

// Mock Platform
jest.mock('react-native/Libraries/Utilities/Platform', () => ({
  OS: 'ios',
  Version: '14.0',
  select: jest.fn(obj => obj.ios),
}));

// Mock Haptics (iOS only)
jest.mock('react-native', () => {
  const RN = jest.requireActual('react-native');
  return {
    ...RN,
    Haptics: {
      impactAsync: jest.fn(),
      ImpactFeedbackStyle: {
        Light: 'light',
        Medium: 'medium',
        Heavy: 'heavy',
      },
    },
    Platform: {
      OS: 'ios',
      Version: '14.0',
      select: jest.fn(obj => obj.ios),
    },
  };
});

// Global test setup
global.__DEV__ = true;

// Silence console warnings during tests
const originalWarn = console.warn;
console.warn = (...args) => {
  if (
    typeof args[0] === 'string' &&
    args[0].includes('Warning: React.createElement')
  ) {
    return;
  }
  originalWarn.call(console, ...args);
};

// Mock timers for better test control
jest.useFakeTimers();