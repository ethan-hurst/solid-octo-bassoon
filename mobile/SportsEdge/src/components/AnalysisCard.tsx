/**
 * Analysis Card Component - Displays analysis data in a card format
 */
import React from 'react';
import {
  View,
  Text,
  StyleSheet,
} from 'react-native';
import { useSelector } from 'react-redux';

import { RootState } from '../store';

interface AnalysisDataItem {
  label: string;
  value: string;
  highlight?: boolean;
}

interface AnalysisCardProps {
  title: string;
  data: AnalysisDataItem[];
  compact?: boolean;
}

const AnalysisCard: React.FC<AnalysisCardProps> = ({
  title,
  data,
  compact = false,
}) => {
  const theme = useSelector((state: RootState) => state.userPreferences.theme);

  const isDark = theme.theme === 'dark' || 
    (theme.theme === 'auto' && new Date().getHours() > 18);

  const colors = {
    background: isDark ? '#1E293B' : '#FFFFFF',
    surface: isDark ? '#334155' : '#F8FAFC',
    text: isDark ? '#F1F5F9' : '#1E293B',
    textSecondary: isDark ? '#94A3B8' : '#64748B',
    border: isDark ? '#475569' : '#E2E8F0',
    accent: theme.accentColor,
  };

  const styles = StyleSheet.create({
    card: {
      backgroundColor: colors.background,
      borderRadius: 12,
      padding: compact ? 12 : 16,
      marginBottom: 16,
      borderWidth: 1,
      borderColor: colors.border,
    },
    title: {
      fontSize: compact ? 14 : 16,
      fontWeight: '600',
      color: colors.text,
      marginBottom: compact ? 8 : 12,
    },
    dataContainer: {
      gap: compact ? 6 : 8,
    },
    dataRow: {
      flexDirection: 'row',
      justifyContent: 'space-between',
      alignItems: 'center',
      paddingVertical: compact ? 4 : 6,
      paddingHorizontal: compact ? 8 : 12,
      backgroundColor: colors.surface,
      borderRadius: 6,
    },
    dataLabel: {
      fontSize: compact ? 12 : 14,
      color: colors.textSecondary,
      flex: 1,
    },
    dataValue: {
      fontSize: compact ? 12 : 14,
      fontWeight: '600',
      color: colors.text,
    },
    highlightedValue: {
      color: colors.accent,
    },
  });

  return (
    <View style={styles.card}>
      <Text style={styles.title}>{title}</Text>
      <View style={styles.dataContainer}>
        {data.map((item, index) => (
          <View key={index} style={styles.dataRow}>
            <Text style={styles.dataLabel}>{item.label}</Text>
            <Text style={[
              styles.dataValue,
              item.highlight && styles.highlightedValue
            ]}>
              {item.value}
            </Text>
          </View>
        ))}
      </View>
    </View>
  );
};

export default AnalysisCard;