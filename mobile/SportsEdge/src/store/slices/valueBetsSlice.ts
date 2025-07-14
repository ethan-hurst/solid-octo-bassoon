/**
 * Value Bets slice for mobile app
 */
import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import { apiClient } from '../../services/apiClient';

export interface QuickValueBet {
  bet_id: string;
  title: string;
  subtitle: string;
  edge: number;
  confidence: number;
  odds: number;
  sport_icon: string;
  urgency: 'high' | 'medium' | 'low';
}

export interface QuickAnalysisResult {
  bet_summary: string;
  value_score: number;
  confidence: number;
  recommendation: 'strong_bet' | 'good_bet' | 'pass' | 'avoid';
  key_insight?: string;
  quick_stats: Array<{ label: string; value: string }>;
  estimated_read_time: number;
}

interface ValueBetsState {
  feed: QuickValueBet[];
  currentAnalysis: QuickAnalysisResult | null;
  page: number;
  hasMore: boolean;
  total: number;
  isLoading: boolean;
  isRefreshing: boolean;
  isLoadingMore: boolean;
  isAnalyzing: boolean;
  error: string | null;
  filters: {
    sports: string[];
    minEdge: number;
  };
  dismissedBets: Set<string>;
}

const initialState: ValueBetsState = {
  feed: [],
  currentAnalysis: null,
  page: 1,
  hasMore: true,
  total: 0,
  isLoading: false,
  isRefreshing: false,
  isLoadingMore: false,
  isAnalyzing: false,
  error: null,
  filters: {
    sports: [],
    minEdge: 0.03,
  },
  dismissedBets: new Set(),
};

// Async thunks
export const fetchValueBetsFeed = createAsyncThunk(
  'valueBets/fetchFeed',
  async (
    { 
      page = 1, 
      refresh = false, 
      sports = [], 
      limit = 20 
    }: { 
      page?: number; 
      refresh?: boolean; 
      sports?: string[]; 
      limit?: number; 
    },
    { rejectWithValue }
  ) => {
    try {
      const params = new URLSearchParams({
        page: page.toString(),
        limit: limit.toString(),
      });

      if (sports.length > 0) {
        sports.forEach(sport => params.append('sports', sport));
      }

      const response = await apiClient.get(`/mobile/value-bets/feed?${params}`);
      
      return {
        ...response.data,
        page,
        refresh,
      };
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.detail || 'Failed to fetch value bets');
    }
  }
);

export const fetchQuickAnalysis = createAsyncThunk(
  'valueBets/fetchQuickAnalysis',
  async (betId: string, { rejectWithValue }) => {
    try {
      const response = await apiClient.get(`/mobile/quick-analysis/${betId}`);
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.detail || 'Failed to fetch analysis');
    }
  }
);

export const quickAddToBetslip = createAsyncThunk(
  'valueBets/quickAddToBetslip',
  async (
    { betId, action, sourceScreen }: { betId: string; action: string; sourceScreen: string },
    { rejectWithValue }
  ) => {
    try {
      const response = await apiClient.post('/mobile/bets/quick-add', {
        bet_id: betId,
        action,
        source_screen: sourceScreen,
      });
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.detail || 'Action failed');
    }
  }
);

const valueBetsSlice = createSlice({
  name: 'valueBets',
  initialState,
  reducers: {
    clearError: (state) => {
      state.error = null;
    },
    
    clearCurrentAnalysis: (state) => {
      state.currentAnalysis = null;
    },

    updateFilters: (state, action: PayloadAction<Partial<ValueBetsState['filters']>>) => {
      state.filters = { ...state.filters, ...action.payload };
    },

    dismissBet: (state, action: PayloadAction<string>) => {
      const betId = action.payload;
      state.dismissedBets.add(betId);
      // Remove from feed
      state.feed = state.feed.filter(bet => bet.bet_id !== betId);
    },

    undoDismissBet: (state, action: PayloadAction<string>) => {
      const betId = action.payload;
      state.dismissedBets.delete(betId);
    },

    resetFeed: (state) => {
      state.feed = [];
      state.page = 1;
      state.hasMore = true;
      state.total = 0;
    },

    clearDismissedBets: (state) => {
      state.dismissedBets.clear();
    },
  },

  extraReducers: (builder) => {
    builder
      // Fetch value bets feed
      .addCase(fetchValueBetsFeed.pending, (state, action) => {
        const { page, refresh } = action.meta.arg;
        
        if (refresh || page === 1) {
          state.isRefreshing = true;
          state.isLoading = true;
        } else {
          state.isLoadingMore = true;
        }
        state.error = null;
      })
      .addCase(fetchValueBetsFeed.fulfilled, (state, action) => {
        const { bets, total, page: requestedPage, has_more, refresh } = action.payload;
        
        state.isLoading = false;
        state.isRefreshing = false;
        state.isLoadingMore = false;
        state.total = total;
        state.hasMore = has_more;
        state.page = requestedPage;

        if (refresh || requestedPage === 1) {
          // Replace feed for refresh or first page
          state.feed = bets.filter(bet => !state.dismissedBets.has(bet.bet_id));
        } else {
          // Append for pagination
          const newBets = bets.filter(bet => !state.dismissedBets.has(bet.bet_id));
          state.feed = [...state.feed, ...newBets];
        }
      })
      .addCase(fetchValueBetsFeed.rejected, (state, action) => {
        state.isLoading = false;
        state.isRefreshing = false;
        state.isLoadingMore = false;
        state.error = action.payload as string;
      })

      // Fetch quick analysis
      .addCase(fetchQuickAnalysis.pending, (state) => {
        state.isAnalyzing = true;
        state.error = null;
      })
      .addCase(fetchQuickAnalysis.fulfilled, (state, action) => {
        state.isAnalyzing = false;
        state.currentAnalysis = action.payload;
      })
      .addCase(fetchQuickAnalysis.rejected, (state, action) => {
        state.isAnalyzing = false;
        state.error = action.payload as string;
      })

      // Quick add to betslip
      .addCase(quickAddToBetslip.fulfilled, (state, action) => {
        // Handle successful bet addition
        // You might want to show a success message or update UI state
      })
      .addCase(quickAddToBetslip.rejected, (state, action) => {
        state.error = action.payload as string;
      });
  },
});

export const {
  clearError,
  clearCurrentAnalysis,
  updateFilters,
  dismissBet,
  undoDismissBet,
  resetFeed,
  clearDismissedBets,
} = valueBetsSlice.actions;

export default valueBetsSlice.reducer;