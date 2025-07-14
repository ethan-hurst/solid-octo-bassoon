/**
 * Portfolio Stack Navigator
 */
import React from 'react';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { useSelector } from 'react-redux';

import { PortfolioStackParamList } from '../types';
import { RootState } from '../../store';

// Placeholder screens for now
import PlaceholderScreen from '../../screens/PlaceholderScreen';

const Stack = createNativeStackNavigator<PortfolioStackParamList>();

const PortfolioStackNavigator: React.FC = () => {
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
      initialRouteName="Dashboard"
    >
      <Stack.Screen
        name="Dashboard"
        component={PlaceholderScreen}
        options={{
          title: 'Portfolio',
          headerLargeTitle: true,
        }}
        initialParams={{ title: 'Portfolio Dashboard' }}
      />
      
      <Stack.Screen
        name="BetHistory"
        component={PlaceholderScreen}
        options={{
          title: 'Bet History',
        }}
        initialParams={{ title: 'Bet History' }}
      />
      
      <Stack.Screen
        name="Statistics"
        component={PlaceholderScreen}
        options={{
          title: 'Statistics',
        }}
        initialParams={{ title: 'Statistics' }}
      />
      
      <Stack.Screen
        name="RiskAnalysis"
        component={PlaceholderScreen}
        options={{
          title: 'Risk Analysis',
        }}
        initialParams={{ title: 'Risk Analysis' }}
      />
      
      <Stack.Screen
        name="PnLDetails"
        component={PlaceholderScreen}
        options={{
          title: 'P&L Details',
        }}
        initialParams={{ title: 'P&L Details' }}
      />
    </Stack.Navigator>
  );
};

export default PortfolioStackNavigator;