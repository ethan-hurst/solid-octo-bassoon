/**
 * Profile Stack Navigator
 */
import React from 'react';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { useSelector } from 'react-redux';

import { ProfileStackParamList } from '../types';
import { RootState } from '../../store';

// Placeholder screens for now
import PlaceholderScreen from '../../screens/PlaceholderScreen';

const Stack = createNativeStackNavigator<ProfileStackParamList>();

const ProfileStackNavigator: React.FC = () => {
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
      initialRouteName="ProfileHome"
    >
      <Stack.Screen
        name="ProfileHome"
        component={PlaceholderScreen}
        options={{
          title: 'Profile',
          headerLargeTitle: true,
        }}
        initialParams={{ title: 'Profile' }}
      />
      
      <Stack.Screen
        name="Settings"
        component={PlaceholderScreen}
        options={{
          title: 'Settings',
        }}
        initialParams={{ title: 'Settings' }}
      />
      
      <Stack.Screen
        name="NotificationSettings"
        component={PlaceholderScreen}
        options={{
          title: 'Notifications',
        }}
        initialParams={{ title: 'Notification Settings' }}
      />
      
      <Stack.Screen
        name="BiometricSettings"
        component={PlaceholderScreen}
        options={{
          title: 'Biometric Login',
        }}
        initialParams={{ title: 'Biometric Settings' }}
      />
      
      <Stack.Screen
        name="HelpSupport"
        component={PlaceholderScreen}
        options={{
          title: 'Help & Support',
        }}
        initialParams={{ title: 'Help & Support' }}
      />
      
      <Stack.Screen
        name="About"
        component={PlaceholderScreen}
        options={{
          title: 'About',
        }}
        initialParams={{ title: 'About' }}
      />
    </Stack.Navigator>
  );
};

export default ProfileStackNavigator;