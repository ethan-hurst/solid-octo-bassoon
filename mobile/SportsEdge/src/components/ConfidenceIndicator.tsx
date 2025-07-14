/**
 * Confidence Indicator Component - Shows confidence score with visual feedback
 */
import React from 'react';
import {
  View,
  Text,
  StyleSheet,
} from 'react-native';
import { useSelector } from 'react-redux';
import Icon from 'react-native-vector-icons/Ionicons';

import { RootState } from '../store';

interface ConfidenceIndicatorProps {
  confidence: number; // 0-1
  size?: 'small' | 'medium' | 'large';
  showLabel?: boolean;
}

const ConfidenceIndicator: React.FC<ConfidenceIndicatorProps> = ({
  confidence,
  size = 'medium',
  showLabel = true,
}) => {
  const theme = useSelector((state: RootState) => state.userPreferences.theme);

  const isDark = theme.theme === 'dark' || 
    (theme.theme === 'auto' && new Date().getHours() > 18);

  const colors = {
    background: isDark ? '#1E293B' : '#FFFFFF',
    text: isDark ? '#F1F5F9' : '#1E293B',
    textSecondary: isDark ? '#94A3B8' : '#64748B',
    border: isDark ? '#475569' : '#E2E8F0',
    success: '#10B981',
    warning: '#F59E0B',
    error: '#EF4444',
  };

  const getConfidenceColor = (conf: number) => {
    if (conf >= 0.8) return colors.success;
    if (conf >= 0.6) return colors.warning;
    return colors.error;
  };

  const getConfidenceLabel = (conf: number) => {
    if (conf >= 0.8) return 'High Confidence';
    if (conf >= 0.6) return 'Medium Confidence';
    return 'Low Confidence';
  };

  const getConfidenceIcon = (conf: number) => {
    if (conf >= 0.8) return 'checkmark-circle';
    if (conf >= 0.6) return 'warning';
    return 'alert-circle';
  };

  const getSizeConfig = () => {
    switch (size) {
      case 'small':
        return {
          containerSize: 40,
          iconSize: 20,
          fontSize: 12,
          strokeWidth: 3,
        };
      case 'large':
        return {
          containerSize: 80,
          iconSize: 40,
          fontSize: 18,
          strokeWidth: 6,
        };
      case 'medium':
      default:
        return {
          containerSize: 60,
          iconSize: 30,
          fontSize: 14,
          strokeWidth: 4,
        };
    }
  };

  const sizeConfig = getSizeConfig();
  const confidenceColor = getConfidenceColor(confidence);
  const confidencePercentage = confidence * 100;

  const styles = StyleSheet.create({
    container: {
      alignItems: 'center',
    },
    circleContainer: {
      width: sizeConfig.containerSize,
      height: sizeConfig.containerSize,
      position: 'relative',
      justifyContent: 'center',
      alignItems: 'center',
    },
    backgroundCircle: {
      position: 'absolute',
      width: sizeConfig.containerSize,
      height: sizeConfig.containerSize,
      borderRadius: sizeConfig.containerSize / 2,
      borderWidth: sizeConfig.strokeWidth,
      borderColor: colors.border,
    },
    progressCircle: {
      position: 'absolute',
      width: sizeConfig.containerSize,
      height: sizeConfig.containerSize,
      borderRadius: sizeConfig.containerSize / 2,
      borderWidth: sizeConfig.strokeWidth,
      borderTopColor: confidenceColor,
      borderRightColor: confidenceColor,
      borderBottomColor: confidenceColor,
      borderLeftColor: 'transparent',
      transform: [{ rotate: '-90deg' }],
    },
    iconContainer: {
      justifyContent: 'center',
      alignItems: 'center',
    },
    percentageText: {
      fontSize: sizeConfig.fontSize,
      fontWeight: 'bold',
      color: confidenceColor,
      marginTop: 4,
    },
    labelText: {
      fontSize: sizeConfig.fontSize - 2,
      color: colors.textSecondary,
      marginTop: 4,
      textAlign: 'center',
    },
  });

  // Calculate the rotation for the progress circle
  const rotation = (confidence * 360) - 90;
  const progressStyle = {
    ...styles.progressCircle,
    transform: [
      { rotate: '-90deg' },
      { rotateZ: `${Math.min(rotation + 90, 360)}deg` }
    ],
  };

  return (
    <View style={styles.container}>
      <View style={styles.circleContainer}>
        <View style={styles.backgroundCircle} />
        {confidence > 0 && (
          <View style={progressStyle} />
        )}
        <View style={styles.iconContainer}>
          <Icon 
            name={getConfidenceIcon(confidence)} 
            size={sizeConfig.iconSize} 
            color={confidenceColor} 
          />
        </View>
      </View>
      
      <Text style={styles.percentageText}>
        {confidencePercentage.toFixed(0)}%
      </Text>
      
      {showLabel && (
        <Text style={styles.labelText}>
          {getConfidenceLabel(confidence)}
        </Text>
      )}
    </View>
  );
};

export default ConfidenceIndicator;