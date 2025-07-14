/**
 * Notifications slice for mobile app
 */
import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import { apiClient } from '../../services/apiClient';

export interface MobileNotification {
  id: string;
  title: string;
  body: string;
  type: 'value_bet' | 'game_starting' | 'social' | 'system';
  data?: any;
  read: boolean;
  created_at: string;
}

export interface NotificationSettings {
  value_bet_alerts: boolean;
  game_starting_alerts: boolean;
  social_notifications: boolean;
  system_notifications: boolean;
  min_edge_threshold: number;
  quiet_hours_enabled: boolean;
  quiet_hours_start: string;
  quiet_hours_end: string;
}

interface NotificationsState {
  notifications: MobileNotification[];
  unreadCount: number;
  settings: NotificationSettings;
  isLoading: boolean;
  error: string | null;
  deviceRegistered: boolean;
}

const initialState: NotificationsState = {
  notifications: [],
  unreadCount: 0,
  settings: {
    value_bet_alerts: true,
    game_starting_alerts: true,
    social_notifications: true,
    system_notifications: true,
    min_edge_threshold: 0.05,
    quiet_hours_enabled: false,
    quiet_hours_start: '22:00',
    quiet_hours_end: '08:00',
  },
  isLoading: false,
  error: null,
  deviceRegistered: false,
};

export const registerDevice = createAsyncThunk(
  'notifications/registerDevice',
  async (deviceInfo: any, { rejectWithValue }) => {
    try {
      const response = await apiClient.post('/mobile/notifications/register', deviceInfo);
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.detail || 'Device registration failed');
    }
  }
);

const notificationsSlice = createSlice({
  name: 'notifications',
  initialState,
  reducers: {
    addNotification: (state, action: PayloadAction<MobileNotification>) => {
      state.notifications.unshift(action.payload);
      if (!action.payload.read) {
        state.unreadCount += 1;
      }
    },
    
    markAsRead: (state, action: PayloadAction<string>) => {
      const notification = state.notifications.find(n => n.id === action.payload);
      if (notification && !notification.read) {
        notification.read = true;
        state.unreadCount = Math.max(0, state.unreadCount - 1);
      }
    },
    
    markAllAsRead: (state) => {
      state.notifications.forEach(n => n.read = true);
      state.unreadCount = 0;
    },
    
    updateSettings: (state, action: PayloadAction<Partial<NotificationSettings>>) => {
      state.settings = { ...state.settings, ...action.payload };
    },
    
    clearError: (state) => {
      state.error = null;
    },
  },

  extraReducers: (builder) => {
    builder
      .addCase(registerDevice.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(registerDevice.fulfilled, (state) => {
        state.isLoading = false;
        state.deviceRegistered = true;
      })
      .addCase(registerDevice.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
      });
  },
});

export const { 
  addNotification, 
  markAsRead, 
  markAllAsRead, 
  updateSettings, 
  clearError 
} = notificationsSlice.actions;

export default notificationsSlice.reducer;