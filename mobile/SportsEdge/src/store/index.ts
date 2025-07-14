/**
 * Redux store configuration for Sports Edge mobile app
 */
import { configureStore } from '@reduxjs/toolkit';
import { TypedUseSelectorHook, useDispatch, useSelector } from 'react-redux';

// Import slices
import authSlice from './slices/authSlice';
import valueBetsSlice from './slices/valueBetsSlice';
import liveGamesSlice from './slices/liveGamesSlice';
import notificationsSlice from './slices/notificationsSlice';
import offlineSlice from './slices/offlineSlice';
import userPreferencesSlice from './slices/userPreferencesSlice';

export const store = configureStore({
  reducer: {
    auth: authSlice,
    valueBets: valueBetsSlice,
    liveGames: liveGamesSlice,
    notifications: notificationsSlice,
    offline: offlineSlice,
    userPreferences: userPreferencesSlice,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        ignoredActions: ['persist/PERSIST', 'persist/REHYDRATE'],
      },
    }),
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;

// Typed hooks
export const useAppDispatch = () => useDispatch<AppDispatch>();
export const useAppSelector: TypedUseSelectorHook<RootState> = useSelector;