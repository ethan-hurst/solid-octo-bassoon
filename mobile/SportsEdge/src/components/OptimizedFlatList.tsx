/**
 * Optimized FlatList Component - High-performance list with virtualization
 */
import React, { useCallback, useMemo, useState } from 'react';
import {
  FlatList,
  FlatListProps,
  ViewToken,
  ListRenderItem,
  RefreshControl,
} from 'react-native';
import { useSelector } from 'react-redux';

import { RootState } from '../store';
import { PerformanceManager } from '../utils/performance';
import LoadingSpinner from './LoadingSpinner';

interface OptimizedFlatListProps<T> extends Omit<FlatListProps<T>, 'renderItem'> {
  data: T[];
  renderItem: ListRenderItem<T>;
  loading?: boolean;
  onRefresh?: () => void;
  refreshing?: boolean;
  estimatedItemSize?: number;
  cacheItemHeight?: boolean;
  onEndReachedThreshold?: number;
  onEndReached?: () => void;
  keyExtractor?: (item: T, index: number) => string;
  windowSize?: number;
  maxToRenderPerBatch?: number;
  updateCellsBatchingPeriod?: number;
  removeClippedSubviews?: boolean;
  getItemLayout?: (data: T[] | null | undefined, index: number) => {
    length: number;
    offset: number;
    index: number;
  };
}

function OptimizedFlatList<T>({
  data,
  renderItem,
  loading = false,
  onRefresh,
  refreshing = false,
  estimatedItemSize = 100,
  cacheItemHeight = true,
  onEndReachedThreshold = 0.1,
  onEndReached,
  keyExtractor,
  windowSize = 10,
  maxToRenderPerBatch = 10,
  updateCellsBatchingPeriod = 50,
  removeClippedSubviews = true,
  getItemLayout,
  ...props
}: OptimizedFlatListProps<T>) {
  const theme = useSelector((state: RootState) => state.userPreferences.theme);
  const [viewableItems, setViewableItems] = useState<Set<string>>(new Set());
  const itemHeightCache = useMemo(() => new Map<string, number>(), []);

  const isDark = theme.theme === 'dark' || 
    (theme.theme === 'auto' && new Date().getHours() > 18);

  const colors = {
    background: isDark ? '#0F172A' : '#FFFFFF',
    text: isDark ? '#F1F5F9' : '#1E293B',
  };

  // Optimize key extraction
  const optimizedKeyExtractor = useCallback((item: T, index: number): string => {
    if (keyExtractor) {
      return keyExtractor(item, index);
    }
    
    // Try to use id field if available
    if (typeof item === 'object' && item !== null && 'id' in item) {
      return String((item as any).id);
    }
    
    return String(index);
  }, [keyExtractor]);

  // Optimize item layout calculation
  const optimizedGetItemLayout = useCallback((
    data: T[] | null | undefined,
    index: number
  ) => {
    if (getItemLayout) {
      return getItemLayout(data, index);
    }

    if (cacheItemHeight && data) {
      const key = optimizedKeyExtractor(data[index], index);
      const cachedHeight = itemHeightCache.get(key);
      
      if (cachedHeight) {
        return {
          length: cachedHeight,
          offset: cachedHeight * index,
          index,
        };
      }
    }

    return {
      length: estimatedItemSize,
      offset: estimatedItemSize * index,
      index,
    };
  }, [getItemLayout, cacheItemHeight, estimatedItemSize, optimizedKeyExtractor, itemHeightCache]);

  // Track viewable items for performance monitoring
  const onViewableItemsChanged = useCallback((info: {
    viewableItems: ViewToken[];
    changed: ViewToken[];
  }) => {
    const newViewableItems = new Set(
      info.viewableItems.map(item => optimizedKeyExtractor(item.item, item.index || 0))
    );
    setViewableItems(newViewableItems);

    // Track performance metrics
    if (info.changed.length > 0) {
      PerformanceManager.startMeasurement('list_viewability_change');
      PerformanceManager.endMeasurement('list_viewability_change');
    }
  }, [optimizedKeyExtractor]);

  const viewabilityConfig = useMemo(() => ({
    waitForInteraction: true,
    viewAreaCoveragePercentThreshold: 50,
    minimumViewTime: 250,
  }), []);

  // Optimized render item with memoization
  const optimizedRenderItem = useCallback<ListRenderItem<T>>(({ item, index }) => {
    const key = optimizedKeyExtractor(item, index);
    const isViewable = viewableItems.has(key);
    
    // Performance tracking for item rendering
    PerformanceManager.startMeasurement(`list_item_render_${key}`);
    
    const renderedItem = renderItem({ 
      item, 
      index, 
      separators: {
        highlight: () => {},
        unhighlight: () => {},
        updateProps: () => {},
      }
    });
    
    PerformanceManager.endMeasurement(`list_item_render_${key}`);
    
    return renderedItem;
  }, [renderItem, optimizedKeyExtractor, viewableItems]);

  // Optimized refresh control
  const refreshControl = useMemo(() => {
    if (!onRefresh) return undefined;
    
    return (
      <RefreshControl
        refreshing={refreshing}
        onRefresh={onRefresh}
        tintColor={colors.text}
        colors={[colors.text]}
        progressBackgroundColor={colors.background}
      />
    );
  }, [onRefresh, refreshing, colors]);

  // Handle end reached with debouncing
  const handleEndReached = useCallback(() => {
    if (onEndReached && !loading) {
      PerformanceManager.runAfterInteractions(() => {
        onEndReached();
      });
    }
  }, [onEndReached, loading]);

  // Show loading spinner for initial load
  if (loading && data.length === 0) {
    return (
      <LoadingSpinner
        size="large"
        text="Loading..."
        overlay={false}
        visible={true}
      />
    );
  }

  return (
    <FlatList
      data={data}
      renderItem={optimizedRenderItem}
      keyExtractor={optimizedKeyExtractor}
      getItemLayout={optimizedGetItemLayout}
      onViewableItemsChanged={onViewableItemsChanged}
      viewabilityConfig={viewabilityConfig}
      refreshControl={refreshControl}
      onEndReached={handleEndReached}
      onEndReachedThreshold={onEndReachedThreshold}
      
      // Performance optimizations
      windowSize={windowSize}
      maxToRenderPerBatch={maxToRenderPerBatch}
      updateCellsBatchingPeriod={updateCellsBatchingPeriod}
      removeClippedSubviews={removeClippedSubviews}
      initialNumToRender={10}
      
      // Memory optimizations
      disableVirtualization={false}
      legacyImplementation={false}
      
      // Additional props
      {...props}
    />
  );
}

export default React.memo(OptimizedFlatList) as <T>(
  props: OptimizedFlatListProps<T>
) => React.ReactElement;