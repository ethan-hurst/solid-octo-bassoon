/**
 * Deep Link Service for Sports Edge mobile app
 */
import { Linking, Alert } from 'react-native';
import { NavigationContainerRef } from '@react-navigation/native';
import AsyncStorage from '@react-native-async-storage/async-storage';

import { store } from '../store';
import { apiClient } from './apiClient';

export interface DeepLinkConfig {
  scheme: string;
  host: string;
  prefixes: string[];
}

export interface DeepLinkData {
  url: string;
  path: string;
  params: Record<string, string>;
  query: Record<string, string>;
}

export interface PendingNavigation {
  route: string;
  params?: any;
  timestamp: number;
}

class DeepLinkService {
  private navigationRef: NavigationContainerRef<any> | null = null;
  private isInitialized = false;
  private pendingNavigation: PendingNavigation | null = null;

  private config: DeepLinkConfig = {
    scheme: 'sportsedge',
    host: 'app.sportsedge.com',
    prefixes: [
      'sportsedge://',
      'https://app.sportsedge.com',
      'https://sportsedge.app',
    ],
  };

  /**
   * Initialize deep link service
   */
  async initialize(navigationRef: NavigationContainerRef<any>): Promise<void> {
    try {
      this.navigationRef = navigationRef;

      // Check if app was opened via deep link
      const initialUrl = await Linking.getInitialURL();
      if (initialUrl) {
        console.log('App opened with initial URL:', initialUrl);
        await this.handleDeepLink(initialUrl);
      }

      // Listen for incoming deep links
      const subscription = Linking.addEventListener('url', (event) => {
        console.log('Deep link received:', event.url);
        this.handleDeepLink(event.url);
      });

      // Process any pending navigation
      await this.processPendingNavigation();

      this.isInitialized = true;
      console.log('Deep link service initialized successfully');

      return () => subscription?.remove();
    } catch (error) {
      console.error('Error initializing deep link service:', error);
    }
  }

  /**
   * Handle incoming deep link
   */
  private async handleDeepLink(url: string): Promise<void> {
    try {
      const linkData = this.parseDeepLink(url);
      if (!linkData) {
        console.warn('Invalid deep link format:', url);
        return;
      }

      console.log('Parsed deep link:', linkData);

      // Track deep link usage
      await this.trackDeepLink(linkData);

      // Check if user is authenticated for protected routes
      const requiresAuth = this.routeRequiresAuth(linkData.path);
      const isAuthenticated = await this.checkAuthentication();

      if (requiresAuth && !isAuthenticated) {
        // Store navigation for after login
        await this.storePendingNavigation(linkData);
        this.navigateToAuth();
        return;
      }

      // Navigate to the appropriate screen
      await this.navigateFromDeepLink(linkData);
    } catch (error) {
      console.error('Error handling deep link:', error);
      Alert.alert('Error', 'Unable to open the requested link');
    }
  }

