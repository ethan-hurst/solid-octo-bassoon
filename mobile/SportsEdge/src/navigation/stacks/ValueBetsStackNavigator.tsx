/**
 * Value Bets Stack Navigator
 */
import React from 'react';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { useSelector } from 'react-redux';

import { ValueBetsStackParamList } from '../types';
import { RootState } from '../../store';

// Screens (to be created)
// import ValueBetsFeedScreen from '../../screens/ValueBets/ValueBetsFeedScreen';
// import QuickAnalysisScreen from '../../screens/ValueBets/QuickAnalysisScreen';
// import BetDetailsScreen from '../../screens/ValueBets/BetDetailsScreen';
// import FilterSettingsScreen from '../../screens/ValueBets/FilterSettingsScreen';

// Placeholder screens for now
import PlaceholderScreen from '../../screens/PlaceholderScreen';

const Stack = createNativeStackNavigator<ValueBetsStackParamList>();

const ValueBetsStackNavigator: React.FC = () => {
  const theme = useSelector((state: RootState) => state.userPreferences.theme);

  const isDark = theme.theme === 'dark' || 
    (theme.theme === 'auto' && new Date().getHours() > 18);

  const colors = {
    background: isDark ? '#0F172A' : '#FFFFFF',
    text: isDark ? '#F1F5F9' : '#1E293B',
    border: isDark ? '#1E293B' : '#E2E8F0',
  };

  const screenOptions = {
    headerStyle: {
      backgroundColor: colors.background,
    },
    headerTintColor: colors.text,
    headerTitleStyle: {
      fontWeight: '600' as const,
    },
    headerShadowVisible: false,
    headerBackTitleVisible: false,
  };

  return (
    <Stack.Navigator
      screenOptions={screenOptions}
      initialRouteName="ValueBetsFeed"
    >
      <Stack.Screen
        name="ValueBetsFeed"
        component={PlaceholderScreen}
        options={{
          title: 'Value Bets',
          headerLargeTitle: true,
        }}
        initialParams={{ title: 'Value Bets Feed' }}
      />
      
      <Stack.Screen
        name="QuickAnalysis"
        component={PlaceholderScreen}
        options={{
          title: 'Quick Analysis',
          presentation: 'modal',
        }}
        initialParams={{ title: 'Quick Analysis' }}
      />
      
      <Stack.Screen
        name="BetDetails"
        component={PlaceholderScreen}
        options={{
          title: 'Bet Details',
        }}
        initialParams={{ title: 'Bet Details' }}
      />
      
      <Stack.Screen
        name="FilterSettings"
        component={PlaceholderScreen}
        options={{
          title: 'Filter Settings',
          presentation: 'modal',
        }}
        initialParams={{ title: 'Filter Settings' }}
      />
    </Stack.Navigator>
  );
};

export default ValueBetsStackNavigator;