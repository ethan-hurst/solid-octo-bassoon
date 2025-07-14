/**
 * Offline Storage Service using AsyncStorage and SQLite
 */
import AsyncStorage from '@react-native-async-storage/async-storage';
import SQLite from 'react-native-sqlite-storage';
import { store } from '../store';
import { updateCachedData, addPendingAction } from '../store/slices/offlineSlice';

// Enable promise-based SQLite
SQLite.enablePromise(true);

interface DatabaseSchema {
  value_bets: {
    id: string;
    data: string; // JSON string
    created_at: number;
    expires_at?: number;
  };
  live_games: {
    id: string;
    data: string; // JSON string
    created_at: number;
    updated_at: number;
  };
  user_data: {
    key: string;
    value: string; // JSON string
    updated_at: number;
  };
  pending_actions: {
    id: string;
    type: string;
    payload: string; // JSON string
    created_at: number;
    retry_count: number;
  };
  analytics_events: {
    id: string;
    event_type: string;
    data: string; // JSON string
    created_at: number;
    synced: number; // 0 or 1
  };
}

class OfflineService {
  private db: SQLite.SQLiteDatabase | null = null;
  private isInitialized = false;

  /**
   * Initialize the offline storage service
   */
  async initialize(): Promise<void> {
    try {
      if (this.isInitialized) {
        console.log('Offline service already initialized');
        return;
      }

      // Open SQLite database
      this.db = await SQLite.openDatabase({
        name: 'SportsEdge.db',
        location: 'default',
        createFromLocation: '~SportsEdge.db',
      });

      console.log('SQLite database opened successfully');

      // Create tables
      await this.createTables();

      // Clean old data
      await this.cleanOldData();

      this.isInitialized = true;
      console.log('Offline service initialized successfully');
    } catch (error) {
      console.error('Error initializing offline service:', error);
      throw error;
    }
  }

  /**
   * Create database tables
   */
  private async createTables(): Promise<void> {
    if (!this.db) throw new Error('Database not initialized');

    const createTableQueries = [
      `CREATE TABLE IF NOT EXISTS value_bets (
        id TEXT PRIMARY KEY,
        data TEXT NOT NULL,
        created_at INTEGER NOT NULL,
        expires_at INTEGER
      )`,
      `CREATE TABLE IF NOT EXISTS live_games (
        id TEXT PRIMARY KEY,
        data TEXT NOT NULL,
        created_at INTEGER NOT NULL,
        updated_at INTEGER NOT NULL
      )`,
      `CREATE TABLE IF NOT EXISTS user_data (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL,
        updated_at INTEGER NOT NULL
      )`,
      `CREATE TABLE IF NOT EXISTS pending_actions (
        id TEXT PRIMARY KEY,
        type TEXT NOT NULL,
        payload TEXT NOT NULL,
        created_at INTEGER NOT NULL,
        retry_count INTEGER DEFAULT 0
      )`,
      `CREATE TABLE IF NOT EXISTS analytics_events (
        id TEXT PRIMARY KEY,
        event_type TEXT NOT NULL,
        data TEXT NOT NULL,
        created_at INTEGER NOT NULL,
        synced INTEGER DEFAULT 0
      )`,
    ];

    for (const query of createTableQueries) {
      await this.db.executeSql(query);
    }

    // Create indexes for better performance
    const indexQueries = [
      'CREATE INDEX IF NOT EXISTS idx_value_bets_created_at ON value_bets(created_at)',
      'CREATE INDEX IF NOT EXISTS idx_value_bets_expires_at ON value_bets(expires_at)',
      'CREATE INDEX IF NOT EXISTS idx_live_games_updated_at ON live_games(updated_at)',
      'CREATE INDEX IF NOT EXISTS idx_pending_actions_created_at ON pending_actions(created_at)',
      'CREATE INDEX IF NOT EXISTS idx_analytics_events_synced ON analytics_events(synced)',
    ];

    for (const query of indexQueries) {
      await this.db.executeSql(query);
    }
  }