  /**
   * Parse deep link URL into structured data
   */
  private parseDeepLink(url: string): DeepLinkData | null {
    try {
      const urlObj = new URL(url);
      const path = urlObj.pathname.replace(/^\//, '');
      
      // Parse query parameters
      const query: Record<string, string> = {};
      urlObj.searchParams.forEach((value, key) => {
        query[key] = value;
      });

      // Parse path parameters
      const pathSegments = path.split('/');
      const params: Record<string, string> = {};

      // Extract route parameters based on path structure
      this.extractRouteParams(pathSegments, params);

      return {
        url,
        path,
        params,
        query,
      };
    } catch (error) {
      console.error('Error parsing deep link:', error);
      return null;
    }
  }

  /**
   * Extract route parameters from path segments
   */
  private extractRouteParams(pathSegments: string[], params: Record<string, string>): void {
    // Define route patterns and extract parameters
    const routes = [
      { pattern: ['bet', 'analysis'], paramName: 'betId', paramIndex: 2 },
      { pattern: ['bet', 'details'], paramName: 'betId', paramIndex: 2 },
      { pattern: ['game', 'live'], paramName: 'gameId', paramIndex: 2 },
      { pattern: ['game', 'details'], paramName: 'gameId', paramIndex: 2 },
      { pattern: ['user', 'profile'], paramName: 'userId', paramIndex: 2 },
      { pattern: ['social', 'post'], paramName: 'postId', paramIndex: 2 },
      { pattern: ['tournament'], paramName: 'tournamentId', paramIndex: 1 },
      { pattern: ['referral'], paramName: 'referralCode', paramIndex: 1 },
    ];

    for (const route of routes) {
      if (this.matchesPattern(pathSegments, route.pattern)) {
        if (pathSegments[route.paramIndex]) {
          params[route.paramName] = pathSegments[route.paramIndex];
        }
        break;
      }
    }
  }

  /**
   * Check if path segments match a pattern
   */
  private matchesPattern(segments: string[], pattern: string[]): boolean {
    if (segments.length < pattern.length) return false;
    
    for (let i = 0; i < pattern.length; i++) {
      if (segments[i] !== pattern[i]) return false;
    }
    
    return true;
  }

  /**
   * Navigate based on deep link data
   */
  private async navigateFromDeepLink(linkData: DeepLinkData): Promise<void> {
    if (!this.navigationRef) {
      console.warn('Navigation ref not available, storing for later');
      await this.storePendingNavigation(linkData);
      return;
    }

    const { path, params, query } = linkData;
    const pathSegments = path.split('/');

    try {
      // Handle different deep link routes
      switch (pathSegments[0]) {
        case 'bet':
          await this.handleBetDeepLink(pathSegments, params, query);
          break;
          
        case 'game':
          await this.handleGameDeepLink(pathSegments, params, query);
          break;
          
        case 'social':
          await this.handleSocialDeepLink(pathSegments, params, query);
          break;
          
        case 'user':
          await this.handleUserDeepLink(pathSegments, params, query);
          break;
          
        case 'tournament':
          await this.handleTournamentDeepLink(pathSegments, params, query);
          break;
          
        case 'referral':
          await this.handleReferralDeepLink(pathSegments, params, query);
          break;
          
        case 'share':
          await this.handleShareDeepLink(pathSegments, params, query);
          break;
          
        default:
          // Navigate to home if no specific route
          this.navigationRef.navigate('Main' as never, { screen: 'ValueBets' } as never);
      }
    } catch (error) {
      console.error('Error navigating from deep link:', error);
      // Fallback to home screen
      this.navigationRef.navigate('Main' as never);
    }
  }

  /**
   * Handle bet-related deep links
   */
  private async handleBetDeepLink(segments: string[], params: Record<string, string>, query: Record<string, string>): Promise<void> {
    const betId = params.betId || query.id;
    
    if (segments[1] === 'analysis' && betId) {
      this.navigationRef?.navigate('Main' as never, {
        screen: 'ValueBets',
        params: {
          screen: 'QuickAnalysis',
          params: { betId },
        },
      } as never);
    } else if (segments[1] === 'details' && betId) {
      this.navigationRef?.navigate('Main' as never, {
        screen: 'ValueBets',
        params: {
          screen: 'BetDetails',
          params: { betId },
        },
      } as never);
    } else {
      // Navigate to value bets feed
      this.navigationRef?.navigate('Main' as never, { screen: 'ValueBets' } as never);
    }
  }

  /**
   * Handle game-related deep links
   */
  private async handleGameDeepLink(segments: string[], params: Record<string, string>, query: Record<string, string>): Promise<void> {
    const gameId = params.gameId || query.id;
    
    if (segments[1] === 'live' && gameId) {
      this.navigationRef?.navigate('Main' as never, {
        screen: 'LiveGames',
        params: {
          screen: 'LiveBetting',
          params: { gameId },
        },
      } as never);
    } else if (segments[1] === 'details' && gameId) {
      this.navigationRef?.navigate('Main' as never, {
        screen: 'LiveGames',
        params: {
          screen: 'GameDetails',
          params: { gameId },
        },
      } as never);
    } else {
      // Navigate to live games
      this.navigationRef?.navigate('Main' as never, { screen: 'LiveGames' } as never);
    }
  }

  /**
   * Handle social-related deep links
   */
  private async handleSocialDeepLink(segments: string[], params: Record<string, string>, query: Record<string, string>): Promise<void> {
    const postId = params.postId || query.id;
    
    if (segments[1] === 'post' && postId) {
      this.navigationRef?.navigate('Main' as never, {
        screen: 'Social',
        params: {
          screen: 'BetPost',
          params: { postId },
        },
      } as never);
    } else {
      // Navigate to social feed
      this.navigationRef?.navigate('Main' as never, { screen: 'Social' } as never);
    }
  }

  /**
   * Handle user-related deep links
   */
  private async handleUserDeepLink(segments: string[], params: Record<string, string>, query: Record<string, string>): Promise<void> {
    const userId = params.userId || query.id;
    
    if (segments[1] === 'profile' && userId) {
      this.navigationRef?.navigate('Main' as never, {
        screen: 'Social',
        params: {
          screen: 'UserProfile',
          params: { userId },
        },
      } as never);
    } else {
      // Navigate to own profile
      this.navigationRef?.navigate('Main' as never, { screen: 'Profile' } as never);
    }
  }

  /**
   * Handle tournament deep links
   */
  private async handleTournamentDeepLink(segments: string[], params: Record<string, string>, query: Record<string, string>): Promise<void> {
    // TODO: Implement tournament navigation when tournaments are added
    this.navigationRef?.navigate('Main' as never, { screen: 'ValueBets' } as never);
  }

  /**
   * Handle referral deep links
   */
  private async handleReferralDeepLink(segments: string[], params: Record<string, string>, query: Record<string, string>): Promise<void> {
    const referralCode = params.referralCode || query.code;
    
    if (referralCode) {
      // Store referral code for registration
      await AsyncStorage.setItem('referralCode', referralCode);
      
      // Check if user is logged in
      const isAuthenticated = await this.checkAuthentication();
      
      if (!isAuthenticated) {
        // Navigate to registration with referral
        this.navigationRef?.navigate('Auth' as never, {
          screen: 'Register',
          params: { referralCode },
        } as never);
      } else {
        // Apply referral bonus if already logged in
        try {
          await apiClient.post('/referrals/apply', { code: referralCode });
          Alert.alert('Success', 'Referral bonus applied!');
        } catch (error) {
          console.error('Error applying referral:', error);
        }
      }
    }
  }

  /**
   * Handle share deep links
   */
  private async handleShareDeepLink(segments: string[], params: Record<string, string>, query: Record<string, string>): Promise<void> {
    const type = query.type;
    const id = query.id;
    
    if (type === 'bet' && id) {
      await this.handleBetDeepLink(['bet', 'details'], { betId: id }, {});
    } else if (type === 'post' && id) {
      await this.handleSocialDeepLink(['social', 'post'], { postId: id }, {});
    } else {
      this.navigationRef?.navigate('Main' as never);
    }
  }

  /**
   * Check if route requires authentication
   */
  private routeRequiresAuth(path: string): boolean {
    const publicRoutes = ['referral', 'share'];
    const firstSegment = path.split('/')[0];
    return !publicRoutes.includes(firstSegment);
  }

  /**
   * Check if user is authenticated
   */
  private async checkAuthentication(): Promise<boolean> {
    try {
      const token = await AsyncStorage.getItem('authToken');
      return !!token;
    } catch (error) {
      return false;
    }
  }

  /**
   * Navigate to authentication flow
   */
  private navigateToAuth(): void {
    this.navigationRef?.navigate('Auth' as never, { screen: 'Login' } as never);
  }

  /**
   * Store pending navigation for after authentication
   */
  private async storePendingNavigation(linkData: DeepLinkData): Promise<void> {
    const pendingNav: PendingNavigation = {
      route: linkData.path,
      params: { ...linkData.params, ...linkData.query },
      timestamp: Date.now(),
    };
    
    await AsyncStorage.setItem('pendingNavigation', JSON.stringify(pendingNav));
    this.pendingNavigation = pendingNav;
  }

  /**
   * Process pending navigation after authentication
   */
  async processPendingNavigation(): Promise<void> {
    try {
      const stored = await AsyncStorage.getItem('pendingNavigation');
      if (stored) {
        const pendingNav: PendingNavigation = JSON.parse(stored);
        
        // Check if navigation is not too old (1 hour limit)
        const oneHour = 60 * 60 * 1000;
        if (Date.now() - pendingNav.timestamp < oneHour) {
          // Reconstruct deep link data
          const linkData: DeepLinkData = {
            url: `sportsedge://${pendingNav.route}`,
            path: pendingNav.route,
            params: pendingNav.params || {},
            query: {},
          };
          
          await this.navigateFromDeepLink(linkData);
        }
        
        // Clear stored navigation
        await AsyncStorage.removeItem('pendingNavigation');
        this.pendingNavigation = null;
      }
    } catch (error) {
      console.error('Error processing pending navigation:', error);
    }
  }

  /**
   * Track deep link usage for analytics
   */
  private async trackDeepLink(linkData: DeepLinkData): Promise<void> {
    try {
      await apiClient.post('/analytics/deep-link', {
        url: linkData.url,
        path: linkData.path,
        params: linkData.params,
        query: linkData.query,
        timestamp: Date.now(),
      });
    } catch (error) {
      console.error('Error tracking deep link:', error);
    }
  }

  /**
   * Generate deep link URL
   */
  generateDeepLink(route: string, params?: Record<string, string>): string {
    let url = `${this.config.scheme}://${route}`;
    
    if (params && Object.keys(params).length > 0) {
      const searchParams = new URLSearchParams(params);
      url += `?${searchParams.toString()}`;
    }
    
    return url;
  }

  /**
   * Generate shareable URL
   */
  generateShareUrl(type: string, id: string): string {
    return `https://${this.config.host}/share?type=${type}&id=${id}`;
  }

  /**
   * Open deep link
   */
  async openDeepLink(url: string): Promise<boolean> {
    try {
      const canOpen = await Linking.canOpenURL(url);
      if (canOpen) {
        await Linking.openURL(url);
        return true;
      } else {
        console.warn('Cannot open URL:', url);
        return false;
      }
    } catch (error) {
      console.error('Error opening deep link:', error);
      return false;
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
export const deepLinkService = new DeepLinkService();