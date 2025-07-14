/**
 * API Client service for Sports Edge mobile app
 */
import axios, { AxiosInstance, AxiosRequestConfig } from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { store } from '../store';
import { logout } from '../store/slices/authSlice';
import { setOnlineStatus } from '../store/slices/offlineSlice';

// API Configuration
const API_BASE_URL = __DEV__ 
  ? 'http://localhost:8000/api/v1' 
  : 'https://api.sportsedge.app/api/v1';

const API_TIMEOUT = 10000; // 10 seconds

class ApiClient {
  private client: AxiosInstance;
  private requestQueue: Array<() => Promise<any>> = [];
  private isRefreshing = false;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: API_TIMEOUT,
      headers: {
        'Content-Type': 'application/json',
        'User-Agent': 'SportsEdge-Mobile/1.0',
      },
    });

    this.setupInterceptors();
  }

  private setupInterceptors() {
    // Request interceptor - Add auth token
    this.client.interceptors.request.use(
      async (config) => {
        const token = await AsyncStorage.getItem('authToken');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // Response interceptor - Handle errors and token refresh
    this.client.interceptors.response.use(
      (response) => {
        // Update online status on successful response
        store.dispatch(setOnlineStatus(true));
        return response;
      },
      async (error) => {
        const originalRequest = error.config;

        // Handle network errors
        if (!error.response) {
          store.dispatch(setOnlineStatus(false));
          return Promise.reject({
            message: 'Network error. Please check your connection.',
            isNetworkError: true,
            originalError: error,
          });
        }

        // Handle 401 unauthorized
        if (error.response.status === 401 && !originalRequest._retry) {
          if (this.isRefreshing) {
            // Add request to queue if token refresh is in progress
            return new Promise((resolve) => {
              this.requestQueue.push(() => resolve(this.client(originalRequest)));
            });
          }

          originalRequest._retry = true;
          this.isRefreshing = true;

          try {
            const refreshToken = await AsyncStorage.getItem('refreshToken');
            if (refreshToken) {
              // Attempt to refresh token
              const response = await this.client.post('/auth/refresh', {
                refresh_token: refreshToken,
              });

              const { access_token } = response.data;
              await AsyncStorage.setItem('authToken', access_token);

              // Retry all queued requests
              this.requestQueue.forEach((callback) => callback());
              this.requestQueue = [];

              // Retry original request
              originalRequest.headers.Authorization = `Bearer ${access_token}`;
              return this.client(originalRequest);
            }
          } catch (refreshError) {
            // Refresh failed, logout user
            await AsyncStorage.multiRemove(['authToken', 'refreshToken']);
            store.dispatch(logout());
            return Promise.reject(error);
          } finally {
            this.isRefreshing = false;
          }
        }

        // Handle other HTTP errors
        const errorMessage = this.getErrorMessage(error);
        return Promise.reject({
          message: errorMessage,
          status: error.response.status,
          originalError: error,
        });
      }
    );
  }

  private getErrorMessage(error: any): string {
    if (error.response?.data?.detail) {
      return error.response.data.detail;
    }
    
    if (error.response?.data?.message) {
      return error.response.data.message;
    }

    switch (error.response?.status) {
      case 400:
        return 'Bad request. Please check your input.';
      case 401:
        return 'Unauthorized. Please log in again.';
      case 403:
        return 'Access forbidden.';
      case 404:
        return 'Resource not found.';
      case 429:
        return 'Too many requests. Please try again later.';
      case 500:
        return 'Server error. Please try again later.';
      case 503:
        return 'Service unavailable. Please try again later.';
      default:
        return 'An unexpected error occurred.';
    }
  }

  // Public API methods
  async get<T = any>(url: string, config?: AxiosRequestConfig): Promise<{ data: T }> {
    return this.client.get(url, config);
  }

  async post<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<{ data: T }> {
    return this.client.post(url, data, config);
  }

  async put<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<{ data: T }> {
    return this.client.put(url, data, config);
  }

  async patch<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<{ data: T }> {
    return this.client.patch(url, data, config);
  }

  async delete<T = any>(url: string, config?: AxiosRequestConfig): Promise<{ data: T }> {
    return this.client.delete(url, config);
  }

  // Mobile-specific optimized requests
  async getMobileDashboard() {
    return this.get('/mobile/dashboard');
  }

  async getValueBetsFeed(page = 1, sports?: string[], limit = 20) {
    const params = new URLSearchParams({
      page: page.toString(),
      limit: limit.toString(),
    });

    if (sports && sports.length > 0) {
      sports.forEach(sport => params.append('sports', sport));
    }

    return this.get(`/mobile/value-bets/feed?${params}`);
  }

  async getQuickAnalysis(betId: string) {
    return this.get(`/mobile/quick-analysis/${betId}`);
  }

  async getLiveGames(sports?: string[]) {
    const params = new URLSearchParams();
    if (sports && sports.length > 0) {
      sports.forEach(sport => params.append('sports', sport));
    }

    return this.get(`/mobile/games/live?${params}`);
  }

  async registerDevice(deviceInfo: any) {
    return this.post('/mobile/notifications/register', deviceInfo);
  }

  async quickAddToBetslip(betId: string, action: string, sourceScreen: string) {
    return this.post('/mobile/bets/quick-add', {
      bet_id: betId,
      action,
      source_screen: sourceScreen,
    });
  }

  async getSocialFeed(page = 1, limit = 20) {
    const params = new URLSearchParams({
      page: page.toString(),
      limit: limit.toString(),
    });

    return this.get(`/mobile/social/feed?${params}`);
  }

  // Utility methods
  isNetworkError(error: any): boolean {
    return error.isNetworkError === true;
  }

  getBaseURL(): string {
    return API_BASE_URL;
  }

  setTimeout(timeout: number) {
    this.client.defaults.timeout = timeout;
  }
}

// Create and export singleton instance
export const apiClient = new ApiClient();