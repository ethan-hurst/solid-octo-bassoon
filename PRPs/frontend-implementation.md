# Sports Betting Edge Finder - Frontend Implementation PRP

## 🎯 Objective

Build a modern React-based frontend application that integrates with the existing FastAPI backend to provide a user-friendly interface for sports betting analysis, real-time alerts, and portfolio management.

## 📚 Critical Context & Resources

### Backend API Integration
- **Base URL**: `http://localhost:8000/api`
- **WebSocket**: `ws://localhost:8000/ws/alerts`
- **API Documentation**: Available at `/docs` endpoint
- **Authentication**: JWT tokens (Bearer auth) - login/register endpoints need to be implemented

### Key Dependencies & Documentation
- **React 18 + TypeScript**: https://react.dev/learn/typescript
- **Vite**: https://vitejs.dev/guide/
- **Zustand**: https://docs.pmnd.rs/zustand/getting-started/introduction
- **TanStack Query v5**: https://tanstack.com/query/latest/docs/react/overview
- **Tailwind CSS**: https://tailwindcss.com/docs/guides/vite
- **Headless UI**: https://headlessui.com/react/menu
- **Chart.js**: https://react-chartjs-2.js.org/
- **React Router v6**: https://reactrouter.com/en/main/start/tutorial

### Existing Backend Models (Reference: src/models/schemas.py)
```python
# Sports supported
SportType: NFL, NBA, MLB, NHL, Soccer (EPL, UEFA), Tennis (ATP, WTA)

# Core data structures
ValueBet: {
    id, game_id, market, true_probability, implied_probability,
    edge, expected_value, confidence_score, kelly_fraction
}

MarketOdds: {
    game_id, sport, home_team, away_team, commence_time,
    bet_type, bookmaker_odds[]
}
```

## 🏗️ Implementation Blueprint

### Phase 1: Project Setup & Foundation

#### 1.1 Initialize Vite Project
```bash
# Create project with TypeScript template
npm create vite@latest frontend -- --template react-ts
cd frontend

# Install core dependencies
npm install axios zustand @tanstack/react-query react-router-dom
npm install -D tailwindcss postcss autoprefixer @types/node
npm install @headlessui/react @heroicons/react framer-motion
npm install chart.js react-chartjs-2 date-fns

# Initialize Tailwind
npx tailwindcss init -p
```

#### 1.2 Project Structure
```
frontend/
├── src/
│   ├── api/              # API client and services
│   ├── components/       # Reusable UI components
│   ├── hooks/           # Custom React hooks
│   ├── pages/           # Page components
│   ├── stores/          # Zustand state stores
│   ├── types/           # TypeScript types
│   ├── utils/           # Helper functions
│   ├── App.tsx          # Root component
│   └── main.tsx         # Entry point
├── public/              # Static assets
├── .env.example         # Environment variables template
└── vite.config.ts       # Vite configuration
```

#### 1.3 Configure Vite
```typescript
// vite.config.ts
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/ws': {
        target: 'ws://localhost:8000',
        ws: true,
      },
    },
  },
})
```

#### 1.4 Configure Tailwind
```javascript
// tailwind.config.js
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#eff6ff',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
          800: '#1e40af',
          900: '#1e3a8a',
        },
        success: '#10b981',
        danger: '#ef4444',
        warning: '#f59e0b',
      },
    },
  },
  plugins: [],
}
```

### Phase 2: Core Infrastructure

#### 2.1 API Client Setup
```typescript
// src/api/client.ts
import axios, { AxiosInstance } from 'axios'

class ApiClient {
  private client: AxiosInstance
  
  constructor() {
    this.client = axios.create({
      baseURL: import.meta.env.VITE_API_URL || '/api',
      headers: {
        'Content-Type': 'application/json',
      },
    })
    
    // Request interceptor for auth
    this.client.interceptors.request.use((config) => {
      const token = localStorage.getItem('authToken')
      if (token) {
        config.headers.Authorization = `Bearer ${token}`
      }
      return config
    })
    
    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      async (error) => {
        if (error.response?.status === 401) {
          // Handle token refresh or redirect to login
          localStorage.removeItem('authToken')
          window.location.href = '/login'
        }
        return Promise.reject(error)
      }
    )
  }
  
  get instance() {
    return this.client
  }
}

export const apiClient = new ApiClient().instance
```

