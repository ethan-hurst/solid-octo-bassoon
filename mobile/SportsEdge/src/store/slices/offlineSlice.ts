/**
 * Offline functionality slice for mobile app
 */
import { createSlice, PayloadAction } from '@reduxjs/toolkit';

export interface PendingAction {
  id: string;
  type: string;
  payload: any;
  timestamp: number;
  retryCount: number;
}

interface OfflineState {
  isOnline: boolean;
  pendingActions: PendingAction[];
  cachedData: {
    valueBets: any[];
    liveGames: any[];
    userProfile: any;
    lastCacheUpdate: number | null;
  };
  syncInProgress: boolean;
  lastSyncTime: number | null;
}

const initialState: OfflineState = {
  isOnline: true,
  pendingActions: [],
  cachedData: {
    valueBets: [],
    liveGames: [],
    userProfile: null,
    lastCacheUpdate: null,
  },
  syncInProgress: false,
  lastSyncTime: null,
};

const offlineSlice = createSlice({
  name: 'offline',
  initialState,
  reducers: {
    setOnlineStatus: (state, action: PayloadAction<boolean>) => {
      state.isOnline = action.payload;
    },
    
    addPendingAction: (state, action: PayloadAction<Omit<PendingAction, 'id' | 'timestamp' | 'retryCount'>>) => {
      const pendingAction: PendingAction = {
        ...action.payload,
        id: Date.now().toString(),
        timestamp: Date.now(),
        retryCount: 0,
      };
      state.pendingActions.push(pendingAction);
    },
    
    removePendingAction: (state, action: PayloadAction<string>) => {
      state.pendingActions = state.pendingActions.filter(action => action.id !== action.payload);
    },
    
    incrementRetryCount: (state, action: PayloadAction<string>) => {
      const actionToRetry = state.pendingActions.find(a => a.id === action.payload);
      if (actionToRetry) {
        actionToRetry.retryCount += 1;
      }
    },
    
    updateCachedData: (state, action: PayloadAction<{ key: keyof OfflineState['cachedData']; data: any }>) => {
      const { key, data } = action.payload;
      if (key !== 'lastCacheUpdate') {
        (state.cachedData as any)[key] = data;
      }
      state.cachedData.lastCacheUpdate = Date.now();
    },
    
    setSyncInProgress: (state, action: PayloadAction<boolean>) => {
      state.syncInProgress = action.payload;
      if (!action.payload) {
        state.lastSyncTime = Date.now();
      }
    },
    
    clearPendingActions: (state) => {
      state.pendingActions = [];
    },
  },
});

export const {
  setOnlineStatus,
  addPendingAction,
  removePendingAction,
  incrementRetryCount,
  updateCachedData,
  setSyncInProgress,
  clearPendingActions,
} = offlineSlice.actions;

export default offlineSlice.reducer;