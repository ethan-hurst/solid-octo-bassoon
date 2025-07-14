/**
 * Navigation types for React Navigation 6
 */
import { NavigatorScreenParams } from '@react-navigation/native';
import { NativeStackScreenProps } from '@react-navigation/native-stack';
import { BottomTabScreenProps } from '@react-navigation/bottom-tabs';

// Root Stack Navigator
export type RootStackParamList = {
  Auth: NavigatorScreenParams<AuthStackParamList>;
  Main: NavigatorScreenParams<MainTabParamList>;
  Modal: NavigatorScreenParams<ModalStackParamList>;
};

// Auth Stack Navigator
export type AuthStackParamList = {
  Welcome: undefined;
  Login: undefined;
  Register: undefined;
  ForgotPassword: undefined;
  Onboarding: undefined;
};

// Main Tab Navigator
export type MainTabParamList = {
  ValueBets: NavigatorScreenParams<ValueBetsStackParamList>;
  LiveGames: NavigatorScreenParams<LiveGamesStackParamList>;
  Social: NavigatorScreenParams<SocialStackParamList>;
  Portfolio: NavigatorScreenParams<PortfolioStackParamList>;
  Profile: NavigatorScreenParams<ProfileStackParamList>;
};

// Value Bets Stack Navigator
export type ValueBetsStackParamList = {
  ValueBetsFeed: undefined;
  QuickAnalysis: { betId: string };
  BetDetails: { betId: string };
  FilterSettings: undefined;
};

// Live Games Stack Navigator
export type LiveGamesStackParamList = {
  LiveGamesList: undefined;
  GameDetails: { gameId: string };
  LiveBetting: { gameId: string };
};

// Social Stack Navigator
export type SocialStackParamList = {
  SocialFeed: undefined;
  UserProfile: { userId: string };
  BetPost: { postId: string };
  Followers: { userId: string };
  Following: { userId: string };
  CopyTradingSettings: undefined;
};

// Portfolio Stack Navigator
export type PortfolioStackParamList = {
  Dashboard: undefined;
  BetHistory: undefined;
  Statistics: undefined;
  RiskAnalysis: undefined;
  PnLDetails: { timeframe?: string };
};

// Profile Stack Navigator
export type ProfileStackParamList = {
  ProfileHome: undefined;
  Settings: undefined;
  NotificationSettings: undefined;
  BiometricSettings: undefined;
  HelpSupport: undefined;
  About: undefined;
};

// Modal Stack Navigator
export type ModalStackParamList = {
  QuickBetModal: { betId: string };
  FilterModal: { filterType: string };
  ShareModal: { content: any };
  NotificationModal: { notificationId: string };
};

// Screen props types for type-safe navigation
export type RootStackScreenProps<T extends keyof RootStackParamList> = 
  NativeStackScreenProps<RootStackParamList, T>;

export type AuthStackScreenProps<T extends keyof AuthStackParamList> = 
  NativeStackScreenProps<AuthStackParamList, T>;

export type MainTabScreenProps<T extends keyof MainTabParamList> = 
  BottomTabScreenProps<MainTabParamList, T>;

export type ValueBetsStackScreenProps<T extends keyof ValueBetsStackParamList> = 
  NativeStackScreenProps<ValueBetsStackParamList, T>;

export type LiveGamesStackScreenProps<T extends keyof LiveGamesStackParamList> = 
  NativeStackScreenProps<LiveGamesStackParamList, T>;

export type SocialStackScreenProps<T extends keyof SocialStackParamList> = 
  NativeStackScreenProps<SocialStackParamList, T>;

export type PortfolioStackScreenProps<T extends keyof PortfolioStackParamList> = 
  NativeStackScreenProps<PortfolioStackParamList, T>;

export type ProfileStackScreenProps<T extends keyof ProfileStackParamList> = 
  NativeStackScreenProps<ProfileStackParamList, T>;

export type ModalStackScreenProps<T extends keyof ModalStackParamList> = 
  NativeStackScreenProps<ModalStackParamList, T>;

// Combined props type for screens that can be accessed from multiple navigators
export type CombinedScreenProps<
  TabNavigatorParamList extends Record<string, any>,
  TabRoute extends keyof TabNavigatorParamList,
  StackNavigatorParamList extends Record<string, any>,
  StackRoute extends keyof StackNavigatorParamList
> = BottomTabScreenProps<TabNavigatorParamList, TabRoute> & 
    NativeStackScreenProps<StackNavigatorParamList, StackRoute>;

declare global {
  namespace ReactNavigation {
    interface RootParamList extends RootStackParamList {}
  }
}