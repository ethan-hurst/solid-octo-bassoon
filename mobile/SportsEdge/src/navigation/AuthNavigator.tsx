/**
 * Authentication Stack Navigator
 */
import React from 'react';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { useSelector } from 'react-redux';

import { AuthStackParamList } from './types';
import { RootState } from '../store';

// Placeholder screens for now
import PlaceholderScreen from '../screens/PlaceholderScreen';

const Stack = createNativeStackNavigator<AuthStackParamList>();

const AuthNavigator: React.FC = () => {
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
      initialRouteName="Welcome"
    >
      <Stack.Screen
        name="Welcome"
        component={PlaceholderScreen}
        options={{
          headerShown: false,
        }}
        initialParams={{ title: 'Welcome to Sports Edge' }}
      />
      
      <Stack.Screen
        name="Login"
        component={PlaceholderScreen}
        options={{
          title: 'Sign In',
          headerBackTitle: 'Back',
        }}
        initialParams={{ title: 'Login' }}
      />
      
      <Stack.Screen
        name="Register"
        component={PlaceholderScreen}
        options={{
          title: 'Create Account',
          headerBackTitle: 'Back',
        }}
        initialParams={{ title: 'Register' }}
      />
      
      <Stack.Screen
        name="ForgotPassword"
        component={PlaceholderScreen}
        options={{
          title: 'Reset Password',
          headerBackTitle: 'Sign In',
        }}
        initialParams={{ title: 'Forgot Password' }}
      />
      
      <Stack.Screen
        name="Onboarding"
        component={PlaceholderScreen}
        options={{
          headerShown: false,
          gestureEnabled: false,
        }}
        initialParams={{ title: 'Getting Started' }}
      />
    </Stack.Navigator>
  );
};

export default AuthNavigator;