#### 2.2 TypeScript Types
```typescript
// src/types/index.ts
export enum SportType {
  NFL = 'americanfootball_nfl',
  NBA = 'basketball_nba',
  MLB = 'baseball_mlb',
  NHL = 'icehockey_nhl',
  SOCCER_EPL = 'soccer_epl',
}

export enum BetType {
  MONEYLINE = 'h2h',
  SPREAD = 'spreads',
  TOTALS = 'totals',
}

export interface BookmakerOdds {
  bookmaker: string
  odds: number
  last_update: string
}

export interface MarketOdds {
  game_id: string
  sport: SportType
  home_team: string
  away_team: string
  commence_time: string
  bet_type: BetType
  bookmaker_odds: BookmakerOdds[]
}

export interface ValueBet {
  id: string
  game_id: string
  market: MarketOdds
  true_probability: number
  implied_probability: number
  edge: number
  expected_value: number
  confidence_score: number
  kelly_fraction: number
  recommended_stake?: number
  created_at: string
}

export interface User {
  id: string
  email: string
  username: string
  is_active: boolean
  sports: SportType[]
  min_edge: number
  max_kelly_fraction: number
  notification_channels: string[]
}
```

#### 2.3 WebSocket Service
```typescript
// src/api/websocket.ts
export type MessageHandler = (data: any) => void

export class WebSocketService {
  private ws: WebSocket | null = null
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private reconnectDelay = 1000
  private messageHandlers = new Set<MessageHandler>()
  
  connect(token: string) {
    const wsUrl = `${import.meta.env.VITE_WS_URL || 'ws://localhost:8000'}/ws/alerts?token=${token}`
    
    this.ws = new WebSocket(wsUrl)
    
    this.ws.onopen = () => {
      console.log('WebSocket connected')
      this.reconnectAttempts = 0
    }
    
    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data)
      this.messageHandlers.forEach(handler => handler(data))
    }
    
    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error)
    }
    
    this.ws.onclose = () => {
      console.log('WebSocket disconnected')
      this.reconnect(token)
    }
  }
  
  private reconnect(token: string) {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      setTimeout(() => {
        this.reconnectAttempts++
        this.connect(token)
      }, this.reconnectDelay * Math.pow(2, this.reconnectAttempts))
    }
  }
  
  subscribe(topic: string, channelId: string) {
    this.send({
      type: 'subscribe',
      channel_type: topic,
      channel_id: channelId,
    })
  }
  
  send(data: any) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data))
    }
  }
  
  addMessageHandler(handler: MessageHandler) {
    this.messageHandlers.add(handler)
  }
  
  removeMessageHandler(handler: MessageHandler) {
    this.messageHandlers.delete(handler)
  }
  
  disconnect() {
    this.ws?.close()
  }
}

export const wsService = new WebSocketService()
```

#### 2.4 Zustand Stores
```typescript
// src/stores/authStore.ts
import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { apiClient } from '@/api/client'

interface AuthState {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  login: (email: string, password: string) => Promise<void>
  logout: () => void
  setUser: (user: User) => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      isAuthenticated: false,
      
      login: async (email, password) => {
        const { data } = await apiClient.post('/auth/login', { email, password })
        set({
          user: data.user,
          token: data.access_token,
          isAuthenticated: true,
        })
        localStorage.setItem('authToken', data.access_token)
      },
      
      logout: () => {
        set({ user: null, token: null, isAuthenticated: false })
        localStorage.removeItem('authToken')
      },
      
      setUser: (user) => set({ user }),
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({ token: state.token }),
    }
  )
)
```

### Phase 3: Component Implementation

#### 3.1 Layout Components
```typescript
// src/components/layout/MainLayout.tsx
import { Outlet } from 'react-router-dom'
import { Header } from './Header'
import { Sidebar } from './Sidebar'

export const MainLayout = () => {
  return (
    <div className="min-h-screen bg-gray-900 text-gray-100">
      <Header />
      <div className="flex">
        <Sidebar />
        <main className="flex-1 p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
```