  /**
   * Clean old data to prevent database bloat
   */
  private async cleanOldData(): Promise<void> {
    if (!this.db) return;

    const now = Date.now();
    const oneDayAgo = now - (24 * 60 * 60 * 1000);
    const oneWeekAgo = now - (7 * 24 * 60 * 60 * 1000);

    try {
      // Remove expired value bets
      await this.db.executeSql(
        'DELETE FROM value_bets WHERE expires_at IS NOT NULL AND expires_at < ?',
        [now]
      );

      // Remove old value bets (older than 1 day)
      await this.db.executeSql(
        'DELETE FROM value_bets WHERE created_at < ?',
        [oneDayAgo]
      );

      // Remove old live games (older than 1 day)
      await this.db.executeSql(
        'DELETE FROM live_games WHERE updated_at < ?',
        [oneDayAgo]
      );

      // Remove old pending actions (older than 1 week)
      await this.db.executeSql(
        'DELETE FROM pending_actions WHERE created_at < ?',
        [oneWeekAgo]
      );

      // Remove synced analytics events (older than 1 week)
      await this.db.executeSql(
        'DELETE FROM analytics_events WHERE synced = 1 AND created_at < ?',
        [oneWeekAgo]
      );

      console.log('Old data cleaned successfully');
    } catch (error) {
      console.error('Error cleaning old data:', error);
    }
  }

  /**
   * Store value bets offline
   */
  async storeValueBets(valueBets: any[]): Promise<void> {
    if (!this.db) throw new Error('Database not initialized');

    try {
      await this.db.transaction(async (tx) => {
        for (const bet of valueBets) {
          await tx.executeSql(
            'INSERT OR REPLACE INTO value_bets (id, data, created_at, expires_at) VALUES (?, ?, ?, ?)',
            [
              bet.id,
              JSON.stringify(bet),
              Date.now(),
              bet.expires_at ? new Date(bet.expires_at).getTime() : null,
            ]
          );
        }
      });

      // Update Redux cache
      store.dispatch(updateCachedData({ key: 'valueBets', data: valueBets }));
      
      console.log(`Stored ${valueBets.length} value bets offline`);
    } catch (error) {
      console.error('Error storing value bets:', error);
      throw error;
    }
  }

  /**
   * Get cached value bets
   */
  async getCachedValueBets(): Promise<any[]> {
    if (!this.db) throw new Error('Database not initialized');

    try {
      const [results] = await this.db.executeSql(
        'SELECT data FROM value_bets WHERE expires_at IS NULL OR expires_at > ? ORDER BY created_at DESC',
        [Date.now()]
      );

      const valueBets = [];
      for (let i = 0; i < results.rows.length; i++) {
        const row = results.rows.item(i);
        valueBets.push(JSON.parse(row.data));
      }

      return valueBets;
    } catch (error) {
      console.error('Error getting cached value bets:', error);
      return [];
    }
  }

  /**
   * Store live games offline
   */
  async storeLiveGames(liveGames: any[]): Promise<void> {
    if (!this.db) throw new Error('Database not initialized');

    try {
      const now = Date.now();
      
      await this.db.transaction(async (tx) => {
        for (const game of liveGames) {
          await tx.executeSql(
            'INSERT OR REPLACE INTO live_games (id, data, created_at, updated_at) VALUES (?, ?, ?, ?)',
            [
              game.id,
              JSON.stringify(game),
              game.created_at ? new Date(game.created_at).getTime() : now,
              now,
            ]
          );
        }
      });

      // Update Redux cache
      store.dispatch(updateCachedData({ key: 'liveGames', data: liveGames }));
      
      console.log(`Stored ${liveGames.length} live games offline`);
    } catch (error) {
      console.error('Error storing live games:', error);
      throw error;
    }
  }

  /**
   * Get cached live games
   */
  async getCachedLiveGames(): Promise<any[]> {
    if (!this.db) throw new Error('Database not initialized');

    try {
      const [results] = await this.db.executeSql(
        'SELECT data FROM live_games ORDER BY updated_at DESC',
        []
      );

      const liveGames = [];
      for (let i = 0; i < results.rows.length; i++) {
        const row = results.rows.item(i);
        liveGames.push(JSON.parse(row.data));
      }

      return liveGames;
    } catch (error) {
      console.error('Error getting cached live games:', error);
      return [];
    }
  }

