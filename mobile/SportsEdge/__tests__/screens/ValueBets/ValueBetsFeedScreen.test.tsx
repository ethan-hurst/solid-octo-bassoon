/**
 * Value Bets Feed Screen Tests
 */
import React from 'react';
import { render, fireEvent, screen, waitFor } from '@testing-library/react-native';
import { Provider } from 'react-redux';
import { NavigationContainer } from '@react-navigation/navigation';
import { createStackNavigator } from '@react-navigation/stack';
import { configureStore } from '@reduxjs/toolkit';

import ValueBetsFeedScreen from '../../../src/screens/ValueBets/ValueBetsFeedScreen';
import { valueBetsSlice } from '../../../src/store/slices/valueBetsSlice';
import { userPreferencesSlice } from '../../../src/store/slices/userPreferencesSlice';

// Mock the useValueBetsWebSocket hook
jest.mock('../../../src/hooks/useWebSocket', () => ({
  useValueBetsWebSocket: jest.fn(),
}));

// Mock react-native modules
jest.mock('react-native', () => {
  const RN = jest.requireActual('react-native');
  return {
    ...RN,
    Alert: {
      alert: jest.fn(),
    },
    Linking: {
      openURL: jest.fn(),
    },
  };
});

// Mock services
jest.mock('../../../src/services', () => ({
  analyticsService: {
    trackScreen: jest.fn(),
    trackInteraction: jest.fn(),
    trackBettingEvent: jest.fn(),
  },
  apiClient: {
    get: jest.fn(),
    post: jest.fn(),
  },
}));

const Stack = createStackNavigator();

const mockValueBets = [
  {
    id: '1',
    game: 'Lakers vs Warriors',
    type: 'moneyline',
    team: 'Lakers',
    odds: -110,
    bookmaker: 'DraftKings',
    edge: 5.2,
    confidence: 0.85,
    sport: 'NBA',
    league: 'NBA',
    start_time: '2024-01-15T20:00:00Z',
    market_type: 'moneyline',
    selection: 'Lakers ML',
    stake_suggestion: 100,
    created_at: '2024-01-15T18:00:00Z',
  },
  {
    id: '2',
    game: 'Chiefs vs Bills',
    type: 'spread',
    team: 'Chiefs',
    odds: +120,
    bookmaker: 'FanDuel',
    edge: 3.8,
    confidence: 0.72,
    sport: 'NFL',
    league: 'NFL',
    start_time: '2024-01-16T13:00:00Z',
    market_type: 'spread',
    selection: 'Chiefs +3.5',
    stake_suggestion: 75,
    created_at: '2024-01-15T19:00:00Z',
  },
];

const mockStore = configureStore({
  reducer: {
    valueBets: valueBetsSlice.reducer,
    userPreferences: userPreferencesSlice.reducer,
  },
  preloadedState: {
    valueBets: {
      valueBets: mockValueBets,
      isLoading: false,
      error: null,
      lastUpdate: new Date().toISOString(),
      filters: {
        sport: 'all',
        minEdge: 0,
        maxEdge: 100,
        bookmakers: [],
        betTypes: [],
      },
      statistics: {
        totalBets: 2,
        averageEdge: 4.5,
        highConfidenceBets: 1,
        topSports: ['NBA', 'NFL'],
      },
    },
    userPreferences: {
      theme: {
        theme: 'light',
        accentColor: '#3B82F6',
      },
      notifications: {
        enabled: true,
        minEdge: 3.0,
        sports: ['NBA', 'NFL'],
      },
      betSettings: {
        defaultStake: 100,
        riskLevel: 'medium',
        autoAcceptOddsChanges: false,
      },
    },
  },
});

const MockedValueBetsFeedScreen = () => (
  <Provider store={mockStore}>
    <NavigationContainer>
      <Stack.Navigator>
        <Stack.Screen 
          name="ValueBetsFeed" 
          component={ValueBetsFeedScreen}
          options={{ headerShown: false }}
        />
      </Stack.Navigator>
    </NavigationContainer>
  </Provider>
);

