# Sports Betting Edge Finder - Frontend Planning Document

## 🎯 Frontend Overview

A modern, responsive web application that provides an intuitive interface for sports betting analysis, real-time alerts, and portfolio management.

## 🏗️ Technology Stack

### Core Framework
- **React 18+** - Component-based UI with hooks
- **TypeScript** - Type safety and better developer experience
- **Vite** - Fast build tool and dev server
- **React Router v6** - Client-side routing

### State Management
- **Zustand** - Lightweight state management
- **React Query (TanStack Query)** - Server state and caching
- **WebSocket Context** - Real-time updates management

### UI Framework & Styling
- **Tailwind CSS** - Utility-first CSS framework
- **Headless UI** - Unstyled, accessible components
- **Framer Motion** - Smooth animations
- **Chart.js/Recharts** - Data visualization

### Development Tools
- **ESLint** - Code linting
- **Prettier** - Code formatting
- **Vitest** - Unit testing
- **Playwright** - E2E testing

## 📁 Project Structure

```
frontend/
├── public/                 # Static assets
├── src/
│   ├── components/        # Reusable components
│   │   ├── common/       # Buttons, inputs, cards
│   │   ├── layout/       # Header, sidebar, footer
│   │   ├── charts/       # Data visualization
│   │   └── forms/        # Form components
│   ├── pages/            # Route components
│   │   ├── Dashboard/    # Main dashboard
│   │   ├── Odds/         # Live odds display
│   │   ├── Analysis/     # Value bets & arbitrage
│   │   ├── Alerts/       # Alert management
│   │   ├── Portfolio/    # Bet tracking
│   │   └── Settings/     # User preferences
│   ├── hooks/            # Custom React hooks
│   ├── services/         # API integration
│   ├── stores/           # Zustand stores
│   ├── types/            # TypeScript types
│   ├── utils/            # Helper functions
│   └── App.tsx           # Root component
├── tests/                # Test files
└── package.json          # Dependencies
```

## 🎨 UI/UX Design Principles

### Visual Design
- **Dark Mode First** - Primary dark theme with light mode option
- **Data-Dense** - Efficient use of space for information
- **High Contrast** - Clear readability for numbers/odds
- **Status Colors** - Green (positive), Red (negative), Blue (info)

### User Experience
- **Real-Time Updates** - Live data without page refreshes
- **Responsive Design** - Mobile, tablet, and desktop layouts
- **Quick Actions** - One-click betting, alerts, analysis
- **Keyboard Shortcuts** - Power user productivity

## 📱 Core Features & Pages

### 1. Dashboard
- **Overview Cards** - Active bets, P&L, win rate
- **Live Opportunities** - Real-time value bets
- **Recent Activity** - Bet history, alerts
- **Quick Stats** - Performance metrics

### 2. Live Odds Page
- **Multi-Sport View** - NBA, NFL, MLB tabs
- **Odds Comparison Table** - Multiple bookmakers
- **Live Updates** - WebSocket-powered changes
- **Filters** - Sport, league, bet type
- **Quick Bet** - One-click bet placement

### 3. Analysis Center
- **Value Bet Scanner** - Real-time opportunities
- **Arbitrage Finder** - Cross-bookmaker analysis
- **Edge Calculator** - Manual bet analysis
- **Model Predictions** - ML confidence scores

### 4. Alert Management
- **Active Alerts** - Current subscriptions
- **Alert History** - Past notifications
- **Preferences** - Thresholds, channels
- **Quick Subscribe** - Game/team alerts

### 5. Portfolio Tracker
- **Active Bets** - Open positions
- **Bet History** - Completed bets
- **Performance Charts** - P&L over time
- **Bankroll Management** - Kelly sizing

### 6. Settings
- **Profile** - User information
- **Preferences** - Odds format, timezone
- **Notifications** - Channel settings
- **API Keys** - Bookmaker integrations

## 🔌 API Integration

### HTTP Client Setup
```typescript
// services/api.ts
import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for auth
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('authToken');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});
```

### WebSocket Integration
```typescript
// services/websocket.ts
export class WebSocketService {
  private ws: WebSocket | null = null;
  
  connect(onMessage: (data: any) => void) {
    this.ws = new WebSocket('ws://localhost:8000/ws');
    
    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      onMessage(data);
    };
  }
  
  subscribe(topic: string) {
    this.ws?.send(JSON.stringify({
      type: 'subscribe',
      topic
    }));
  }
}
```

## 🎯 Component Examples

