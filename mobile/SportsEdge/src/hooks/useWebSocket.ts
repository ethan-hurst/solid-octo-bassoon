/**
 * Custom hook for WebSocket functionality
 */
import { useEffect, useState, useCallback } from 'react';
import { useSelector } from 'react-redux';
import { webSocketService, WebSocketEvents } from '../services/websocketService';
import { RootState } from '../store';

interface UseWebSocketOptions {
  autoConnect?: boolean;
  autoReconnect?: boolean;
}

interface UseWebSocketReturn {
  isConnected: boolean;
  isAuthenticated: boolean;
  connectionStatus: 'disconnected' | 'connecting' | 'connected';
  connect: () => Promise<void>;
  disconnect: () => void;
  emit: (event: string, data?: any) => void;
  joinRoom: (room: string) => void;
  leaveRoom: (room: string) => void;
  reconnect: () => void;
}

export const useWebSocket = (options: UseWebSocketOptions = {}): UseWebSocketReturn => {
  const { autoConnect = true, autoReconnect = true } = options;
  
  const [isConnected, setIsConnected] = useState(false);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<'disconnected' | 'connecting' | 'connected'>('disconnected');
  
  const { isAuthenticated: userAuthenticated } = useSelector((state: RootState) => state.auth);

  // Update connection status
  const updateStatus = useCallback(() => {
    setIsConnected(webSocketService.isConnected());
    setIsAuthenticated(webSocketService.isAuth());
    setConnectionStatus(webSocketService.getConnectionStatus());
  }, []);

  // Connect to WebSocket
  const connect = useCallback(async () => {
    if (!userAuthenticated) {
      console.log('User not authenticated, skipping WebSocket connection');
      return;
    }
    
    try {
      await webSocketService.connect();
      updateStatus();
    } catch (error) {
      console.error('Failed to connect WebSocket:', error);
    }
  }, [userAuthenticated, updateStatus]);

  // Disconnect from WebSocket
  const disconnect = useCallback(() => {
    webSocketService.disconnect();
    updateStatus();
  }, [updateStatus]);

  // Emit event
  const emit = useCallback((event: string, data?: any) => {
    webSocketService.emit(event, data);
  }, []);

  // Join room
  const joinRoom = useCallback((room: string) => {
    webSocketService.joinRoom(room);
  }, []);

  // Leave room
  const leaveRoom = useCallback((room: string) => {
    webSocketService.leaveRoom(room);
  }, []);

  // Reconnect
  const reconnect = useCallback(() => {
    webSocketService.reconnect();
    updateStatus();
  }, [updateStatus]);

  // Auto-connect when component mounts and user is authenticated
  useEffect(() => {
    if (autoConnect && userAuthenticated && !isConnected) {
      connect();
    }
  }, [autoConnect, userAuthenticated, isConnected, connect]);

  // Disconnect when user logs out
  useEffect(() => {
    if (!userAuthenticated && isConnected) {
      disconnect();
    }
  }, [userAuthenticated, isConnected, disconnect]);

  // Update status when WebSocket state changes
  useEffect(() => {
    const interval = setInterval(updateStatus, 1000);
    return () => clearInterval(interval);
  }, [updateStatus]);

  // Auto-reconnect on app focus (if supported)
  useEffect(() => {
    const handleAppStateChange = (nextAppState: string) => {
      if (nextAppState === 'active' && autoReconnect && userAuthenticated && !isConnected) {
        connect();
      }
    };

    // Note: This would need react-native AppState in a real implementation
    // AppState.addEventListener('change', handleAppStateChange);
    // return () => AppState.removeEventListener('change', handleAppStateChange);
  }, [autoReconnect, userAuthenticated, isConnected, connect]);

  return {
    isConnected,
    isAuthenticated,
    connectionStatus,
    connect,
    disconnect,
    emit,
    joinRoom,
    leaveRoom,
    reconnect,
  };
};

/**
 * Hook for listening to specific WebSocket events
 */
export const useWebSocketEvent = (
  event: WebSocketEvents | string,
  handler: (data: any) => void,
  deps: any[] = []
): void => {
  useEffect(() => {
    const socket = (webSocketService as any).socket;
    
    if (socket) {
      socket.on(event, handler);
      
      return () => {
        socket.off(event, handler);
      };
    }
  }, [event, ...deps]);
};

/**
 * Hook for managing room subscriptions
 */
export const useWebSocketRoom = (
  roomName: string,
  shouldJoin: boolean = true
): {
  joinRoom: () => void;
  leaveRoom: () => void;
  isInRoom: boolean;
} => {
  const [isInRoom, setIsInRoom] = useState(false);
  const { isConnected, isAuthenticated } = useWebSocket({ autoConnect: false });

  const joinRoom = useCallback(() => {
    if (isConnected && isAuthenticated) {
      webSocketService.joinRoom(roomName);
      setIsInRoom(true);
    }
  }, [isConnected, isAuthenticated, roomName]);

  const leaveRoom = useCallback(() => {
    if (isConnected) {
      webSocketService.leaveRoom(roomName);
      setIsInRoom(false);
    }
  }, [isConnected, roomName]);

  // Auto-join/leave room based on conditions
  useEffect(() => {
    if (shouldJoin && isConnected && isAuthenticated && !isInRoom) {
      joinRoom();
    } else if (!shouldJoin && isInRoom) {
      leaveRoom();
    }
  }, [shouldJoin, isConnected, isAuthenticated, isInRoom, joinRoom, leaveRoom]);

  // Leave room on cleanup
  useEffect(() => {
    return () => {
      if (isInRoom) {
        leaveRoom();
      }
    };
  }, []);

  return {
    joinRoom,
    leaveRoom,
    isInRoom,
  };
};

/**
 * Hook for real-time value bets updates
 */
export const useValueBetsWebSocket = () => {
  const { isConnected } = useWebSocket();
  
  useWebSocketEvent(WebSocketEvents.NEW_VALUE_BET, (valueBet) => {
    console.log('Real-time value bet update:', valueBet);
  });

  useWebSocketEvent(WebSocketEvents.VALUE_BET_UPDATE, (update) => {
    console.log('Value bet updated:', update);
  });

  useWebSocketEvent(WebSocketEvents.VALUE_BET_REMOVED, (betId) => {
    console.log('Value bet removed:', betId);
  });

  return { isConnected };
};

/**
 * Hook for real-time live games updates
 */
export const useLiveGamesWebSocket = () => {
  const { isConnected } = useWebSocket();
  
  useWebSocketEvent(WebSocketEvents.GAME_UPDATE, (update) => {
    console.log('Live game update:', update);
  });

  useWebSocketEvent(WebSocketEvents.GAME_STARTED, (game) => {
    console.log('Game started:', game);
  });

  useWebSocketEvent(WebSocketEvents.ODDS_UPDATE, (oddsUpdate) => {
    console.log('Odds update:', oddsUpdate);
  });

  return { isConnected };
};

/**
 * Hook for real-time social updates
 */
export const useSocialWebSocket = () => {
  const { isConnected } = useWebSocket();
  
  useWebSocketEvent(WebSocketEvents.NEW_POST, (post) => {
    console.log('New social post:', post);
  });

  useWebSocketEvent(WebSocketEvents.NEW_FOLLOWER, (follower) => {
    console.log('New follower:', follower);
  });

  useWebSocketEvent(WebSocketEvents.COPY_TRADE_UPDATE, (update) => {
    console.log('Copy trade update:', update);
  });

  return { isConnected };
};