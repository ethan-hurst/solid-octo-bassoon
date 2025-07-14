/**
 * WebSocket Service for real-time updates in Sports Edge mobile app
 */
import { io, Socket } from 'socket.io-client';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { store } from '../store';
import { addNotification } from '../store/slices/notificationsSlice';
import { setOnlineStatus } from '../store/slices/offlineSlice';
import { updateValueBets } from '../store/slices/valueBetsSlice';
import { updateLiveGame, addLiveGame } from '../store/slices/liveGamesSlice';

// WebSocket event types
export enum WebSocketEvents {
  // Connection events
  CONNECT = 'connect',
  DISCONNECT = 'disconnect',
  RECONNECT = 'reconnect',
  
  // Authentication events
  AUTHENTICATE = 'authenticate',
  AUTHENTICATED = 'authenticated',
  AUTHENTICATION_ERROR = 'authentication_error',
  
  // Value bet events
  VALUE_BET_UPDATE = 'value_bet_update',
  VALUE_BET_REMOVED = 'value_bet_removed',
  NEW_VALUE_BET = 'new_value_bet',
  
  // Live game events
  GAME_UPDATE = 'game_update',
  GAME_STARTED = 'game_started',
  GAME_ENDED = 'game_ended',
  ODDS_UPDATE = 'odds_update',
  
  // Social events
  NEW_POST = 'new_post',
  POST_LIKED = 'post_liked',
  NEW_FOLLOWER = 'new_follower',
  COPY_TRADE_UPDATE = 'copy_trade_update',
  
  // Notification events
  NEW_NOTIFICATION = 'new_notification',
  NOTIFICATION_READ = 'notification_read',
  
  // System events
  SYSTEM_MAINTENANCE = 'system_maintenance',
  ERROR = 'error',
}

export interface WebSocketConfig {
  url: string;
  autoConnect: boolean;
  reconnection: boolean;
  reconnectionAttempts: number;
  reconnectionDelay: number;
  timeout: number;
}

class WebSocketService {
  private socket: Socket | null = null;
  private config: WebSocketConfig;
  private isAuthenticated = false;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private connectionStatus: 'disconnected' | 'connecting' | 'connected' = 'disconnected';

  constructor() {
    this.config = {
      url: __DEV__ 
        ? 'ws://localhost:8000' 
        : 'wss://api.sportsedge.app',
      autoConnect: false,
      reconnection: true,
      reconnectionAttempts: 5,
      reconnectionDelay: 2000,
      timeout: 10000,
    };
  }

  /**
   * Initialize WebSocket connection
   */
  async connect(): Promise<void> {
    try {
      if (this.socket?.connected) {
        console.log('WebSocket already connected');
        return;
      }

      console.log('Connecting to WebSocket...');
      this.connectionStatus = 'connecting';

      this.socket = io(this.config.url, {
        transports: ['websocket'],
        upgrade: false,
        reconnection: this.config.reconnection,
        reconnectionAttempts: this.config.reconnectionAttempts,
        reconnectionDelay: this.config.reconnectionDelay,
        timeout: this.config.timeout,
      });

      this.setupEventListeners();
      
      // Auto-authenticate if we have a token
      const token = await AsyncStorage.getItem('authToken');
      if (token) {
        this.authenticate(token);
      }

    } catch (error) {
      console.error('WebSocket connection error:', error);
      this.connectionStatus = 'disconnected';
      store.dispatch(setOnlineStatus(false));
    }
  }

  /**
   * Disconnect WebSocket
   */
  disconnect(): void {
    if (this.socket) {
      console.log('Disconnecting WebSocket...');
      this.socket.disconnect();
      this.socket = null;
      this.isAuthenticated = false;
      this.connectionStatus = 'disconnected';
    }
  }

  /**
   * Authenticate with the WebSocket server
   */
  private authenticate(token: string): void {
    if (this.socket && this.socket.connected) {
      console.log('Authenticating WebSocket connection...');
      this.socket.emit(WebSocketEvents.AUTHENTICATE, { token });
    }
  }

