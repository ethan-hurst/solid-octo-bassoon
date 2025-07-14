/**
 * User Preferences slice for mobile app
 */
import { createSlice, PayloadAction } from '@reduxjs/toolkit';

export interface ThemeSettings {
  theme: 'light' | 'dark' | 'auto';
  accentColor: string;
}

export interface DisplaySettings {
  fontSize: 'small' | 'medium' | 'large';
  compactMode: boolean;
  showProbabilities: boolean;
  oddsFormat: 'american' | 'decimal' | 'fractional';
}

export interface BettingPreferences {
  defaultStake: number;
  maxStakePerBet: number;
  followedSports: string[];
  minEdgeFilter: number;
  autoFollowCopiedBets: boolean;
  quickAnalysisEnabled: boolean;
}

export interface PrivacySettings {
  shareProfilePublicly: boolean;
  allowFollowing: boolean;
  showBettingHistory: boolean;
  dataUsageOptimization: boolean;
}

interface UserPreferencesState {
  theme: ThemeSettings;
  display: DisplaySettings;
  betting: BettingPreferences;
  privacy: PrivacySettings;
  onboardingCompleted: boolean;
  firstTimeUser: boolean;
  tutorialSteps: {
    valueBetsFeed: boolean;
    quickAnalysis: boolean;
    swipeInterface: boolean;
    liveGames: boolean;
    socialFeatures: boolean;
  };
}

const initialState: UserPreferencesState = {
  theme: {
    theme: 'dark',
    accentColor: '#3B82F6',
  },
  display: {
    fontSize: 'medium',
    compactMode: false,
    showProbabilities: true,
    oddsFormat: 'american',
  },
  betting: {
    defaultStake: 25,
    maxStakePerBet: 100,
    followedSports: ['NFL', 'NBA'],
    minEdgeFilter: 0.03,
    autoFollowCopiedBets: false,
    quickAnalysisEnabled: true,
  },
  privacy: {
    shareProfilePublicly: false,
    allowFollowing: true,
    showBettingHistory: false,
    dataUsageOptimization: true,
  },
  onboardingCompleted: false,
  firstTimeUser: true,
  tutorialSteps: {
    valueBetsFeed: false,
    quickAnalysis: false,
    swipeInterface: false,
    liveGames: false,
    socialFeatures: false,
  },
};

const userPreferencesSlice = createSlice({
  name: 'userPreferences',
  initialState,
  reducers: {
    updateThemeSettings: (state, action: PayloadAction<Partial<ThemeSettings>>) => {
      state.theme = { ...state.theme, ...action.payload };
    },
    
    updateDisplaySettings: (state, action: PayloadAction<Partial<DisplaySettings>>) => {
      state.display = { ...state.display, ...action.payload };
    },
    
    updateBettingPreferences: (state, action: PayloadAction<Partial<BettingPreferences>>) => {
      state.betting = { ...state.betting, ...action.payload };
    },
    
    updatePrivacySettings: (state, action: PayloadAction<Partial<PrivacySettings>>) => {
      state.privacy = { ...state.privacy, ...action.payload };
    },
    
    toggleFollowedSport: (state, action: PayloadAction<string>) => {
      const sport = action.payload;
      const index = state.betting.followedSports.indexOf(sport);
      
      if (index > -1) {
        state.betting.followedSports.splice(index, 1);
      } else {
        state.betting.followedSports.push(sport);
      }
    },
    
    completeOnboarding: (state) => {
      state.onboardingCompleted = true;
      state.firstTimeUser = false;
    },
    
    completeTutorialStep: (state, action: PayloadAction<keyof UserPreferencesState['tutorialSteps']>) => {
      state.tutorialSteps[action.payload] = true;
    },
    
    resetTutorials: (state) => {
      state.tutorialSteps = {
        valueBetsFeed: false,
        quickAnalysis: false,
        swipeInterface: false,
        liveGames: false,
        socialFeatures: false,
      };
    },
    
    resetAllPreferences: () => {
      return initialState;
    },
  },
});

export const {
  updateThemeSettings,
  updateDisplaySettings,
  updateBettingPreferences,
  updatePrivacySettings,
  toggleFollowedSport,
  completeOnboarding,
  completeTutorialStep,
  resetTutorials,
  resetAllPreferences,
} = userPreferencesSlice.actions;

export default userPreferencesSlice.reducer;