/**
 * SportsEdge Mobile App
 * Real-time sports betting edge finder with AI analysis
 */

import React, { useEffect } from 'react';
import { StatusBar, StyleSheet, View } from 'react-native';
import { Provider } from 'react-redux';
import { NavigationContainer } from '@react-navigation/native';

import { store } from './src/store';
import { AppNavigator } from './src/navigation/AppNavigator';
import { crashReportingService } from './src/services';

function App() {
  useEffect(() => {
    // Initialize crash reporting
    crashReportingService.initialize();
  }, []);

  return (
    <Provider store={store}>
      <NavigationContainer>
        <View style={styles.container}>
          <StatusBar 
            barStyle="light-content" 
            backgroundColor="#0F172A"
            translucent
          />
          <AppNavigator />
        </View>
      </NavigationContainer>
    </Provider>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0F172A',
  },
});

export default App;
