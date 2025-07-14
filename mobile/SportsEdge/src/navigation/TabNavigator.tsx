/**
 * Bottom Tab Navigator for main app navigation
 */
import React from 'react';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { useSelector } from 'react-redux';
import Icon from 'react-native-vector-icons/Ionicons';

import { MainTabParamList } from './types';
import { RootState } from '../store';

// Stack Navigators
import ValueBetsStackNavigator from './stacks/ValueBetsStackNavigator';
import LiveGamesStackNavigator from './stacks/LiveGamesStackNavigator';
import SocialStackNavigator from './stacks/SocialStackNavigator';
import PortfolioStackNavigator from './stacks/PortfolioStackNavigator';
import ProfileStackNavigator from './stacks/ProfileStackNavigator';

const Tab = createBottomTabNavigator<MainTabParamList>();

const TabNavigator: React.FC = () => {
  const theme = useSelector((state: RootState) => state.userPreferences.theme);
  const unreadCount = useSelector((state: RootState) => state.notifications.unreadCount);

  const isDark = theme.theme === 'dark' || 
    (theme.theme === 'auto' && new Date().getHours() > 18);

  const colors = {
    background: isDark ? '#0F172A' : '#FFFFFF',
    border: isDark ? '#1E293B' : '#E2E8F0',
    active: theme.accentColor,
    inactive: isDark ? '#64748B' : '#94A3B8',
    text: isDark ? '#F1F5F9' : '#1E293B',
  };

  return (
    <Tab.Navigator
      screenOptions={({ route }) => ({
        tabBarIcon: ({ focused, color, size }) => {
          let iconName: string;

          switch (route.name) {
            case 'ValueBets':
              iconName = focused ? 'flash' : 'flash-outline';
              break;
            case 'LiveGames':
              iconName = focused ? 'play-circle' : 'play-circle-outline';
              break;
            case 'Social':
              iconName = focused ? 'people' : 'people-outline';
              break;
            case 'Portfolio':
              iconName = focused ? 'trending-up' : 'trending-up-outline';
              break;
            case 'Profile':
              iconName = focused ? 'person' : 'person-outline';
              break;
            default:
              iconName = 'help-outline';
          }

          return <Icon name={iconName} size={size} color={color} />;
        },
        tabBarActiveTintColor: colors.active,
        tabBarInactiveTintColor: colors.inactive,
        tabBarStyle: {
          backgroundColor: colors.background,
          borderTopColor: colors.border,
          borderTopWidth: 1,
          paddingBottom: 8,
          paddingTop: 8,
          height: 60,
        },
        tabBarLabelStyle: {
          fontSize: 11,
          fontWeight: '500',
          marginTop: 4,
        },
        headerShown: false,
        tabBarHideOnKeyboard: true,
      })}
    >
      <Tab.Screen
        name="ValueBets"
        component={ValueBetsStackNavigator}
        options={{
          tabBarLabel: 'Value Bets',
          tabBarBadge: undefined, // TODO: Add value bet count badge
        }}
      />
      
      <Tab.Screen
        name="LiveGames"
        component={LiveGamesStackNavigator}
        options={{
          tabBarLabel: 'Live',
        }}
      />
      
      <Tab.Screen
        name="Social"
        component={SocialStackNavigator}
        options={{
          tabBarLabel: 'Social',
          tabBarBadge: unreadCount > 0 ? unreadCount : undefined,
        }}
      />
      
      <Tab.Screen
        name="Portfolio"
        component={PortfolioStackNavigator}
        options={{
          tabBarLabel: 'Portfolio',
        }}
      />
      
      <Tab.Screen
        name="Profile"
        component={ProfileStackNavigator}
        options={{
          tabBarLabel: 'Profile',
        }}
      />
    </Tab.Navigator>
  );
};

export default TabNavigator;