  /**
   * Store user data
   */
  async storeUserData(key: string, data: any): Promise<void> {
    if (!this.db) throw new Error('Database not initialized');

    try {
      await this.db.executeSql(
        'INSERT OR REPLACE INTO user_data (key, value, updated_at) VALUES (?, ?, ?)',
        [key, JSON.stringify(data), Date.now()]
      );

      // Also store in AsyncStorage for quick access
      await AsyncStorage.setItem(`user_data_${key}`, JSON.stringify(data));
      
      console.log(`Stored user data: ${key}`);
    } catch (error) {
      console.error('Error storing user data:', error);
      throw error;
    }
  }

  /**
   * Get user data
   */
  async getUserData(key: string): Promise<any | null> {
    try {
      // Try AsyncStorage first for quick access
      const cachedData = await AsyncStorage.getItem(`user_data_${key}`);
      if (cachedData) {
        return JSON.parse(cachedData);
      }

      // Fallback to SQLite
      if (!this.db) throw new Error('Database not initialized');

      const [results] = await this.db.executeSql(
        'SELECT value FROM user_data WHERE key = ?',
        [key]
      );

      if (results.rows.length > 0) {
        const data = JSON.parse(results.rows.item(0).value);
        // Cache in AsyncStorage for next time
        await AsyncStorage.setItem(`user_data_${key}`, JSON.stringify(data));
        return data;
      }

      return null;
    } catch (error) {
      console.error('Error getting user data:', error);
      return null;
    }
  }

  /**
   * Add pending action for later sync
   */
  async addPendingAction(type: string, payload: any): Promise<void> {
    if (!this.db) throw new Error('Database not initialized');

    try {
      const actionId = `${type}_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
      
      await this.db.executeSql(
        'INSERT INTO pending_actions (id, type, payload, created_at) VALUES (?, ?, ?, ?)',
        [actionId, type, JSON.stringify(payload), Date.now()]
      );

      // Update Redux store
      store.dispatch(addPendingAction({ type, payload }));
      
      console.log(`Added pending action: ${type}`);
    } catch (error) {
      console.error('Error adding pending action:', error);
      throw error;
    }
  }

  /**
   * Get pending actions
   */
  async getPendingActions(): Promise<any[]> {
    if (!this.db) throw new Error('Database not initialized');

    try {
      const [results] = await this.db.executeSql(
        'SELECT * FROM pending_actions ORDER BY created_at ASC',
        []
      );

      const actions = [];
      for (let i = 0; i < results.rows.length; i++) {
        const row = results.rows.item(i);
        actions.push({
          id: row.id,
          type: row.type,
          payload: JSON.parse(row.payload),
          created_at: row.created_at,
          retry_count: row.retry_count,
        });
      }

      return actions;
    } catch (error) {
      console.error('Error getting pending actions:', error);
      return [];
    }
  }

  /**
   * Remove pending action after successful sync
   */
  async removePendingAction(actionId: string): Promise<void> {
    if (!this.db) throw new Error('Database not initialized');

    try {
      await this.db.executeSql(
        'DELETE FROM pending_actions WHERE id = ?',
        [actionId]
      );

      console.log(`Removed pending action: ${actionId}`);
    } catch (error) {
      console.error('Error removing pending action:', error);
      throw error;
    }
  }

  /**
   * Increment retry count for pending action
   */
  async incrementRetryCount(actionId: string): Promise<void> {
    if (!this.db) throw new Error('Database not initialized');

    try {
      await this.db.executeSql(
        'UPDATE pending_actions SET retry_count = retry_count + 1 WHERE id = ?',
        [actionId]
      );

      console.log(`Incremented retry count for action: ${actionId}`);
    } catch (error) {
      console.error('Error incrementing retry count:', error);
      throw error;
    }
  }

  /**
   * Store analytics event for later sync
   */
  async storeAnalyticsEvent(eventType: string, data: any): Promise<void> {
    if (!this.db) throw new Error('Database not initialized');

    try {
      const eventId = `${eventType}_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
      
      await this.db.executeSql(
        'INSERT INTO analytics_events (id, event_type, data, created_at) VALUES (?, ?, ?, ?)',
        [eventId, eventType, JSON.stringify(data), Date.now()]
      );

      console.log(`Stored analytics event: ${eventType}`);
    } catch (error) {
      console.error('Error storing analytics event:', error);
      throw error;
    }
  }

