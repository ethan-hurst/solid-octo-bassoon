/**
 * Performance Hooks
 */
import { useEffect, useRef, useState, useCallback, useMemo } from 'react';
import { AppState, AppStateStatus } from 'react-native';
import { PerformanceManager, MemoryManager } from '../utils/performance';

export const usePerformanceTracking = (componentName: string) => {
  const mountTime = useRef<number>(Date.now());
  const renderCount = useRef<number>(0);
  
  useEffect(() => {
    PerformanceManager.startMeasurement(`${componentName}_mount`);
    
    return () => {
      const mountDuration = PerformanceManager.endMeasurement(`${componentName}_mount`);
      console.log(`[Performance] ${componentName} was mounted for ${mountDuration}ms`);
    };
  }, [componentName]);
  
  useEffect(() => {
    renderCount.current += 1;
  });
  
  return {
    renderCount: renderCount.current,
    mountTime: mountTime.current,
  };
};

export const useMemoryWarning = (onMemoryWarning: () => void) => {
  useEffect(() => {
    MemoryManager.addMemoryWarningHandler(onMemoryWarning);
    
    return () => {
      MemoryManager.removeMemoryWarningHandler(onMemoryWarning);
    };
  }, [onMemoryWarning]);
};

export const useAppStatePerformance = () => {
  const [appState, setAppState] = useState<AppStateStatus>(AppState.currentState);
  const backgroundTime = useRef<number | null>(null);
  
  useEffect(() => {
    const handleAppStateChange = (nextAppState: AppStateStatus) => {
      if (appState === 'active' && nextAppState === 'background') {
        backgroundTime.current = Date.now();
        // Trigger memory cleanup when app goes to background
        MemoryManager.clearImageCache();
      } else if (appState === 'background' && nextAppState === 'active') {
        if (backgroundTime.current) {
          const backgroundDuration = Date.now() - backgroundTime.current;
          console.log(`[Performance] App was in background for ${backgroundDuration}ms`);
          backgroundTime.current = null;
        }
      }
      
      setAppState(nextAppState);
    };
    
    const subscription = AppState.addEventListener('change', handleAppStateChange);
    
    return () => {
      subscription?.remove();
    };
  }, [appState]);
  
  return { appState, isBackground: appState !== 'active' };
};

export const useOptimizedCallback = <T extends (...args: any[]) => any>(
  callback: T,
  deps: React.DependencyList,
  options?: {
    debounce?: number;
    throttle?: number;
  }
): T => {
  const { debounce: debounceMs, throttle: throttleMs } = options || {};
  
  const memoizedCallback = useCallback(callback, deps);
  
  return useMemo(() => {
    let optimizedCallback = memoizedCallback;
    
    if (debounceMs) {
      const { debounce } = require('../utils/performance');
      optimizedCallback = debounce(optimizedCallback, debounceMs);
    }
    
    if (throttleMs) {
      const { throttle } = require('../utils/performance');
      optimizedCallback = throttle(optimizedCallback, throttleMs);
    }
    
    return optimizedCallback;
  }, [memoizedCallback, debounceMs, throttleMs]);
};

export const useInteractionManager = () => {
  const [interactionsComplete, setInteractionsComplete] = useState(false);
  
  useEffect(() => {
    PerformanceManager.waitForPendingInteractions().then(() => {
      setInteractionsComplete(true);
    });
  }, []);
  
  const createInteraction = useCallback((name: string) => {
    const handle = PerformanceManager.createInteractionHandle(name);
    
    return () => {
      PerformanceManager.clearInteractionHandle(handle, name);
    };
  }, []);
  
  return {
    interactionsComplete,
    createInteraction,
    runAfterInteractions: PerformanceManager.runAfterInteractions,
  };
};

export const useRenderOptimization = (componentName: string) => {
  const renderCount = useRef(0);
  const lastRenderTime = useRef(Date.now());
  const [isSlowRendering, setIsSlowRendering] = useState(false);
  
  useEffect(() => {
    renderCount.current += 1;
    const now = Date.now();
    const renderDuration = now - lastRenderTime.current;
    lastRenderTime.current = now;
    
    // Flag as slow if render takes longer than one frame (16.67ms at 60fps)
    const isSlow = renderDuration > 16.67;
    setIsSlowRendering(isSlow);
    
    if (isSlow) {
      console.warn(`[Performance] Slow render in ${componentName}: ${renderDuration}ms (render #${renderCount.current})`);
    }
  });
  
  return {
    renderCount: renderCount.current,
    isSlowRendering,
    shouldOptimize: renderCount.current > 10 && isSlowRendering,
  };
};

export const useLazyLoading = <T>(
  loadFn: () => Promise<T>,
  deps: React.DependencyList = [],
  immediate = true
) => {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  
  const load = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const result = await PerformanceManager.runAfterInteractions(loadFn);
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Unknown error'));
    } finally {
      setLoading(false);
    }
  }, deps);
  
  useEffect(() => {
    if (immediate) {
      load();
    }
  }, [load, immediate]);
  
  return {
    data,
    loading,
    error,
    reload: load,
  };
};

export const useImagePreloader = (imageUrls: string[]) => {
  const [preloaded, setPreloaded] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(false);
  
  const preloadImages = useCallback(async (urls: string[]) => {
    setLoading(true);
    
    try {
      const { preloadImages: preload } = require('../utils/performance');
      await preload(urls);
      setPreloaded(new Set(urls));
    } catch (error) {
      console.warn('Error preloading images:', error);
    } finally {
      setLoading(false);
    }
  }, []);
  
  useEffect(() => {
    if (imageUrls.length > 0) {
      const unloadedUrls = imageUrls.filter(url => !preloaded.has(url));
      if (unloadedUrls.length > 0) {
        preloadImages(unloadedUrls);
      }
    }
  }, [imageUrls, preloaded, preloadImages]);
  
  return {
    preloaded,
    loading,
    isImagePreloaded: (url: string) => preloaded.has(url),
  };
};

export const useMemoryOptimization = () => {
  const clearCaches = useCallback(() => {
    MemoryManager.clearImageCache();
    MemoryManager.clearComponentCache();
  }, []);
  
  const handleMemoryPressure = useCallback(() => {
    console.log('[Performance] Handling memory pressure');
    clearCaches();
    // Force garbage collection if available
    if (global.gc) {
      global.gc();
    }
  }, [clearCaches]);
  
  useMemoryWarning(handleMemoryPressure);
  
  return {
    clearCaches,
    handleMemoryPressure,
  };
};

export const useBatchedUpdates = <T>(
  initialValue: T,
  batchSize: number = 10,
  delay: number = 16
) => {
  const [value, setValue] = useState<T>(initialValue);
  const pendingUpdates = useRef<((prev: T) => T)[]>([]);
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);
  
  const batchedSetValue = useCallback((updater: (prev: T) => T) => {
    pendingUpdates.current.push(updater);
    
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }
    
    timeoutRef.current = setTimeout(() => {
      setValue(prevValue => {
        let newValue = prevValue;
        pendingUpdates.current.forEach(update => {
          newValue = update(newValue);
        });
        pendingUpdates.current = [];
        return newValue;
      });
    }, delay);
  }, [delay]);
  
  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);
  
  return [value, batchedSetValue] as const;
};