#### 3.2 Value Bet Card Component
```typescript
// src/components/cards/ValueBetCard.tsx
import { ValueBet } from '@/types'
import { formatDistanceToNow } from 'date-fns'

interface ValueBetCardProps {
  bet: ValueBet
  onPlace: (bet: ValueBet) => void
}

export const ValueBetCard = ({ bet, onPlace }: ValueBetCardProps) => {
  const { market, edge, expected_value, confidence_score, kelly_fraction } = bet
  
  return (
    <div className="bg-gray-800 rounded-lg p-4 border border-gray-700 hover:border-blue-500 transition-colors">
      <div className="flex justify-between items-start mb-3">
        <div>
          <h3 className="text-lg font-semibold">{market.home_team} vs {market.away_team}</h3>
          <p className="text-sm text-gray-400">{market.sport.toUpperCase()}</p>
        </div>
        <span className="text-green-400 font-mono text-lg">
          {(edge * 100).toFixed(1)}% edge
        </span>
      </div>
      
      <div className="grid grid-cols-2 gap-3 mb-4">
        <div className="text-sm">
          <span className="text-gray-400">Best Odds:</span>
          <span className="ml-2 font-mono">{market.bookmaker_odds[0]?.odds.toFixed(2)}</span>
        </div>
        <div className="text-sm">
          <span className="text-gray-400">EV:</span>
          <span className="ml-2 font-mono text-green-400">
            +{(expected_value * 100).toFixed(1)}%
          </span>
        </div>
        <div className="text-sm">
          <span className="text-gray-400">Confidence:</span>
          <span className="ml-2">{(confidence_score * 100).toFixed(0)}%</span>
        </div>
        <div className="text-sm">
          <span className="text-gray-400">Kelly:</span>
          <span className="ml-2">{(kelly_fraction * 100).toFixed(1)}%</span>
        </div>
      </div>
      
      <div className="flex items-center justify-between">
        <span className="text-xs text-gray-500">
          {formatDistanceToNow(new Date(bet.created_at), { addSuffix: true })}
        </span>
        <button
          onClick={() => onPlace(bet)}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md transition-colors"
        >
          Place Bet
        </button>
      </div>
    </div>
  )
}
```

### Phase 4: Page Components

#### 4.1 Dashboard Page
```typescript
// src/pages/Dashboard.tsx
import { useQuery } from '@tanstack/react-query'
import { apiClient } from '@/api/client'
import { ValueBetCard } from '@/components/cards/ValueBetCard'
import { StatsCard } from '@/components/cards/StatsCard'

export const Dashboard = () => {
  const { data: valueBets, isLoading } = useQuery({
    queryKey: ['valueBets'],
    queryFn: async () => {
      const { data } = await apiClient.post('/analysis/value-bets?min_edge=0.05', {
        sport: 'americanfootball_nfl'
      })
      return data
    },
    refetchInterval: 30000, // Refresh every 30 seconds
  })
  
  const { data: performance } = useQuery({
    queryKey: ['performance'],
    queryFn: async () => {
      const { data } = await apiClient.get('/analysis/performance/summary')
      return data
    },
  })
  
  if (isLoading) {
    return <div className="flex justify-center p-8">Loading...</div>
  }
  
  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Dashboard</h1>
      
      {/* Stats Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatsCard
          title="Total P&L"
          value={`$${performance?.total_profit || 0}`}
          change={performance?.profit_change || 0}
        />
        <StatsCard
          title="Win Rate"
          value={`${performance?.win_rate || 0}%`}
          change={performance?.win_rate_change || 0}
        />
        <StatsCard
          title="Active Bets"
          value={performance?.active_bets || 0}
        />
        <StatsCard
          title="Avg Edge"
          value={`${performance?.avg_edge || 0}%`}
        />
      </div>
      
      {/* Value Bets */}
      <div>
        <h2 className="text-2xl font-semibold mb-4">Live Value Bets</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {valueBets?.map((bet: ValueBet) => (
            <ValueBetCard
              key={bet.id}
              bet={bet}
              onPlace={(bet) => console.log('Place bet:', bet)}
            />
          ))}
        </div>
      </div>
    </div>
  )
}
```

### Phase 5: Router Setup

```typescript
// src/App.tsx
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useAuthStore } from '@/stores/authStore'
import { MainLayout } from '@/components/layout/MainLayout'
import { Dashboard } from '@/pages/Dashboard'
import { LiveOdds } from '@/pages/LiveOdds'
import { Analysis } from '@/pages/Analysis'
import { Login } from '@/pages/Login'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      retry: 1,
    },
  },
})

const ProtectedRoute = ({ children }: { children: React.ReactNode }) => {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated)
  
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }
  
  return <>{children}</>
}

export const App = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <MainLayout />
              </ProtectedRoute>
            }
          >
            <Route index element={<Dashboard />} />
            <Route path="odds" element={<LiveOdds />} />
            <Route path="analysis" element={<Analysis />} />
            <Route path="alerts" element={<Alerts />} />
            <Route path="portfolio" element={<Portfolio />} />
            <Route path="settings" element={<Settings />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  )
}
```

