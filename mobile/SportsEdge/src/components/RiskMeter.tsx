/**
 * Risk Meter Component - Visual risk assessment indicator
 */
import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  Dimensions,
} from 'react-native';
import { useSelector } from 'react-redux';
import Icon from 'react-native-vector-icons/Ionicons';

import { RootState } from '../store';

interface RiskMeterProps {
  riskLevel: 'low' | 'medium' | 'high';
  volatility: number; // 0-1
  bankrollImpact: number; // 0-1
}

const { width } = Dimensions.get('window');

const RiskMeter: React.FC<RiskMeterProps> = ({
  riskLevel,
  volatility,
  bankrollImpact,
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
    success: '#10B981',
    warning: '#F59E0B',
    error: '#EF4444',
    low: '#10B981',
    medium: '#F59E0B',
    high: '#EF4444',
  };

  const getRiskColor = (level: string) => {
    switch (level) {
      case 'low':
        return colors.low;
      case 'medium':
        return colors.medium;
      case 'high':
        return colors.high;
      default:
        return colors.textSecondary;
    }
  };

  const getRiskIcon = (level: string) => {
    switch (level) {
      case 'low':
        return 'shield-checkmark';
      case 'medium':
        return 'warning';
      case 'high':
        return 'alert-circle';
      default:
        return 'help-circle';
    }
  };

  const styles = StyleSheet.create({
    container: {
      backgroundColor: colors.background,
      borderRadius: 12,
      padding: 16,
      marginBottom: 16,
      borderWidth: 1,
      borderColor: colors.border,
    },
    header: {
      flexDirection: 'row',
      alignItems: 'center',
      marginBottom: 16,
    },
    title: {
      fontSize: 16,
      fontWeight: '600',
      color: colors.text,
      marginLeft: 8,
    },
    riskLevelContainer: {
      alignItems: 'center',
      marginBottom: 20,
    },
    riskLevelIcon: {
      width: 60,
      height: 60,
      borderRadius: 30,
      justifyContent: 'center',
      alignItems: 'center',
      marginBottom: 8,
    },
    riskLevelText: {
      fontSize: 18,
      fontWeight: 'bold',
      textTransform: 'uppercase',
    },
    riskLevelSubtext: {
      fontSize: 12,
      color: colors.textSecondary,
      marginTop: 2,
    },
    metricsContainer: {
      gap: 12,
    },
    metricRow: {
      flexDirection: 'row',
      justifyContent: 'space-between',
      alignItems: 'center',
    },
    metricLabel: {
      fontSize: 14,
      color: colors.textSecondary,
      flex: 1,
    },
    metricBarContainer: {
      flex: 2,
      height: 8,
      backgroundColor: colors.surface,
      borderRadius: 4,
      marginHorizontal: 12,
      overflow: 'hidden',
    },
    metricBar: {
      height: '100%',
      borderRadius: 4,
    },
    metricValue: {
      fontSize: 12,
      fontWeight: '600',
      color: colors.text,
      minWidth: 30,
      textAlign: 'right',
    },
    legend: {
      flexDirection: 'row',
      justifyContent: 'space-between',
      marginTop: 16,
      paddingTop: 12,
      borderTopWidth: 1,
      borderTopColor: colors.border,
    },
    legendItem: {
      flexDirection: 'row',
      alignItems: 'center',
    },
    legendDot: {
      width: 8,
      height: 8,
      borderRadius: 4,
      marginRight: 4,
    },
    legendText: {
      fontSize: 11,
      color: colors.textSecondary,
    },
  });

  const getMetricColor = (value: number) => {
    if (value <= 0.33) return colors.low;
    if (value <= 0.66) return colors.medium;
    return colors.high;
  };

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Icon name="analytics" size={20} color={colors.accent} />
        <Text style={styles.title}>Risk Assessment</Text>
      </View>

      {/* Risk Level Indicator */}
      <View style={styles.riskLevelContainer}>
        <View style={[
          styles.riskLevelIcon,
          { backgroundColor: getRiskColor(riskLevel) + '20' }
        ]}>
          <Icon 
            name={getRiskIcon(riskLevel)} 
            size={30} 
            color={getRiskColor(riskLevel)} 
          />
        </View>
        <Text style={[
          styles.riskLevelText,
          { color: getRiskColor(riskLevel) }
        ]}>
          {riskLevel} Risk
        </Text>
        <Text style={styles.riskLevelSubtext}>
          Overall risk assessment
        </Text>
      </View>

      {/* Risk Metrics */}
      <View style={styles.metricsContainer}>
        <View style={styles.metricRow}>
          <Text style={styles.metricLabel}>Volatility</Text>
          <View style={styles.metricBarContainer}>
            <View style={[
              styles.metricBar,
              {
                width: `${volatility * 100}%`,
                backgroundColor: getMetricColor(volatility),
              }
            ]} />
          </View>
          <Text style={styles.metricValue}>
            {(volatility * 100).toFixed(0)}%
          </Text>
        </View>

        <View style={styles.metricRow}>
          <Text style={styles.metricLabel}>Bankroll Impact</Text>
          <View style={styles.metricBarContainer}>
            <View style={[
              styles.metricBar,
              {
                width: `${bankrollImpact * 100}%`,
                backgroundColor: getMetricColor(bankrollImpact),
              }
            ]} />
          </View>
          <Text style={styles.metricValue}>
            {(bankrollImpact * 100).toFixed(0)}%
          </Text>
        </View>
      </View>

      {/* Legend */}
      <View style={styles.legend}>
        <View style={styles.legendItem}>
          <View style={[styles.legendDot, { backgroundColor: colors.low }]} />
          <Text style={styles.legendText}>Low</Text>
        </View>
        <View style={styles.legendItem}>
          <View style={[styles.legendDot, { backgroundColor: colors.medium }]} />
          <Text style={styles.legendText}>Medium</Text>
        </View>
        <View style={styles.legendItem}>
          <View style={[styles.legendDot, { backgroundColor: colors.high }]} />
          <Text style={styles.legendText}>High</Text>
        </View>
      </View>
    </View>
  );
};

export default RiskMeter;