### Value Bet Card Component
```typescript
// components/cards/ValueBetCard.tsx
interface ValueBetCardProps {
  bet: ValueBet;
  onPlace: (bet: ValueBet) => void;
}

export const ValueBetCard: React.FC<ValueBetCardProps> = ({ bet, onPlace }) => {
  return (
    <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
      <div className="flex justify-between items-start mb-2">
        <h3 className="text-lg font-semibold">{bet.selection}</h3>
        <span className="text-green-400 font-mono">
          {(bet.edge * 100).toFixed(1)}% edge
        </span>
      </div>
      
      <div className="grid grid-cols-2 gap-2 text-sm">
        <div>
          <span className="text-gray-400">Odds:</span>
          <span className="ml-2 font-mono">{bet.odds.toFixed(2)}</span>
        </div>
        <div>
          <span className="text-gray-400">Kelly:</span>
          <span className="ml-2">${bet.kellyStake.toFixed(0)}</span>
        </div>
      </div>
      
      <button
        onClick={() => onPlace(bet)}
        className="mt-3 w-full bg-blue-600 hover:bg-blue-700 text-white 
                   font-medium py-2 rounded transition-colors"
      >
        Place Bet
      </button>
    </div>
  );
};
```

## 🔐 Authentication Flow

### Login/Register
- **JWT Storage** - Secure token management
- **Auto Refresh** - Token renewal
- **Protected Routes** - Auth guards
- **Session Persistence** - Remember me

### Route Protection
```typescript
// components/ProtectedRoute.tsx
export const ProtectedRoute: React.FC<{ children: ReactNode }> = ({ children }) => {
  const { isAuthenticated } = useAuthStore();
  
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  
  return <>{children}</>;
};
```

## 📊 State Management

### Zustand Store Example
```typescript
// stores/bettingStore.ts
interface BettingState {
  valueBets: ValueBet[];
  activeBets: Bet[];
  isLoading: boolean;
  
  fetchValueBets: () => Promise<void>;
  placeBet: (bet: ValueBet) => Promise<void>;
}

export const useBettingStore = create<BettingState>((set) => ({
  valueBets: [],
  activeBets: [],
  isLoading: false,
  
  fetchValueBets: async () => {
    set({ isLoading: true });
    const bets = await api.getValueBets();
    set({ valueBets: bets, isLoading: false });
  },
  
  placeBet: async (bet) => {
    await api.placeBet(bet);
    // Update state
  }
}));
```

## 🚀 Performance Optimization

### Code Splitting
- **Route-based splitting** - Lazy load pages
- **Component splitting** - Heavy components
- **Bundle analysis** - Monitor size

### Caching Strategy
- **React Query** - Server state caching
- **Local Storage** - User preferences
- **Service Worker** - Offline support

### Real-time Optimization
- **Debounced updates** - Prevent UI thrashing
- **Virtual scrolling** - Large data lists
- **Memoization** - Expensive calculations

## 📱 Responsive Design

### Breakpoints
- **Mobile**: 0-640px
- **Tablet**: 641-1024px
- **Desktop**: 1025px+
- **Wide**: 1280px+

### Mobile Considerations
- **Touch-friendly** - Larger tap targets
- **Swipe gestures** - Navigation
- **Condensed views** - Essential info only
- **Bottom navigation** - Thumb-friendly

## 🧪 Testing Strategy

### Unit Tests
- **Components** - Isolated testing
- **Hooks** - Custom hook logic
- **Utils** - Helper functions
- **Coverage** - Minimum 80%

### Integration Tests
- **User flows** - Complete workflows
- **API mocking** - Predictable tests
- **WebSocket testing** - Real-time features

### E2E Tests
- **Critical paths** - Login, betting, alerts
- **Cross-browser** - Chrome, Firefox, Safari
- **Mobile testing** - Responsive behavior

## 🚦 Development Phases

### Phase 1: Foundation (Week 1-2)
- [ ] Project setup with Vite + React + TypeScript
- [ ] Basic routing and layout components
- [ ] API service setup
- [ ] Authentication flow
- [ ] Dark theme implementation

### Phase 2: Core Features (Week 3-4)  
- [ ] Dashboard page
- [ ] Live odds display
- [ ] Value bet cards
- [ ] WebSocket integration
- [ ] Basic state management

### Phase 3: Advanced Features (Week 5-6)
- [ ] Analysis center
- [ ] Alert management
- [ ] Portfolio tracking
- [ ] Charts and visualizations
- [ ] User settings

### Phase 4: Polish (Week 7-8)
- [ ] Performance optimization
- [ ] Mobile responsiveness
- [ ] Error handling
- [ ] Loading states
- [ ] Testing suite

## 📈 Future Enhancements

### Short Term
- **PWA Support** - Installable app
- **Push Notifications** - Browser alerts
- **Keyboard Navigation** - Power users
- **Export Features** - CSV, PDF reports

### Long Term
- **React Native App** - Mobile apps
- **Advanced Charts** - TradingView integration
- **Social Features** - Leaderboards
- **AI Assistant** - Betting advice

## 🎯 Success Metrics

### Performance
- **Initial Load** - < 3 seconds
- **Time to Interactive** - < 5 seconds
- **Lighthouse Score** - > 90

### User Experience
- **Task Completion** - < 3 clicks
- **Error Rate** - < 1%
- **Mobile Usage** - > 40%

This planning document provides a comprehensive roadmap for building a modern, performant frontend for the Sports Betting Edge Finder application.