## 📋 Implementation Tasks (In Order)

1. **Project Setup** (Day 1)
   - [ ] Initialize Vite project with React + TypeScript
   - [ ] Install all dependencies
   - [ ] Configure Tailwind CSS
   - [ ] Set up project structure
   - [ ] Configure environment variables

2. **Core Infrastructure** (Day 2-3)
   - [ ] Implement API client with axios
   - [ ] Create TypeScript types from backend schemas
   - [ ] Set up WebSocket service
   - [ ] Configure Zustand stores (auth, betting, alerts)
   - [ ] Set up React Query

3. **Authentication** (Day 4)
   - [ ] Create login/register pages
   - [ ] Implement auth store
   - [ ] Set up protected routes
   - [ ] Add token refresh logic

4. **Layout & Navigation** (Day 5)
   - [ ] Create main layout with header/sidebar
   - [ ] Implement dark theme
   - [ ] Set up React Router
   - [ ] Create navigation menu

5. **Dashboard** (Day 6-7)
   - [ ] Create stats cards
   - [ ] Implement value bet cards
   - [ ] Add real-time updates via WebSocket
   - [ ] Create loading states

6. **Live Odds Page** (Day 8-9)
   - [ ] Create odds comparison table
   - [ ] Implement sport filters
   - [ ] Add real-time odds updates
   - [ ] Create quick bet functionality

7. **Analysis Center** (Day 10-11)
   - [ ] Create value bet scanner
   - [ ] Implement arbitrage finder
   - [ ] Add edge calculator
   - [ ] Display ML predictions

8. **Alert Management** (Day 12)
   - [ ] Create alert list/history
   - [ ] Implement preference settings
   - [ ] Add subscription management

9. **Portfolio Tracker** (Day 13)
   - [ ] Create bet history table
   - [ ] Implement performance charts
   - [ ] Add bankroll management

10. **Testing & Polish** (Day 14-15)
    - [ ] Write unit tests for components
    - [ ] Add error boundaries
    - [ ] Implement loading states
    - [ ] Optimize performance
    - [ ] Mobile responsiveness

## 🧪 Validation Gates

```bash
# Install dependencies
cd frontend && npm install

# Type checking
npm run type-check

# Linting
npm run lint

# Unit tests
npm run test

# Build verification
npm run build

# Development server
npm run dev
```

### package.json Scripts
```json
{
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview",
    "type-check": "tsc --noEmit",
    "lint": "eslint . --ext ts,tsx --report-unused-disable-directives",
    "test": "vitest",
    "test:ui": "vitest --ui"
  }
}
```

## ⚠️ Critical Gotchas & Solutions

1. **Authentication Missing**: Backend lacks login/register endpoints
   - **Solution**: Mock auth for now or implement basic JWT endpoints

2. **CORS in Development**: Vite proxy configuration required
   - **Solution**: Use Vite proxy config provided above

3. **WebSocket Reconnection**: Handle connection drops gracefully
   - **Solution**: Implemented exponential backoff in WebSocket service

4. **Type Safety**: Ensure frontend types match backend schemas
   - **Solution**: Generate types from OpenAPI spec or maintain manually

5. **Real-time Updates**: Efficient state management for live data
   - **Solution**: Use React Query for caching + WebSocket for updates

## 🎯 Success Criteria

- [ ] All validation gates pass
- [ ] Dashboard displays real-time value bets
- [ ] WebSocket connection maintains stable connection
- [ ] Responsive design works on mobile/tablet/desktop
- [ ] Performance metrics meet targets (<3s load time)
- [ ] Error handling prevents crashes
- [ ] Type safety throughout application

## 📊 Confidence Score: 8.5/10

**Rationale**: 
- Strong foundation with modern tech stack
- Clear implementation path with working backend
- Minor uncertainty around missing auth endpoints
- Well-documented external libraries
- Comprehensive validation gates

This PRP provides everything needed for successful one-pass implementation of the frontend application.