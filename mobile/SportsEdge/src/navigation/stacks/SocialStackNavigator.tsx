/**
 * Social Stack Navigator
 */
import React from 'react';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { useSelector } from 'react-redux';

import { SocialStackParamList } from '../types';
import { RootState } from '../../store';

// Placeholder screens for now
import PlaceholderScreen from '../../screens/PlaceholderScreen';

const Stack = createNativeStackNavigator<SocialStackParamList>();

const SocialStackNavigator: React.FC = () => {
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
      initialRouteName="SocialFeed"
    >
      <Stack.Screen
        name="SocialFeed"
        component={PlaceholderScreen}
        options={{
          title: 'Social Feed',
          headerLargeTitle: true,
        }}
        initialParams={{ title: 'Social Feed' }}
      />
      
      <Stack.Screen
        name="UserProfile"
        component={PlaceholderScreen}
        options={{
          title: 'Profile',
        }}
        initialParams={{ title: 'User Profile' }}
      />
      
      <Stack.Screen
        name="BetPost"
        component={PlaceholderScreen}
        options={{
          title: 'Bet Post',
        }}
        initialParams={{ title: 'Bet Post' }}
      />
      
      <Stack.Screen
        name="Followers"
        component={PlaceholderScreen}
        options={{
          title: 'Followers',
        }}
        initialParams={{ title: 'Followers' }}
      />
      
      <Stack.Screen
        name="Following"
        component={PlaceholderScreen}
        options={{
          title: 'Following',
        }}
        initialParams={{ title: 'Following' }}
      />
      
      <Stack.Screen
        name="CopyTradingSettings"
        component={PlaceholderScreen}
        options={{
          title: 'Copy Trading',
          presentation: 'modal',
        }}
        initialParams={{ title: 'Copy Trading Settings' }}
      />
    </Stack.Navigator>
  );
};

export default SocialStackNavigator;