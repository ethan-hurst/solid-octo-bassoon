export const SportType = {
  NFL: 'americanfootball_nfl',
  NBA: 'basketball_nba',
  MLB: 'baseball_mlb',
  NHL: 'icehockey_nhl',
  SOCCER_EPL: 'soccer_epl',
  SOCCER_UEFA_CL: 'soccer_uefa_champs_league',
  SOCCER_UEFA_EL: 'soccer_uefa_europa_league',
  TENNIS_ATP: 'tennis_atp',
  TENNIS_WTA: 'tennis_wta',
} as const

export type SportType = typeof SportType[keyof typeof SportType]

export const BetType = {
  MONEYLINE: 'h2h',
  SPREAD: 'spreads',
  TOTALS: 'totals',
} as const

export type BetType = typeof BetType[keyof typeof BetType]

export const OddsFormat = {
  AMERICAN: 'american',
  DECIMAL: 'decimal',
  FRACTIONAL: 'fractional',
} as const

export type OddsFormat = typeof OddsFormat[keyof typeof OddsFormat]

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

export interface Alert {
  id: string
  user_id: string
  value_bet: ValueBet
  created_at: string
  notification_channels: string[]
  status: 'pending' | 'sent' | 'failed'
  sent_at?: string
}

export interface PerformanceSummary {
  total_profit: number
  profit_change: number
  win_rate: number
  win_rate_change: number
  active_bets: number
  avg_edge: number
}

export interface AuthResponse {
  access_token: string
  token_type: string
  user: User
}

export interface WebSocketMessage {
  type: 'subscribe' | 'unsubscribe' | 'ping' | 'alert'
  data: any
  timestamp?: string
  channel_type?: string
  channel_id?: string
}

// Player Props Types
export interface Player {
  id: string
  name: string
  team: string
  position: string
  sport: SportType
  image_url?: string
  jersey_number?: string
}

export interface PlayerStats {
  player_id: string
  season: string
  games_played: number
  stats: Record<string, number>
  averages: Record<string, number>
  recent_form: number[] // Last 5 games
}

export interface PropBet {
  id: string
  player: Player
  prop_type: string // 'points', 'rebounds', 'assists', etc.
  line: number
  over_odds: number
  under_odds: number
  bookmaker: string
  confidence: number
  prediction: 'over' | 'under'
  reasoning: string
}

export interface PropComparison {
  prop_type: string
  player: Player
  lines: {
    bookmaker: string
    line: number
    over_odds: number
    under_odds: number
  }[]
  best_over: { bookmaker: string; odds: number }
  best_under: { bookmaker: string; odds: number }
}

// Social Trading Types
export interface UserProfile {
  id: string
  username: string
  display_name: string
  avatar_url?: string
  bio?: string
  verified: boolean
  subscription_tier: 'free' | 'pro' | 'expert'
  followers_count: number
  following_count: number
  total_bets: number
  win_rate: number
  total_profit: number
  roi: number
  sports: SportType[]
  created_at: string
}

export interface BetPost {
  id: string
  user: UserProfile
  bet: ValueBet
  analysis?: string
  likes_count: number
  comments_count: number
  shares_count: number
  created_at: string
  is_liked?: boolean
}

export interface Comment {
  id: string
  user: UserProfile
  content: string
  likes_count: number
  created_at: string
  replies?: Comment[]
}

export interface CopySettings {
  user_id: string
  followed_user_id: string
  auto_copy: boolean
  max_stake_per_bet: number
  max_daily_stake: number
  copy_sports: SportType[]
  min_edge: number
  enabled: boolean
}

// Professional Tools Types
export interface Position {
  id: string
  bet: ValueBet
  stake: number
  status: 'pending' | 'won' | 'lost' | 'void'
  placed_at: string
  settled_at?: string
  payout?: number
  profit?: number
}

export interface RiskMetrics {
  value_at_risk: number
  sharpe_ratio: number
  sortino_ratio: number
  max_drawdown: number
  current_drawdown: number
  kelly_criterion: number
  correlation_matrix: number[][]
}

export interface Strategy {
  id: string
  name: string
  description: string
  rules: StrategyRule[]
  backtest_results?: BacktestResult
  is_active: boolean
  created_at: string
}

export interface StrategyRule {
  id: string
  type: 'edge' | 'kelly' | 'sport' | 'odds' | 'time'
  operator: 'gt' | 'lt' | 'eq' | 'between' | 'in'
  value: any
  combine_with: 'AND' | 'OR'
}

export interface BacktestResult {
  total_bets: number
  win_rate: number
  total_profit: number
  roi: number
  sharpe_ratio: number
  max_drawdown: number
  monthly_returns: { month: string; return: number }[]
}

// Dashboard Widget Types
export interface DashboardWidget {
  id: string
  type: 'chart' | 'stat' | 'table' | 'feed'
  title: string
  config: Record<string, any>
  position: { x: number; y: number }
  size: { width: number; height: number }
}

// Subscription Types
export interface Subscription {
  id: string
  user_id: string
  plan: 'free' | 'pro' | 'expert' | 'enterprise'
  status: 'active' | 'canceled' | 'past_due'
  current_period_start: string
  current_period_end: string
  features: string[]
  limits: {
    api_calls: number
    concurrent_bets: number
    followed_users: number
    strategies: number
  }
}

// Notification Types
export interface Notification {
  id: string
  type: 'bet' | 'follow' | 'comment' | 'like' | 'system'
  title: string
  message: string
  data?: any
  read: boolean
  created_at: string
}