  /**
   * Setup event listeners for WebSocket
   */
  private setupEventListeners(): void {
    if (!this.socket) return;

    // Connection events
    this.socket.on(WebSocketEvents.CONNECT, () => {
      console.log('WebSocket connected');
      this.connectionStatus = 'connected';
      this.reconnectAttempts = 0;
      store.dispatch(setOnlineStatus(true));
    });

    this.socket.on(WebSocketEvents.DISCONNECT, (reason) => {
      console.log('WebSocket disconnected:', reason);
      this.connectionStatus = 'disconnected';
      this.isAuthenticated = false;
      store.dispatch(setOnlineStatus(false));
      
      // Attempt reconnection if it wasn't a manual disconnect
      if (reason !== 'io client disconnect' && this.reconnectAttempts < this.maxReconnectAttempts) {
        this.attemptReconnection();
      }
    });

    this.socket.on(WebSocketEvents.RECONNECT, () => {
      console.log('WebSocket reconnected');
      this.connectionStatus = 'connected';
      store.dispatch(setOnlineStatus(true));
    });

    // Authentication events
    this.socket.on(WebSocketEvents.AUTHENTICATED, (data) => {
      console.log('WebSocket authenticated:', data);
      this.isAuthenticated = true;
      this.subscribeToUserChannels();
    });

    this.socket.on(WebSocketEvents.AUTHENTICATION_ERROR, (error) => {
      console.error('WebSocket authentication error:', error);
      this.isAuthenticated = false;
    });

    // Value bet events
    this.socket.on(WebSocketEvents.NEW_VALUE_BET, (valueBet) => {
      console.log('New value bet received:', valueBet);
      store.dispatch(updateValueBets([valueBet]));
      
      // Send notification for high-value bets
      if (valueBet.edge >= 0.05) {
        store.dispatch(addNotification({
          id: `value_bet_${valueBet.id}`,
          title: 'New Value Bet',
          body: `${valueBet.edge * 100}% edge found`,
          type: 'value_bet',
          data: valueBet,
          read: false,
          created_at: new Date().toISOString(),
        }));
      }
    });

    this.socket.on(WebSocketEvents.VALUE_BET_UPDATE, (update) => {
      console.log('Value bet updated:', update);
      store.dispatch(updateValueBets([update]));
    });

    this.socket.on(WebSocketEvents.VALUE_BET_REMOVED, (betId) => {
      console.log('Value bet removed:', betId);
      // TODO: Implement remove value bet action
    });

    // Live game events
    this.socket.on(WebSocketEvents.GAME_STARTED, (game) => {
      console.log('Game started:', game);
      store.dispatch(addLiveGame(game));
      
      store.dispatch(addNotification({
        id: `game_started_${game.id}`,
        title: 'Game Starting',
        body: `${game.home_team} vs ${game.away_team}`,
        type: 'game_starting',
        data: game,
        read: false,
        created_at: new Date().toISOString(),
      }));
    });

    this.socket.on(WebSocketEvents.GAME_UPDATE, (update) => {
      console.log('Game updated:', update);
      store.dispatch(updateLiveGame(update));
    });

    this.socket.on(WebSocketEvents.ODDS_UPDATE, (oddsUpdate) => {
      console.log('Odds updated:', oddsUpdate);
      // TODO: Implement odds update action
    });

    // Social events
    this.socket.on(WebSocketEvents.NEW_POST, (post) => {
      console.log('New social post:', post);
      
      store.dispatch(addNotification({
        id: `social_post_${post.id}`,
        title: 'New Post',
        body: `${post.author.username} shared a bet`,
        type: 'social',
        data: post,
        read: false,
        created_at: new Date().toISOString(),
      }));
    });

    this.socket.on(WebSocketEvents.NEW_FOLLOWER, (follower) => {
      console.log('New follower:', follower);
      
      store.dispatch(addNotification({
        id: `new_follower_${follower.id}`,
        title: 'New Follower',
        body: `${follower.username} started following you`,
        type: 'social',
        data: follower,
        read: false,
        created_at: new Date().toISOString(),
      }));
    });

    // Notification events
    this.socket.on(WebSocketEvents.NEW_NOTIFICATION, (notification) => {
      console.log('New notification received:', notification);
      store.dispatch(addNotification(notification));
    });

    // Error events
    this.socket.on(WebSocketEvents.ERROR, (error) => {
      console.error('WebSocket error:', error);
    });

    this.socket.on('connect_error', (error) => {
      console.error('WebSocket connection error:', error);
      this.connectionStatus = 'disconnected';
      store.dispatch(setOnlineStatus(false));
    });
  }

  /**
   * Subscribe to user-specific channels after authentication
   */
  private subscribeToUserChannels(): void {
    if (!this.socket || !this.isAuthenticated) return;

    // Subscribe to user-specific channels
    this.socket.emit('subscribe', {
      channels: [
        'value_bets',
        'live_games',
        'social_feed',
        'notifications',
        'user_specific',
      ],
    });

    console.log('Subscribed to user channels');
  }

  /**
   * Attempt to reconnect WebSocket
   */
  private attemptReconnection(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.log('Max reconnection attempts reached');
      return;
    }

    this.reconnectAttempts++;
    const delay = this.config.reconnectionDelay * this.reconnectAttempts;
    
    console.log(`Attempting to reconnect in ${delay}ms (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
    
    setTimeout(() => {
      this.connect();
    }, delay);
  }

  /**
   * Send a message through WebSocket
   */
  emit(event: string, data?: any): void {
    if (this.socket && this.socket.connected) {
      this.socket.emit(event, data);
    } else {
      console.warn('Cannot emit event: WebSocket not connected');
    }
  }

  /**
   * Join a specific room/channel
   */
  joinRoom(room: string): void {
    if (this.socket && this.socket.connected && this.isAuthenticated) {
      this.socket.emit('join_room', room);
      console.log(`Joined room: ${room}`);
    }
  }

  /**
   * Leave a specific room/channel
   */
  leaveRoom(room: string): void {
    if (this.socket && this.socket.connected) {
      this.socket.emit('leave_room', room);
      console.log(`Left room: ${room}`);
    }
  }

  /**
   * Get connection status
   */
  getConnectionStatus(): 'disconnected' | 'connecting' | 'connected' {
    return this.connectionStatus;
  }

  /**
   * Check if WebSocket is connected
   */
  isConnected(): boolean {
    return this.socket?.connected || false;
  }

  /**
   * Check if WebSocket is authenticated
   */
  isAuth(): boolean {
    return this.isAuthenticated;
  }

  /**
   * Update WebSocket configuration
   */
  updateConfig(newConfig: Partial<WebSocketConfig>): void {
    this.config = { ...this.config, ...newConfig };
  }

  /**
   * Manually trigger reconnection
   */
  reconnect(): void {
    if (this.socket) {
      this.disconnect();
    }
    setTimeout(() => {
      this.connect();
    }, 1000);
  }
}

// Create and export singleton instance
export const webSocketService = new WebSocketService();