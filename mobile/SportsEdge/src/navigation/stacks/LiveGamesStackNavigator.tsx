/**
 * Live Games Stack Navigator
 */
import React from 'react';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { useSelector } from 'react-redux';

import { LiveGamesStackParamList } from '../types';
import { RootState } from '../../store';

// Placeholder screens for now
import PlaceholderScreen from '../../screens/PlaceholderScreen';

const Stack = createNativeStackNavigator<LiveGamesStackParamList>();

const LiveGamesStackNavigator: React.FC = () => {
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
      initialRouteName="LiveGamesList"
    >
      <Stack.Screen
        name="LiveGamesList"
        component={PlaceholderScreen}
        options={{
          title: 'Live Games',
          headerLargeTitle: true,
        }}
        initialParams={{ title: 'Live Games' }}
      />
      
      <Stack.Screen
        name="GameDetails"
        component={PlaceholderScreen}
        options={{
          title: 'Game Details',
        }}
        initialParams={{ title: 'Game Details' }}
      />
      
      <Stack.Screen
        name="LiveBetting"
        component={PlaceholderScreen}
        options={{
          title: 'Live Betting',
          presentation: 'fullScreenModal',
        }}
        initialParams={{ title: 'Live Betting' }}
      />
    </Stack.Navigator>
  );
};

export default LiveGamesStackNavigator;