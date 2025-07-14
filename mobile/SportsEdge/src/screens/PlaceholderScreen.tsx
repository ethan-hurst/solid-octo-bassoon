/**
 * Placeholder Screen Component
 * Used during development for screens that haven't been implemented yet
 */
import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  SafeAreaView,
  ScrollView,
  TouchableOpacity,
} from 'react-native';
import { useSelector } from 'react-redux';
import { useNavigation, useRoute } from '@react-navigation/native';
import Icon from 'react-native-vector-icons/Ionicons';

import { RootState } from '../store';

interface PlaceholderScreenProps {
  title?: string;
}

const PlaceholderScreen: React.FC<PlaceholderScreenProps> = () => {
  const navigation = useNavigation();
  const route = useRoute();
  const theme = useSelector((state: RootState) => state.userPreferences.theme);
  
  // Get title from route params or use default
  const title = (route.params as any)?.title || 'Screen';

  const isDark = theme.theme === 'dark' || 
    (theme.theme === 'auto' && new Date().getHours() > 18);

  const colors = {
    background: isDark ? '#0F172A' : '#FFFFFF',
    surface: isDark ? '#1E293B' : '#F8FAFC',
    text: isDark ? '#F1F5F9' : '#1E293B',
    textSecondary: isDark ? '#94A3B8' : '#64748B',
    border: isDark ? '#334155' : '#E2E8F0',
    accent: theme.accentColor,
  };

  const styles = StyleSheet.create({
    container: {\n      flex: 1,\n      backgroundColor: colors.background,\n    },\n    content: {\n      flex: 1,\n      justifyContent: 'center',\n      alignItems: 'center',\n      padding: 20,\n    },\n    card: {\n      backgroundColor: colors.surface,\n      borderRadius: 16,\n      padding: 24,\n      alignItems: 'center',\n      borderWidth: 1,\n      borderColor: colors.border,\n      minWidth: 280,\n    },\n    icon: {\n      marginBottom: 16,\n    },\n    title: {\n      fontSize: 24,\n      fontWeight: 'bold',\n      color: colors.text,\n      textAlign: 'center',\n      marginBottom: 8,\n    },\n    subtitle: {\n      fontSize: 16,\n      color: colors.textSecondary,\n      textAlign: 'center',\n      marginBottom: 24,\n    },\n    info: {\n      backgroundColor: colors.background,\n      borderRadius: 12,\n      padding: 16,\n      marginBottom: 20,\n      borderWidth: 1,\n      borderColor: colors.border,\n      width: '100%',\n    },\n    infoTitle: {\n      fontSize: 14,\n      fontWeight: '600',\n      color: colors.text,\n      marginBottom: 8,\n    },\n    infoText: {\n      fontSize: 12,\n      color: colors.textSecondary,\n      lineHeight: 16,\n    },\n    button: {\n      backgroundColor: colors.accent,\n      borderRadius: 12,\n      paddingHorizontal: 24,\n      paddingVertical: 12,\n      flexDirection: 'row',\n      alignItems: 'center',\n    },\n    buttonText: {\n      color: '#FFFFFF',\n      fontSize: 16,\n      fontWeight: '600',\n      marginLeft: 8,\n    },\n  });\n\n  const handleGoBack = () => {\n    if (navigation.canGoBack()) {\n      navigation.goBack();\n    }\n  };\n\n  return (\n    <SafeAreaView style={styles.container}>\n      <ScrollView contentContainerStyle={styles.content}>\n        <View style={styles.card}>\n          <View style={styles.icon}>\n            <Icon \n              name=\"construct-outline\" \n              size={48} \n              color={colors.accent} \n            />\n          </View>\n          \n          <Text style={styles.title}>{title}</Text>\n          <Text style={styles.subtitle}>Coming Soon</Text>\n          \n          <View style={styles.info}>\n            <Text style={styles.infoTitle}>Development Status</Text>\n            <Text style={styles.infoText}>\n              This screen is currently under development. The navigation structure \n              is in place and ready for the actual screen implementation.\n            </Text>\n          </View>\n          \n          {navigation.canGoBack() && (\n            <TouchableOpacity \n              style={styles.button} \n              onPress={handleGoBack}\n              activeOpacity={0.8}\n            >\n              <Icon name=\"arrow-back\" size={20} color=\"#FFFFFF\" />\n              <Text style={styles.buttonText}>Go Back</Text>\n            </TouchableOpacity>\n          )}\n        </View>\n      </ScrollView>\n    </SafeAreaView>\n  );\n};\n\nexport default PlaceholderScreen;