/**
 * Live Games slice for mobile app
 */
import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { apiClient } from '../../services/apiClient';

export interface LiveGameMobile {
  game_id: string;
  sport: string;
  home_team: string;
  away_team: string;
  score: { home: number; away: number };
  time_remaining: string;
  live_bets_available: number;
  value_bets_count: number;
  is_followed: boolean;
}

interface LiveGamesState {
  games: LiveGameMobile[];
  followedGames: Set<string>;
  isLoading: boolean;
  error: string | null;
  lastUpdated: number | null;
}

const initialState: LiveGamesState = {
  games: [],
  followedGames: new Set(),
  isLoading: false,
  error: null,
  lastUpdated: null,
};

export const fetchLiveGames = createAsyncThunk(
  'liveGames/fetchLiveGames',
  async (sports?: string[], { rejectWithValue }) => {
    try {
      const params = new URLSearchParams();
      if (sports && sports.length > 0) {
        sports.forEach(sport => params.append('sports', sport));
      }

      const response = await apiClient.get(`/mobile/games/live?${params}`);
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.detail || 'Failed to fetch live games');
    }
  }
);

const liveGamesSlice = createSlice({
  name: 'liveGames',
  initialState,
  reducers: {
    toggleFollowGame: (state, action) => {
      const gameId = action.payload;
      if (state.followedGames.has(gameId)) {
        state.followedGames.delete(gameId);
      } else {
        state.followedGames.add(gameId);
      }
      
      // Update the game in the list
      const game = state.games.find(g => g.game_id === gameId);
      if (game) {
        game.is_followed = state.followedGames.has(gameId);
      }
    },
    
    clearError: (state) => {
      state.error = null;
    },
  },

  extraReducers: (builder) => {
    builder
      .addCase(fetchLiveGames.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(fetchLiveGames.fulfilled, (state, action) => {
        state.isLoading = false;
        state.games = action.payload;
        state.lastUpdated = Date.now();
      })
      .addCase(fetchLiveGames.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
      });
  },
});

export const { toggleFollowGame, clearError } = liveGamesSlice.actions;
export default liveGamesSlice.reducer;