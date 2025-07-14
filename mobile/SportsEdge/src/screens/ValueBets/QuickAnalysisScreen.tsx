/**
 * Quick Analysis Screen - Instant bet analysis with AI insights
 */
import React, { useEffect, useState, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
  Dimensions,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useSelector, useDispatch } from 'react-redux';
import { useRoute, useNavigation } from '@react-navigation/native';
import Icon from 'react-native-vector-icons/Ionicons';

import { RootState } from '../../store';
import { ValueBetsStackScreenProps } from '../../navigation/types';
import { apiClient } from '../../services';

// Components
import AnalysisCard from '../../components/AnalysisCard';
import RiskMeter from '../../components/RiskMeter';
import ConfidenceIndicator from '../../components/ConfidenceIndicator';
import ActionButtons from '../../components/ActionButtons';

type Props = ValueBetsStackScreenProps<'QuickAnalysis'>;

interface QuickAnalysisData {
  bet_id: string;
  edge_analysis: {
    calculated_edge: number;
    confidence_score: number;
    expected_value: number;
    implied_probability: number;
    fair_probability: number;
  };
  risk_assessment: {
    risk_level: 'low' | 'medium' | 'high';
    volatility: number;
    bankroll_impact: number;
    variance: number;
  };
  market_insights: {
    line_movement: string;
    public_betting_percentage: number;
    sharp_money_indicator: boolean;
    market_efficiency: number;
  };
  recommendation: {
    action: 'strong_bet' | 'bet' | 'pass' | 'avoid';
    suggested_stake: number;
    max_stake: number;
    reasoning: string[];
  };
  historical_performance: {
    similar_bets_roi: number;
    win_rate: number;
    sample_size: number;
  };
}

