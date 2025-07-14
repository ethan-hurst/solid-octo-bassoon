/**
 * Button Component Tests
 */
import React from 'react';
import { render, fireEvent, screen } from '@testing-library/react-native';
import { Provider } from 'react-redux';
import { createStore } from '@reduxjs/toolkit';

import Button from '../../src/components/Button';

// Mock store with theme configuration
const mockStore = createStore(() => ({
  userPreferences: {
    theme: {
      theme: 'light',
      accentColor: '#3B82F6',
    },
  },
}));

const MockedButton = (props: any) => (
  <Provider store={mockStore}>
    <Button {...props} />
  </Provider>
);

describe('Button Component', () => {
  it('renders correctly with title', () => {
    const mockOnPress = jest.fn();
    render(
      <MockedButton 
        title="Test Button" 
        onPress={mockOnPress} 
      />
    );
    
    expect(screen.getByText('Test Button')).toBeTruthy();
  });

  it('calls onPress when pressed', () => {
    const mockOnPress = jest.fn();
    render(
      <MockedButton 
        title="Press Me" 
        onPress={mockOnPress} 
      />
    );
    
    fireEvent.press(screen.getByText('Press Me'));
    expect(mockOnPress).toHaveBeenCalledTimes(1);
  });

  it('renders loading state correctly', () => {
    const mockOnPress = jest.fn();
    render(
      <MockedButton 
        title="Loading Button" 
        onPress={mockOnPress}
        loading={true}
      />
    );
    
    expect(screen.getByText('Loading...')).toBeTruthy();
  });

  it('does not call onPress when disabled', () => {
    const mockOnPress = jest.fn();
    render(
      <MockedButton 
        title="Disabled Button" 
        onPress={mockOnPress}
        disabled={true}
      />
    );
    
    fireEvent.press(screen.getByText('Disabled Button'));
    expect(mockOnPress).not.toHaveBeenCalled();
  });

  it('renders icon correctly', () => {
    const mockOnPress = jest.fn();
    render(
      <MockedButton 
        title="Icon Button" 
        onPress={mockOnPress}
        icon="star"
      />
    );
    
    expect(screen.getByText('Icon Button')).toBeTruthy();
  });

  it('applies correct variant styles', () => {
    const mockOnPress = jest.fn();
    
    // Test primary variant
    const { rerender } = render(
      <MockedButton 
        title="Primary Button" 
        onPress={mockOnPress}
        variant="primary"
      />
    );
    expect(screen.getByText('Primary Button')).toBeTruthy();
    
    // Test secondary variant
    rerender(
      <MockedButton 
        title="Secondary Button" 
        onPress={mockOnPress}
        variant="secondary"
      />
    );
    expect(screen.getByText('Secondary Button')).toBeTruthy();
    
    // Test outline variant
    rerender(
      <MockedButton 
        title="Outline Button" 
        onPress={mockOnPress}
        variant="outline"
      />
    );
    expect(screen.getByText('Outline Button')).toBeTruthy();
  });

  it('applies correct size configurations', () => {
    const mockOnPress = jest.fn();
    
    // Test small size
    const { rerender } = render(
      <MockedButton 
        title="Small Button" 
        onPress={mockOnPress}
        size="small"
      />
    );
    expect(screen.getByText('Small Button')).toBeTruthy();
    
    // Test large size
    rerender(
      <MockedButton 
        title="Large Button" 
        onPress={mockOnPress}
        size="large"
      />
    );
    expect(screen.getByText('Large Button')).toBeTruthy();
  });
});