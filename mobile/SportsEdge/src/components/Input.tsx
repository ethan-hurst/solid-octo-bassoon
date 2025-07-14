/**
 * Custom Input Component - Mobile-optimized text input
 */
import React, { useState, forwardRef } from 'react';
import {
  View,
  TextInput,
  Text,
  StyleSheet,
  TouchableOpacity,
  TextInputProps,
} from 'react-native';
import { useSelector } from 'react-redux';
import Icon from 'react-native-vector-icons/Ionicons';

import { RootState } from '../store';

interface InputProps extends TextInputProps {
  label?: string;
  error?: string;
  hint?: string;
  leftIcon?: string;
  rightIcon?: string;
  onRightIconPress?: () => void;
  variant?: 'default' | 'outlined' | 'filled';
  size?: 'small' | 'medium' | 'large';
  required?: boolean;
}

const Input = forwardRef<TextInput, InputProps>(({
  label,
  error,
  hint,
  leftIcon,
  rightIcon,
  onRightIconPress,
  variant = 'outlined',
  size = 'medium',
  required = false,
  style,
  ...props
}, ref) => {
  const theme = useSelector((state: RootState) => state.userPreferences.theme);
  const [isFocused, setIsFocused] = useState(false);

  const isDark = theme.theme === 'dark' || 
    (theme.theme === 'auto' && new Date().getHours() > 18);

  const colors = {
    background: isDark ? '#1E293B' : '#FFFFFF',
    surface: isDark ? '#334155' : '#F8FAFC',
    text: isDark ? '#F1F5F9' : '#1E293B',
    textSecondary: isDark ? '#94A3B8' : '#64748B',
    border: isDark ? '#475569' : '#D1D5DB',
    borderFocused: theme.accentColor,
    error: '#EF4444',
    success: '#10B981',
    placeholder: isDark ? '#64748B' : '#9CA3AF',
  };

  const getSizeConfig = () => {
    switch (size) {
      case 'small':
        return {
          height: 40,
          fontSize: 14,
          paddingHorizontal: 12,
          iconSize: 18,
          labelFontSize: 12,
        };
      case 'large':
        return {
          height: 56,
          fontSize: 18,
          paddingHorizontal: 16,
          iconSize: 24,
          labelFontSize: 16,
        };
      case 'medium':
      default:
        return {
          height: 48,
          fontSize: 16,
          paddingHorizontal: 14,
          iconSize: 20,
          labelFontSize: 14,
        };
    }
  };

  const sizeConfig = getSizeConfig();

  const getVariantStyles = () => {
    const baseStyle = {
      height: sizeConfig.height,
      borderRadius: 8,
      paddingHorizontal: sizeConfig.paddingHorizontal,
      fontSize: sizeConfig.fontSize,
      color: colors.text,
    };

    switch (variant) {
      case 'filled':
        return {
          ...baseStyle,
          backgroundColor: colors.surface,
          borderWidth: 0,
        };
      case 'outlined':
        return {
          ...baseStyle,
          backgroundColor: colors.background,
          borderWidth: 1,
          borderColor: error ? colors.error : isFocused ? colors.borderFocused : colors.border,
        };
      case 'default':
      default:
        return {
          ...baseStyle,
          backgroundColor: 'transparent',
          borderBottomWidth: 1,
          borderColor: error ? colors.error : isFocused ? colors.borderFocused : colors.border,
          borderRadius: 0,
        };
    }
  };

  const styles = StyleSheet.create({
    container: {
      marginBottom: 4,
    },
    labelContainer: {
      flexDirection: 'row',
      alignItems: 'center',
      marginBottom: 8,
    },
    label: {
      fontSize: sizeConfig.labelFontSize,
      fontWeight: '500',
      color: colors.text,
    },
    required: {
      color: colors.error,
      marginLeft: 2,
    },
    inputContainer: {
      flexDirection: 'row',
      alignItems: 'center',
      position: 'relative',
    },
    input: {
      flex: 1,
      ...getVariantStyles(),
      paddingLeft: leftIcon ? sizeConfig.paddingHorizontal + sizeConfig.iconSize + 8 : sizeConfig.paddingHorizontal,
      paddingRight: rightIcon ? sizeConfig.paddingHorizontal + sizeConfig.iconSize + 8 : sizeConfig.paddingHorizontal,
    },
    leftIcon: {
      position: 'absolute',
      left: sizeConfig.paddingHorizontal,
      zIndex: 1,
    },
    rightIcon: {
      position: 'absolute',
      right: sizeConfig.paddingHorizontal,
      zIndex: 1,
    },
    hint: {
      fontSize: 12,
      color: colors.textSecondary,
      marginTop: 4,
    },
    error: {
      fontSize: 12,
      color: colors.error,
      marginTop: 4,
    },
    focusedContainer: {
      // Additional styles when focused
    },
    errorContainer: {
      // Additional styles when error
    },
  });

  const handleFocus = (e: any) => {
    setIsFocused(true);
    props.onFocus?.(e);
  };

  const handleBlur = (e: any) => {
    setIsFocused(false);
    props.onBlur?.(e);
  };

  return (
    <View style={[styles.container, style]}>
      {label && (
        <View style={styles.labelContainer}>
          <Text style={styles.label}>{label}</Text>
          {required && <Text style={styles.required}>*</Text>}
        </View>
      )}
      
      <View style={[
        styles.inputContainer,
        isFocused && styles.focusedContainer,
        error && styles.errorContainer,
      ]}>
        {leftIcon && (
          <Icon
            name={leftIcon}
            size={sizeConfig.iconSize}
            color={error ? colors.error : isFocused ? colors.borderFocused : colors.textSecondary}
            style={styles.leftIcon}
          />
        )}
        
        <TextInput
          ref={ref}
          style={styles.input}
          placeholderTextColor={colors.placeholder}
          onFocus={handleFocus}
          onBlur={handleBlur}
          {...props}
        />
        
        {rightIcon && (
          <TouchableOpacity
            style={styles.rightIcon}
            onPress={onRightIconPress}
            disabled={!onRightIconPress}
          >
            <Icon
              name={rightIcon}
              size={sizeConfig.iconSize}
              color={error ? colors.error : isFocused ? colors.borderFocused : colors.textSecondary}
            />
          </TouchableOpacity>
        )}
      </View>
      
      {error && <Text style={styles.error}>{error}</Text>}
      {hint && !error && <Text style={styles.hint}>{hint}</Text>}
    </View>
  );
});

Input.displayName = 'Input';

export default Input;