  /**
   * Get unsynced analytics events
   */
  async getUnsyncedAnalyticsEvents(): Promise<any[]> {
    if (!this.db) throw new Error('Database not initialized');

    try {
      const [results] = await this.db.executeSql(
        'SELECT * FROM analytics_events WHERE synced = 0 ORDER BY created_at ASC LIMIT 100',
        []
      );

      const events = [];
      for (let i = 0; i < results.rows.length; i++) {
        const row = results.rows.item(i);
        events.push({
          id: row.id,
          event_type: row.event_type,
          data: JSON.parse(row.data),
          created_at: row.created_at,
        });
      }

      return events;
    } catch (error) {
      console.error('Error getting unsynced analytics events:', error);
      return [];
    }
  }

  /**
   * Mark analytics events as synced
   */
  async markAnalyticsEventsSynced(eventIds: string[]): Promise<void> {
    if (!this.db) throw new Error('Database not initialized');

    try {
      const placeholders = eventIds.map(() => '?').join(',');
      await this.db.executeSql(
        `UPDATE analytics_events SET synced = 1 WHERE id IN (${placeholders})`,
        eventIds
      );

      console.log(`Marked ${eventIds.length} analytics events as synced`);
    } catch (error) {
      console.error('Error marking analytics events as synced:', error);
      throw error;
    }
  }

  /**
   * Get storage statistics
   */
  async getStorageStats(): Promise<any> {
    if (!this.db) throw new Error('Database not initialized');

    try {
      const tables = ['value_bets', 'live_games', 'user_data', 'pending_actions', 'analytics_events'];
      const stats: any = {};

      for (const table of tables) {
        const [results] = await this.db.executeSql(
          `SELECT COUNT(*) as count FROM ${table}`,
          []
        );
        stats[table] = results.rows.item(0).count;
      }

      // Get database size (approximate)
      const [sizeResults] = await this.db.executeSql(
        'PRAGMA page_count',
        []
      );
      const [pageSizeResults] = await this.db.executeSql(
        'PRAGMA page_size',
        []
      );
      
      const pageCount = sizeResults.rows.item(0).page_count;
      const pageSize = pageSizeResults.rows.item(0).page_size;
      stats.database_size_bytes = pageCount * pageSize;
      stats.database_size_mb = (stats.database_size_bytes / (1024 * 1024)).toFixed(2);

      return stats;
    } catch (error) {
      console.error('Error getting storage stats:', error);
      return {};
    }
  }

  /**
   * Clear all offline data
   */
  async clearAllData(): Promise<void> {
    if (!this.db) throw new Error('Database not initialized');

    try {
      const tables = ['value_bets', 'live_games', 'user_data', 'pending_actions', 'analytics_events'];
      
      for (const table of tables) {
        await this.db.executeSql(`DELETE FROM ${table}`, []);
      }

      // Clear AsyncStorage cache
      const keys = await AsyncStorage.getAllKeys();
      const userDataKeys = keys.filter(key => key.startsWith('user_data_'));
      if (userDataKeys.length > 0) {
        await AsyncStorage.multiRemove(userDataKeys);
      }

      console.log('All offline data cleared');
    } catch (error) {
      console.error('Error clearing offline data:', error);
      throw error;
    }
  }

  /**
   * Close database connection
   */
  async close(): Promise<void> {
    if (this.db) {
      await this.db.close();
      this.db = null;
      this.isInitialized = false;
      console.log('Database connection closed');
    }
  }

  /**
   * Check if service is initialized
   */
  isServiceInitialized(): boolean {
    return this.isInitialized;
  }
}

// Create and export singleton instance
export const offlineService = new OfflineService();