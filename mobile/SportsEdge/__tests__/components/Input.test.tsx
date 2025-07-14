/**
 * Input Component Tests
 */
import React from 'react';
import { render, fireEvent, screen } from '@testing-library/react-native';
import { Provider } from 'react-redux';
import { createStore } from '@reduxjs/toolkit';

import Input from '../../src/components/Input';

// Mock store with theme configuration
const mockStore = createStore(() => ({
  userPreferences: {
    theme: {
      theme: 'light',
      accentColor: '#3B82F6',
    },
  },
}));

const MockedInput = (props: any) => (
  <Provider store={mockStore}>
    <Input {...props} />
  </Provider>
);

describe('Input Component', () => {
  it('renders correctly with placeholder', () => {
    render(
      <MockedInput 
        placeholder="Enter text"
        onChangeText={jest.fn()}
      />
    );
    
    expect(screen.getByPlaceholderText('Enter text')).toBeTruthy();
  });

  it('renders with label', () => {
    render(
      <MockedInput 
        label="Username"
        placeholder="Enter username"
        onChangeText={jest.fn()}
      />
    );
    
    expect(screen.getByText('Username')).toBeTruthy();
  });

  it('shows required indicator when required', () => {
    render(
      <MockedInput 
        label="Required Field"
        required={true}
        onChangeText={jest.fn()}
      />
    );
    
    expect(screen.getByText('Required Field')).toBeTruthy();
    expect(screen.getByText('*')).toBeTruthy();
  });

  it('displays error message', () => {
    render(
      <MockedInput 
        label="Email"
        error="Invalid email format"
        onChangeText={jest.fn()}
      />
    );
    
    expect(screen.getByText('Invalid email format')).toBeTruthy();
  });

  it('displays hint when no error', () => {
    render(
      <MockedInput 
        label="Password"
        hint="Must be at least 8 characters"
        onChangeText={jest.fn()}
      />
    );
    
    expect(screen.getByText('Must be at least 8 characters')).toBeTruthy();
  });

  it('calls onChangeText when text changes', () => {
    const mockOnChangeText = jest.fn();
    render(
      <MockedInput 
        placeholder="Type here"
        onChangeText={mockOnChangeText}
      />
    );
    
    const input = screen.getByPlaceholderText('Type here');
    fireEvent.changeText(input, 'test input');
    
    expect(mockOnChangeText).toHaveBeenCalledWith('test input');
  });

  it('applies correct variant styles', () => {
    const { rerender } = render(
      <MockedInput 
        placeholder="Default Input"
        variant="default"
        onChangeText={jest.fn()}
      />
    );
    expect(screen.getByPlaceholderText('Default Input')).toBeTruthy();
    
    rerender(
      <MockedInput 
        placeholder="Outlined Input"
        variant="outlined"
        onChangeText={jest.fn()}
      />
    );
    expect(screen.getByPlaceholderText('Outlined Input')).toBeTruthy();
    
    rerender(
      <MockedInput 
        placeholder="Filled Input"
        variant="filled"
        onChangeText={jest.fn()}
      />
    );
    expect(screen.getByPlaceholderText('Filled Input')).toBeTruthy();
  });

  it('handles focus and blur events', () => {
    const mockOnFocus = jest.fn();
    const mockOnBlur = jest.fn();
    
    render(
      <MockedInput 
        placeholder="Focus test"
        onFocus={mockOnFocus}
        onBlur={mockOnBlur}
        onChangeText={jest.fn()}
      />
    );
    
    const input = screen.getByPlaceholderText('Focus test');
    
    fireEvent(input, 'focus');
    expect(mockOnFocus).toHaveBeenCalled();
    
    fireEvent(input, 'blur');
    expect(mockOnBlur).toHaveBeenCalled();
  });

  it('renders with left and right icons', () => {
    const mockRightIconPress = jest.fn();
    
    render(
      <MockedInput 
        placeholder="Icon input"
        leftIcon="search"
        rightIcon="close"
        onRightIconPress={mockRightIconPress}
        onChangeText={jest.fn()}
      />
    );
    
    expect(screen.getByPlaceholderText('Icon input')).toBeTruthy();
  });
});