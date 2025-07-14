/**
 * Filter Button Component
 */
import React from 'react';
import {
  TouchableOpacity,
  Text,
  StyleSheet,
} from 'react-native';
import { useSelector } from 'react-redux';
import Icon from 'react-native-vector-icons/Ionicons';

import { RootState } from '../store';

interface FilterButtonProps {
  title: string;
  active: boolean;
  onPress: () => void;
  icon?: string;
}

const FilterButton: React.FC<FilterButtonProps> = ({
  title,
  active,
  onPress,
  icon = 'options-outline',
}) => {
  const theme = useSelector((state: RootState) => state.userPreferences.theme);

  const isDark = theme.theme === 'dark' || 
    (theme.theme === 'auto' && new Date().getHours() > 18);

  const colors = {
    background: isDark ? '#334155' : '#F1F5F9',
    activeBackground: theme.accentColor,
    text: isDark ? '#F1F5F9' : '#1E293B',
    activeText: '#FFFFFF',
    border: isDark ? '#475569' : '#E2E8F0',
  };

  const styles = StyleSheet.create({
    button: {
      flexDirection: 'row',
      alignItems: 'center',
      paddingHorizontal: 12,
      paddingVertical: 8,
      borderRadius: 20,
      marginRight: 8,
      borderWidth: 1,
      borderColor: active ? theme.accentColor : colors.border,
      backgroundColor: active ? colors.activeBackground : colors.background,
    },
    text: {
      fontSize: 13,
      fontWeight: '500',
      color: active ? colors.activeText : colors.text,
      marginLeft: 4,
    },
  });

  return (
    <TouchableOpacity 
      style={styles.button} 
      onPress={onPress}
      activeOpacity={0.7}
    >
      <Icon 
        name={icon} 
        size={14} 
        color={active ? colors.activeText : colors.text} 
      />
      <Text style={styles.text}>{title}</Text>
    </TouchableOpacity>
  );
};

export default FilterButton;