const QuickAnalysisScreen: React.FC<Props> = ({ navigation, route }) => {
  const { betId } = route.params;
  const dispatch = useDispatch();
  const theme = useSelector((state: RootState) => state.userPreferences.theme);
  const betting = useSelector((state: RootState) => state.userPreferences.betting);

  const [analysisData, setAnalysisData] = useState<QuickAnalysisData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const isDark = theme.theme === 'dark' || 
    (theme.theme === 'auto' && new Date().getHours() > 18);

  const colors = {
    background: isDark ? '#0F172A' : '#FFFFFF',
    surface: isDark ? '#1E293B' : '#F8FAFC',
    text: isDark ? '#F1F5F9' : '#1E293B',
    textSecondary: isDark ? '#94A3B8' : '#64748B',
    border: isDark ? '#334155' : '#E2E8F0',
    accent: theme.accentColor,
    success: '#10B981',
    warning: '#F59E0B',
    error: '#EF4444',
  };

  const styles = StyleSheet.create({
    container: {
      flex: 1,
      backgroundColor: colors.background,
    },
    header: {
      flexDirection: 'row',
      justifyContent: 'space-between',
      alignItems: 'center',
      paddingHorizontal: 16,
      paddingVertical: 12,
      borderBottomWidth: 1,
      borderBottomColor: colors.border,
    },
    headerTitle: {
      fontSize: 20,
      fontWeight: '600',
      color: colors.text,
    },
    closeButton: {
      padding: 8,
    },
    content: {
      flex: 1,
    },
    loadingContainer: {
      flex: 1,
      justifyContent: 'center',
      alignItems: 'center',
      paddingHorizontal: 32,
    },
    loadingText: {
      fontSize: 16,
      color: colors.textSecondary,
      marginTop: 16,
      textAlign: 'center',
    },
    errorContainer: {
      flex: 1,
      justifyContent: 'center',
      alignItems: 'center',
      paddingHorizontal: 32,
    },
    errorText: {
      fontSize: 16,
      color: colors.error,
      textAlign: 'center',
      marginBottom: 24,
    },
    retryButton: {
      backgroundColor: colors.accent,
      paddingHorizontal: 24,
      paddingVertical: 12,
      borderRadius: 8,
    },
    retryButtonText: {
      color: '#FFFFFF',
      fontSize: 16,
      fontWeight: '600',
    },
    scrollContent: {
      padding: 16,
    },
    sectionTitle: {
      fontSize: 18,
      fontWeight: '600',
      color: colors.text,
      marginBottom: 12,
      marginTop: 20,
    },
    summaryCard: {
      backgroundColor: colors.surface,
      borderRadius: 12,
      padding: 16,
      marginBottom: 16,
      borderWidth: 1,
      borderColor: colors.border,
    },
    summaryHeader: {
      flexDirection: 'row',
      justifyContent: 'space-between',
      alignItems: 'center',
      marginBottom: 12,
    },
    summaryTitle: {
      fontSize: 16,
      fontWeight: '600',
      color: colors.text,
    },
    edgeValue: {
      fontSize: 24,
      fontWeight: 'bold',
      color: colors.success,
    },
    metricsGrid: {
      flexDirection: 'row',
      flexWrap: 'wrap',
      justifyContent: 'space-between',
    },
    metricItem: {
      width: '48%',
      backgroundColor: colors.background,
      borderRadius: 8,
      padding: 12,
      marginBottom: 8,
      borderWidth: 1,
      borderColor: colors.border,
    },
    metricLabel: {
      fontSize: 12,
      color: colors.textSecondary,
      marginBottom: 4,
    },
    metricValue: {
      fontSize: 16,
      fontWeight: '600',
      color: colors.text,
    },
    recommendationCard: {
      backgroundColor: colors.surface,
      borderRadius: 12,
      padding: 16,
      marginBottom: 16,
      borderWidth: 2,
    },
    recommendationHeader: {
      flexDirection: 'row',
      alignItems: 'center',
      marginBottom: 12,
    },
    recommendationText: {
      fontSize: 18,
      fontWeight: 'bold',
      marginLeft: 8,
    },
    reasoningList: {
      marginTop: 8,
    },
    reasoningItem: {
      flexDirection: 'row',
      alignItems: 'flex-start',
      marginBottom: 6,
    },
    reasoningText: {
      fontSize: 14,
      color: colors.textSecondary,
      marginLeft: 8,
      flex: 1,
    },
    stakeInfo: {
      backgroundColor: colors.background,
      borderRadius: 8,
      padding: 12,
      marginTop: 12,
    },
    stakeRow: {
      flexDirection: 'row',
      justifyContent: 'space-between',
      marginBottom: 4,
    },
    stakeLabel: {
      fontSize: 14,
      color: colors.textSecondary,
    },
    stakeValue: {
      fontSize: 14,
      fontWeight: '600',
      color: colors.text,
    },
  });

  useEffect(() => {
    loadAnalysis();
  }, [betId]);

  const loadAnalysis = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      
      const response = await apiClient.getQuickAnalysis(betId);
      setAnalysisData(response.data);
    } catch (error: any) {
      console.error('Error loading quick analysis:', error);
      setError(error.message || 'Failed to load analysis');
    } finally {
      setIsLoading(false);
    }
  }, [betId]);

  const handleClose = useCallback(() => {
    navigation.goBack();
  }, [navigation]);

  const handleRetry = useCallback(() => {
    loadAnalysis();
  }, [loadAnalysis]);

  const getRecommendationColor = (action: string) => {
    switch (action) {
      case 'strong_bet':
        return colors.success;
      case 'bet':
        return colors.accent;
      case 'pass':
        return colors.warning;
      case 'avoid':
        return colors.error;
      default:
        return colors.textSecondary;
    }
  };

  const getRecommendationIcon = (action: string) => {
    switch (action) {
      case 'strong_bet':
        return 'checkmark-circle';
      case 'bet':
        return 'thumbs-up';
      case 'pass':
        return 'pause-circle';
      case 'avoid':
        return 'close-circle';
      default:
        return 'help-circle';
    }
  };

  const getRecommendationText = (action: string) => {
    switch (action) {
      case 'strong_bet':
        return 'STRONG BET';
      case 'bet':
        return 'BET';
      case 'pass':
        return 'PASS';
      case 'avoid':
        return 'AVOID';
      default:
        return 'UNKNOWN';
    }
  };

  if (isLoading) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.header}>
          <Text style={styles.headerTitle}>Quick Analysis</Text>
          <TouchableOpacity style={styles.closeButton} onPress={handleClose}>
            <Icon name="close" size={24} color={colors.text} />
          </TouchableOpacity>
        </View>
        
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={colors.accent} />
          <Text style={styles.loadingText}>
            Analyzing bet opportunity...{'\n'}
            Calculating edge, risk, and market insights
          </Text>
        </View>
      </SafeAreaView>
    );
  }

  if (error || !analysisData) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.header}>
          <Text style={styles.headerTitle}>Quick Analysis</Text>
          <TouchableOpacity style={styles.closeButton} onPress={handleClose}>
            <Icon name="close" size={24} color={colors.text} />
          </TouchableOpacity>
        </View>
        
        <View style={styles.errorContainer}>
          <Text style={styles.errorText}>
            {error || 'Failed to load analysis data'}
          </Text>
          <TouchableOpacity style={styles.retryButton} onPress={handleRetry}>
            <Text style={styles.retryButtonText}>Try Again</Text>
          </TouchableOpacity>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Quick Analysis</Text>
        <TouchableOpacity style={styles.closeButton} onPress={handleClose}>
          <Icon name="close" size={24} color={colors.text} />
        </TouchableOpacity>
      </View>

      <ScrollView style={styles.content} contentContainerStyle={styles.scrollContent}>
        {/* Summary */}
        <View style={styles.summaryCard}>
          <View style={styles.summaryHeader}>
            <Text style={styles.summaryTitle}>Edge Analysis</Text>
            <Text style={styles.edgeValue}>
              {(analysisData.edge_analysis.calculated_edge * 100).toFixed(1)}%
            </Text>
          </View>
          
          <View style={styles.metricsGrid}>
            <View style={styles.metricItem}>
              <Text style={styles.metricLabel}>Confidence</Text>
              <Text style={styles.metricValue}>
                {(analysisData.edge_analysis.confidence_score * 100).toFixed(0)}%
              </Text>
            </View>
            <View style={styles.metricItem}>
              <Text style={styles.metricLabel}>Expected Value</Text>
              <Text style={styles.metricValue}>
                ${analysisData.edge_analysis.expected_value.toFixed(2)}
              </Text>
            </View>
            <View style={styles.metricItem}>
              <Text style={styles.metricLabel}>Fair Probability</Text>
              <Text style={styles.metricValue}>
                {(analysisData.edge_analysis.fair_probability * 100).toFixed(1)}%
              </Text>
            </View>
            <View style={styles.metricItem}>
              <Text style={styles.metricLabel}>Implied Probability</Text>
              <Text style={styles.metricValue}>
                {(analysisData.edge_analysis.implied_probability * 100).toFixed(1)}%
              </Text>
            </View>
          </View>
        </View>

        {/* Risk Assessment */}
        <Text style={styles.sectionTitle}>Risk Assessment</Text>
        <RiskMeter
          riskLevel={analysisData.risk_assessment.risk_level}
          volatility={analysisData.risk_assessment.volatility}
          bankrollImpact={analysisData.risk_assessment.bankroll_impact}
        />

        {/* Market Insights */}
        <Text style={styles.sectionTitle}>Market Insights</Text>
        <AnalysisCard
          title="Market Analysis"
          data={[
            {
              label: 'Line Movement',
              value: analysisData.market_insights.line_movement,
            },
            {
              label: 'Public Betting',
              value: `${analysisData.market_insights.public_betting_percentage}%`,
            },
            {
              label: 'Sharp Money',
              value: analysisData.market_insights.sharp_money_indicator ? 'Yes' : 'No',
            },
            {
              label: 'Market Efficiency',
              value: `${(analysisData.market_insights.market_efficiency * 100).toFixed(0)}%`,
            },
          ]}
        />

        {/* Historical Performance */}
        <Text style={styles.sectionTitle}>Historical Performance</Text>
        <AnalysisCard
          title="Similar Bets"
          data={[
            {
              label: 'ROI',
              value: `${(analysisData.historical_performance.similar_bets_roi * 100).toFixed(1)}%`,
            },
            {
              label: 'Win Rate',
              value: `${(analysisData.historical_performance.win_rate * 100).toFixed(1)}%`,
            },
            {
              label: 'Sample Size',
              value: analysisData.historical_performance.sample_size.toString(),
            },
          ]}
        />

        {/* Recommendation */}
        <Text style={styles.sectionTitle}>Recommendation</Text>
        <View 
          style={[
            styles.recommendationCard, 
            { borderColor: getRecommendationColor(analysisData.recommendation.action) }
          ]}
        >
          <View style={styles.recommendationHeader}>
            <Icon 
              name={getRecommendationIcon(analysisData.recommendation.action)} 
              size={24} 
              color={getRecommendationColor(analysisData.recommendation.action)} 
            />
            <Text 
              style={[
                styles.recommendationText, 
                { color: getRecommendationColor(analysisData.recommendation.action) }
              ]}
            >
              {getRecommendationText(analysisData.recommendation.action)}
            </Text>
          </View>

          <View style={styles.reasoningList}>
            {analysisData.recommendation.reasoning.map((reason, index) => (
              <View key={index} style={styles.reasoningItem}>
                <Icon name="checkmark" size={14} color={colors.success} />
                <Text style={styles.reasoningText}>{reason}</Text>
              </View>
            ))}
          </View>

          <View style={styles.stakeInfo}>
            <View style={styles.stakeRow}>
              <Text style={styles.stakeLabel}>Suggested Stake:</Text>
              <Text style={styles.stakeValue}>
                ${analysisData.recommendation.suggested_stake.toFixed(0)}
              </Text>
            </View>
            <View style={styles.stakeRow}>
              <Text style={styles.stakeLabel}>Maximum Stake:</Text>
              <Text style={styles.stakeValue}>
                ${analysisData.recommendation.max_stake.toFixed(0)}
              </Text>
            </View>
          </View>
        </View>

        {/* Action Buttons */}
        <ActionButtons
          betId={betId}
          recommendation={analysisData.recommendation}
          onClose={handleClose}
        />
      </ScrollView>
    </SafeAreaView>
  );
};

export default QuickAnalysisScreen;