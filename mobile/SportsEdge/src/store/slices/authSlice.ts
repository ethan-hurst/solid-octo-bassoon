/**
 * Authentication slice for mobile app
 */
import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { apiClient } from '../../services/apiClient';
import { biometricService } from '../../services/biometricService';

export interface User {
  id: string;
  email: string;
  username: string;
  is_active: boolean;
  sports: string[];
  min_edge: number;
  max_kelly_fraction: number;
  notification_channels: string[];
}

interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  biometricEnabled: boolean;
  isLoading: boolean;
  error: string | null;
}

const initialState: AuthState = {
  user: null,
  token: null,
  isAuthenticated: false,
  biometricEnabled: false,
  isLoading: false,
  error: null,
};

// Async thunks
export const loginWithCredentials = createAsyncThunk(
  'auth/loginWithCredentials',
  async ({ email, password }: { email: string; password: string }, { rejectWithValue }) => {
    try {
      const response = await apiClient.post('/auth/login', { email, password });
      const { access_token, user } = response.data;
      
      // Store token securely
      await AsyncStorage.setItem('authToken', access_token);
      
      return { token: access_token, user };
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.detail || 'Login failed');
    }
  }
);

export const loginWithBiometric = createAsyncThunk(
  'auth/loginWithBiometric',
  async (_, { rejectWithValue }) => {
    try {
      // Check if biometric is available
      const biometricAvailable = await biometricService.isBiometricAvailable();
      if (!biometricAvailable) {
        throw new Error('Biometric authentication not available');
      }

      // Authenticate with biometric
      const biometricResult = await biometricService.authenticate(
        'Authenticate to access Sports Edge',
        'Use your biometric authentication to login'
      );

      if (!biometricResult.success) {
        throw new Error('Biometric authentication failed');
      }

      // Get stored token
      const storedToken = await AsyncStorage.getItem('authToken');
      if (!storedToken) {
        throw new Error('No stored authentication found');
      }

      // Verify token with backend
      const response = await apiClient.get('/auth/verify', {
        headers: { Authorization: `Bearer ${storedToken}` }
      });

      return { token: storedToken, user: response.data };
    } catch (error: any) {
      return rejectWithValue(error.message || 'Biometric login failed');
    }
  }
);

export const logout = createAsyncThunk(
  'auth/logout',
  async (_, { dispatch }) => {
    try {
      // Clear stored token
      await AsyncStorage.removeItem('authToken');
      
      // Clear any biometric data
      await biometricService.clearBiometricData();
      
      return true;
    } catch (error) {
      console.error('Logout error:', error);
      return true; // Still logout even if cleanup fails
    }
  }
);

export const enableBiometric = createAsyncThunk(
  'auth/enableBiometric',
  async (_, { getState, rejectWithValue }) => {
    try {
      const state = getState() as { auth: AuthState };
      const { token } = state.auth;

      if (!token) {
        throw new Error('No authentication token available');
      }

      const biometricAvailable = await biometricService.isBiometricAvailable();
      if (!biometricAvailable) {
        throw new Error('Biometric authentication not available on this device');
      }

      // Store token for biometric access
      await biometricService.storeBiometricCredentials(token);
      
      return true;
    } catch (error: any) {
      return rejectWithValue(error.message || 'Failed to enable biometric authentication');
    }
  }
);

export const checkStoredAuth = createAsyncThunk(
  'auth/checkStoredAuth',
  async (_, { rejectWithValue }) => {
    try {
      const storedToken = await AsyncStorage.getItem('authToken');
      if (!storedToken) {
        return null;
      }

      // Verify token with backend
      const response = await apiClient.get('/auth/verify', {
        headers: { Authorization: `Bearer ${storedToken}` }
      });

      // Check if biometric is enabled
      const biometricEnabled = await biometricService.isBiometricEnabled();

      return { 
        token: storedToken, 
        user: response.data,
        biometricEnabled 
      };
    } catch (error) {
      // Token is invalid, remove it
      await AsyncStorage.removeItem('authToken');
      return null;
    }
  }
);

const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    clearError: (state) => {
      state.error = null;
    },
    updateUser: (state, action: PayloadAction<Partial<User>>) => {
      if (state.user) {
        state.user = { ...state.user, ...action.payload };
      }
    },
  },
  extraReducers: (builder) => {
    builder
      // Login with credentials
      .addCase(loginWithCredentials.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(loginWithCredentials.fulfilled, (state, action) => {
        state.isLoading = false;
        state.isAuthenticated = true;
        state.token = action.payload.token;
        state.user = action.payload.user;
        state.error = null;
      })
      .addCase(loginWithCredentials.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
      })

      // Login with biometric
      .addCase(loginWithBiometric.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(loginWithBiometric.fulfilled, (state, action) => {
        state.isLoading = false;
        state.isAuthenticated = true;
        state.token = action.payload.token;
        state.user = action.payload.user;
        state.biometricEnabled = true;
        state.error = null;
      })
      .addCase(loginWithBiometric.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
      })

      // Logout
      .addCase(logout.fulfilled, (state) => {
        state.user = null;
        state.token = null;
        state.isAuthenticated = false;
        state.biometricEnabled = false;
        state.error = null;
      })

      // Enable biometric
      .addCase(enableBiometric.fulfilled, (state) => {
        state.biometricEnabled = true;
      })
      .addCase(enableBiometric.rejected, (state, action) => {
        state.error = action.payload as string;
      })

      // Check stored auth
      .addCase(checkStoredAuth.pending, (state) => {
        state.isLoading = true;
      })
      .addCase(checkStoredAuth.fulfilled, (state, action) => {
        state.isLoading = false;
        if (action.payload) {
          state.isAuthenticated = true;
          state.token = action.payload.token;
          state.user = action.payload.user;
          state.biometricEnabled = action.payload.biometricEnabled;
        }
      })
      .addCase(checkStoredAuth.rejected, (state) => {
        state.isLoading = false;
      });
  },
});

export const { clearError, updateUser } = authSlice.actions;
export default authSlice.reducer;