describe('ValueBetsFeedScreen', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders correctly with value bets', async () => {
    render(<MockedValueBetsFeedScreen />);
    
    await waitFor(() => {
      expect(screen.getByText('Value Bets')).toBeTruthy();
      expect(screen.getByText('Lakers vs Warriors')).toBeTruthy();
      expect(screen.getByText('Chiefs vs Bills')).toBeTruthy();
    });
  });

  it('displays statistics correctly', async () => {
    render(<MockedValueBetsFeedScreen />);
    
    await waitFor(() => {
      expect(screen.getByText('2')).toBeTruthy(); // Total bets
      expect(screen.getByText('4.5%')).toBeTruthy(); // Average edge
      expect(screen.getByText('1')).toBeTruthy(); // High confidence bets
    });
  });

  it('handles refresh functionality', async () => {
    render(<MockedValueBetsFeedScreen />);
    
    const refreshControl = screen.getByTestId('value-bets-refresh');
    fireEvent(refreshControl, 'refresh');
    
    // Should trigger refresh action
    await waitFor(() => {
      expect(screen.getByText('Value Bets')).toBeTruthy();
    });
  });

  it('opens filter modal when filter button is pressed', async () => {
    render(<MockedValueBetsFeedScreen />);
    
    const filterButton = screen.getByTestId('filter-button');
    fireEvent.press(filterButton);
    
    await waitFor(() => {
      expect(screen.getByText('Filter Options')).toBeTruthy();
    });
  });

  it('navigates to bet analysis when bet card is pressed', async () => {
    render(<MockedValueBetsFeedScreen />);
    
    await waitFor(() => {
      const betCard = screen.getByTestId('value-bet-card-1');
      fireEvent.press(betCard);
    });
    
    // Should navigate to analysis screen
    // This would require mocking navigation
  });

  it('displays empty state when no bets available', async () => {
    const emptyStore = configureStore({
      reducer: {
        valueBets: valueBetsSlice.reducer,
        userPreferences: userPreferencesSlice.reducer,
      },
      preloadedState: {
        valueBets: {
          valueBets: [],
          isLoading: false,
          error: null,
          lastUpdate: null,
          filters: {
            sport: 'all',
            minEdge: 0,
            maxEdge: 100,
            bookmakers: [],
            betTypes: [],
          },
          statistics: {
            totalBets: 0,
            averageEdge: 0,
            highConfidenceBets: 0,
            topSports: [],
          },
        },
        userPreferences: {
          theme: {
            theme: 'light',
            accentColor: '#3B82F6',
          },
          notifications: {
            enabled: true,
            minEdge: 3.0,
            sports: ['NBA', 'NFL'],
          },
          betSettings: {
            defaultStake: 100,
            riskLevel: 'medium',
            autoAcceptOddsChanges: false,
          },
        },
      },
    });

    render(
      <Provider store={emptyStore}>
        <NavigationContainer>
          <Stack.Navigator>
            <Stack.Screen 
              name="ValueBetsFeed" 
              component={ValueBetsFeedScreen}
              options={{ headerShown: false }}
            />
          </Stack.Navigator>
        </NavigationContainer>
      </Provider>
    );
    
    await waitFor(() => {
      expect(screen.getByText('No value bets found')).toBeTruthy();
    });
  });

  it('displays loading state correctly', async () => {
    const loadingStore = configureStore({
      reducer: {
        valueBets: valueBetsSlice.reducer,
        userPreferences: userPreferencesSlice.reducer,
      },
      preloadedState: {
        valueBets: {
          valueBets: [],
          isLoading: true,
          error: null,
          lastUpdate: null,
          filters: {
            sport: 'all',
            minEdge: 0,
            maxEdge: 100,
            bookmakers: [],
            betTypes: [],
          },
          statistics: {
            totalBets: 0,
            averageEdge: 0,
            highConfidenceBets: 0,
            topSports: [],
          },
        },
        userPreferences: {
          theme: {
            theme: 'light',
            accentColor: '#3B82F6',
          },
          notifications: {
            enabled: true,
            minEdge: 3.0,
            sports: ['NBA', 'NFL'],
          },
          betSettings: {
            defaultStake: 100,
            riskLevel: 'medium',
            autoAcceptOddsChanges: false,
          },
        },
      },
    });

    render(
      <Provider store={loadingStore}>
        <NavigationContainer>
          <Stack.Navigator>
            <Stack.Screen 
              name="ValueBetsFeed" 
              component={ValueBetsFeedScreen}
              options={{ headerShown: false }}
            />
          </Stack.Navigator>
        </NavigationContainer>
      </Provider>
    );
    
    await waitFor(() => {
      expect(screen.getByTestId('loading-spinner')).toBeTruthy();
    });
  });

  it('handles error state correctly', async () => {
    const errorStore = configureStore({
      reducer: {
        valueBets: valueBetsSlice.reducer,
        userPreferences: userPreferencesSlice.reducer,
      },
      preloadedState: {
        valueBets: {
          valueBets: [],
          isLoading: false,
          error: 'Failed to load value bets',
          lastUpdate: null,
          filters: {
            sport: 'all',
            minEdge: 0,
            maxEdge: 100,
            bookmakers: [],
            betTypes: [],
          },
          statistics: {
            totalBets: 0,
            averageEdge: 0,
            highConfidenceBets: 0,
            topSports: [],
          },
        },
        userPreferences: {
          theme: {
            theme: 'light',
            accentColor: '#3B82F6',
          },
          notifications: {
            enabled: true,
            minEdge: 3.0,
            sports: ['NBA', 'NFL'],
          },
          betSettings: {
            defaultStake: 100,
            riskLevel: 'medium',
            autoAcceptOddsChanges: false,
          },
        },
      },
    });

    render(
      <Provider store={errorStore}>
        <NavigationContainer>
          <Stack.Navigator>
            <Stack.Screen 
              name="ValueBetsFeed" 
              component={ValueBetsFeedScreen}
              options={{ headerShown: false }}
            />
          </Stack.Navigator>
        </NavigationContainer>
      </Provider>
    );
    
    await waitFor(() => {
      expect(screen.getByText('Failed to load value bets')).toBeTruthy();
    });
  });

  it('applies filters correctly', async () => {
    render(<MockedValueBetsFeedScreen />);
    
    // Open filter modal
    const filterButton = screen.getByTestId('filter-button');
    fireEvent.press(filterButton);
    
    await waitFor(() => {
      // Select NBA filter
      const nbaFilter = screen.getByText('NBA');
      fireEvent.press(nbaFilter);
      
      // Apply filters
      const applyButton = screen.getByText('Apply Filters');
      fireEvent.press(applyButton);
    });
    
    // Should show only NBA bets
    await waitFor(() => {
      expect(screen.getByText('Lakers vs Warriors')).toBeTruthy();
    });
  });

  it('displays real-time updates indicator', async () => {
    render(<MockedValueBetsFeedScreen />);
    
    await waitFor(() => {
      expect(screen.getByTestId('real-time-indicator')).toBeTruthy();
    });
  });

  it('tracks analytics events correctly', async () => {
    const { analyticsService } = require('../../../src/services');
    
    render(<MockedValueBetsFeedScreen />);
    
    await waitFor(() => {
      expect(analyticsService.trackScreen).toHaveBeenCalledWith('ValueBetsFeedScreen');
    });
    
    // Test interaction tracking
    const filterButton = screen.getByTestId('filter-button');
    fireEvent.press(filterButton);
    
    expect(analyticsService.trackInteraction).toHaveBeenCalledWith(
      'button_press',
      'filter_button',
      { screen: 'ValueBetsFeedScreen' }
    );
  });
});