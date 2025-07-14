/**
 * Performance Optimization Utilities
 */
import { InteractionManager } from 'react-native';

export interface PerformanceConfig {
  enableProfiling: boolean;
  enableOptimizations: boolean;
  debugMode: boolean;
}

export const performanceConfig: PerformanceConfig = {
  enableProfiling: __DEV__,
  enableOptimizations: true,
  debugMode: __DEV__,
};

export class PerformanceManager {
  private static measurements: Map<string, number> = new Map();
  private static pendingInteractions: Set<string> = new Set();

  static startMeasurement(name: string): void {
    if (performanceConfig.enableProfiling) {
      this.measurements.set(name, Date.now());
    }
  }

  static endMeasurement(name: string): number | null {
    if (performanceConfig.enableProfiling && this.measurements.has(name)) {
      const startTime = this.measurements.get(name)!;
      const duration = Date.now() - startTime;
      this.measurements.delete(name);
      
      if (performanceConfig.debugMode) {
        console.log(`[Performance] ${name}: ${duration}ms`);
      }
      
      return duration;
    }
    return null;
  }

  static runAfterInteractions<T>(callback: () => T): Promise<T> {
    return new Promise((resolve) => {
      InteractionManager.runAfterInteractions(() => {
        resolve(callback());
      });
    });
  }

  static createInteractionHandle(name: string): number {
    const handle = InteractionManager.createInteractionHandle();
    this.pendingInteractions.add(name);
    
    if (performanceConfig.debugMode) {
      console.log(`[Performance] Started interaction: ${name}`);
    }
    
    return handle;
  }

  static clearInteractionHandle(handle: number, name?: string): void {
    InteractionManager.clearInteractionHandle(handle);
    
    if (name) {
      this.pendingInteractions.delete(name);
      
      if (performanceConfig.debugMode) {
        console.log(`[Performance] Cleared interaction: ${name}`);
      }
    }
  }

  static getPendingInteractions(): string[] {
    return Array.from(this.pendingInteractions);
  }

  static async waitForPendingInteractions(): Promise<void> {
    return new Promise((resolve) => {
      InteractionManager.runAfterInteractions(resolve);
    });
  }
}

export const withPerformanceTracking = <T extends (...args: any[]) => any>(
  fn: T,
  name: string
): T => {
  return ((...args: any[]) => {
    PerformanceManager.startMeasurement(name);
    const result = fn(...args);
    
    if (result instanceof Promise) {
      return result.finally(() => {
        PerformanceManager.endMeasurement(name);
      });
    }
    
    PerformanceManager.endMeasurement(name);
    return result;
  }) as T;
};

export const debounce = <T extends (...args: any[]) => any>(
  func: T,
  wait: number,
  immediate = false
): T => {
  let timeout: NodeJS.Timeout | null = null;
  
  return ((...args: any[]) => {
    const later = () => {
      timeout = null;
      if (!immediate) func(...args);
    };
    
    const callNow = immediate && !timeout;
    
    if (timeout) clearTimeout(timeout);
    timeout = setTimeout(later, wait);
    
    if (callNow) func(...args);
  }) as T;
};

export const throttle = <T extends (...args: any[]) => any>(
  func: T,
  limit: number
): T => {
  let inThrottle: boolean;
  
  return ((...args: any[]) => {
    if (!inThrottle) {
      func(...args);
      inThrottle = true;
      setTimeout(() => (inThrottle = false), limit);
    }
  }) as T;
};

export const memoize = <T extends (...args: any[]) => any>(
  fn: T,
  getKey?: (...args: Parameters<T>) => string
): T => {
  const cache = new Map();
  
  return ((...args: any[]) => {
    const key = getKey ? getKey(...args) : JSON.stringify(args);
    
    if (cache.has(key)) {
      return cache.get(key);
    }
    
    const result = fn(...args);
    cache.set(key, result);
    
    return result;
  }) as T;
};

export const batchUpdates = <T>(
  updates: (() => T)[],
  batchSize: number = 10,
  delay: number = 0
): Promise<T[]> => {
  return new Promise((resolve) => {
    const results: T[] = [];
    let currentIndex = 0;
    
    const processBatch = () => {
      const batch = updates.slice(currentIndex, currentIndex + batchSize);
      
      batch.forEach((update) => {
        results.push(update());
      });
      
      currentIndex += batchSize;
      
      if (currentIndex < updates.length) {
        setTimeout(processBatch, delay);
      } else {
        resolve(results);
      }
    };
    
    processBatch();
  });
};

export const createLazyComponent = <T extends React.ComponentType<any>>(
  importFn: () => Promise<{ default: T }>
): React.LazyExoticComponent<T> => {
  return React.lazy(importFn);
};

export const isLowEndDevice = (): boolean => {
  // This is a simplified check - in a real app, you'd want more sophisticated detection
  return false; // Placeholder implementation
};

export const getOptimalImageSize = (
  originalWidth: number,
  originalHeight: number,
  maxWidth: number,
  maxHeight: number
): { width: number; height: number } => {
  const aspectRatio = originalWidth / originalHeight;
  
  let newWidth = originalWidth;
  let newHeight = originalHeight;
  
  if (newWidth > maxWidth) {
    newWidth = maxWidth;
    newHeight = newWidth / aspectRatio;
  }
  
  if (newHeight > maxHeight) {
    newHeight = maxHeight;
    newWidth = newHeight * aspectRatio;
  }
  
  return {
    width: Math.round(newWidth),
    height: Math.round(newHeight),
  };
};

export const preloadImages = async (imageUrls: string[]): Promise<void> => {
  const Image = require('react-native').Image;
  
  const promises = imageUrls.map((url) => {
    return new Promise<void>((resolve, reject) => {
      Image.prefetch(url)
        .then(() => resolve())
        .catch(() => resolve()); // Don't fail the entire batch if one image fails
    });
  });
  
  await Promise.all(promises);
};

export class MemoryManager {
  private static memoryWarningHandlers: (() => void)[] = [];
  
  static addMemoryWarningHandler(handler: () => void): void {
    this.memoryWarningHandlers.push(handler);
  }
  
  static removeMemoryWarningHandler(handler: () => void): void {
    const index = this.memoryWarningHandlers.indexOf(handler);
    if (index > -1) {
      this.memoryWarningHandlers.splice(index, 1);
    }
  }
  
  static triggerMemoryWarning(): void {
    this.memoryWarningHandlers.forEach((handler) => {
      try {
        handler();
      } catch (error) {
        console.warn('Error in memory warning handler:', error);
      }
    });
  }
  
  static clearImageCache(): void {
    // This would clear the image cache in a real implementation
    if (performanceConfig.debugMode) {
      console.log('[MemoryManager] Cleared image cache');
    }
  }
  
  static clearComponentCache(): void {
    // This would clear cached components in a real implementation
    if (performanceConfig.debugMode) {
      console.log('[MemoryManager] Cleared component cache');
    }
  }
}

// Performance monitoring for Redux actions
export const performanceMiddleware = (store: any) => (next: any) => (action: any) => {
  const start = Date.now();
  const result = next(action);
  const duration = Date.now() - start;
  
  if (duration > 16.67) { // Longer than one frame at 60fps
    console.warn(`[Redux Performance] Slow action ${action.type}: ${duration}ms`);
  }
  
  return result;
};

// React Native specific optimizations
export const enableHermes = (): boolean => {
  return !!(global as any).HermesInternal;
};

export const enableFabric = (): boolean => {
  return !!(global as any).nativeFabricUIManager;
};

export const enableTurboModules = (): boolean => {
  return !!(global as any).RN$TurboInterop;
};

export const getPerformanceInfo = () => ({
  hermes: enableHermes(),
  fabric: enableFabric(),
  turboModules: enableTurboModules(),
  lowEndDevice: isLowEndDevice(),
  pendingInteractions: PerformanceManager.getPendingInteractions(),
});