"""Pydantic models for live betting data validation."""
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Union, Literal
from pydantic import BaseModel, Field, validator
import uuid


class LiveEventType(str, Enum):
    """Types of live game events."""
    SCORE = "score"
    TIMEOUT = "timeout"
    PENALTY = "penalty"
    INJURY = "injury"
    SUBSTITUTION = "substitution"
    QUARTER_END = "quarter_end"
    HALF_TIME = "half_time"
    GAME_END = "game_end"
    TURNOVER = "turnover"
    FOUL = "foul"


class LiveBetType(str, Enum):
    """Live betting market types."""
    MONEYLINE = "moneyline"
    SPREAD = "spread"
    TOTAL = "total"
    NEXT_SCORE = "next_score"
    PROP = "prop"
    QUARTER_RESULT = "quarter_result"
    HALFTIME_RESULT = "halftime_result"


class GameClock(BaseModel):
    """Game clock representation."""
    minutes: int = Field(ge=0, le=60)
    seconds: int = Field(ge=0, le=59)
    quarter_period: int = Field(ge=1, le=4)
    is_overtime: bool = False
    
    @property
    def total_seconds(self) -> int:
        """Convert to total seconds."""
        return self.minutes * 60 + self.seconds
    
    def __str__(self) -> str:
        return f"{self.minutes:02d}:{self.seconds:02d}"


class LiveGameState(BaseModel):
    """Current state of a live game."""
    game_id: str
    sport: str
    home_team: str
    away_team: str
    current_score: Dict[str, int]  # {"home": 21, "away": 14}
    game_clock: Optional[GameClock] = None
    quarter_period: int = Field(ge=1, le=4)
    is_active: bool = True
    possession: Optional[str] = None  # "home" or "away"
    down_distance: Optional[str] = None  # For football: "3rd & 7"
    field_position: Optional[str] = None  # For football: "OWN 25"
    last_updated: datetime = Field(default_factory=datetime.utcnow)


class LiveOdds(BaseModel):
    """Live odds data."""
    game_id: str
    bookmaker: str
    bet_type: LiveBetType
    selection: str
    odds: float = Field(gt=1.0, description="Decimal odds")
    line: Optional[float] = None  # Point spread or total line
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    @validator("odds")
    def validate_odds(cls, v: float) -> float:
        """Ensure odds are reasonable."""
        if v < 1.01 or v > 50:
            raise ValueError("Live odds must be between 1.01 and 50")
        return v


class OddsUpdate(BaseModel):
    """Odds movement data."""
    bookmaker: str
    bet_type: str
    old_odds: float
    new_odds: float
    line_movement: float
    significance: float = Field(ge=0.0, le=1.0, description="Movement significance score")


class LiveEvent(BaseModel):
    """Live game event."""
    game_id: str
    event_type: LiveEventType
    description: str
    event_data: Dict[str, Any] = Field(default_factory=dict)
    game_clock: Optional[str] = None
    impact_score: float = Field(ge=0.0, le=1.0, description="Event impact on game")
    probability_change: Dict[str, float] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class LivePrediction(BaseModel):
    """Live ML prediction."""
    model_config = {"protected_namespaces": ()}
    game_id: str
    model_version: str
    home_win_probability: float = Field(ge=0.0, le=1.0)
    away_win_probability: float = Field(ge=0.0, le=1.0)
    draw_probability: Optional[float] = Field(None, ge=0.0, le=1.0)
    confidence_score: float = Field(ge=0.0, le=1.0)
    features_used: Dict[str, Any] = Field(default_factory=dict)
    prediction_timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    @validator("home_win_probability")
    def validate_probabilities_sum(cls, v, values):
        """Ensure probabilities sum to approximately 1.0."""
        if "away_win_probability" in values:
            away_prob = values["away_win_probability"]
            draw_prob = values.get("draw_probability", 0.0)
            total = v + away_prob + draw_prob
            if abs(total - 1.0) > 0.05:  # Allow 5% tolerance
                raise ValueError(f"Probabilities must sum to 1.0, got {total}")
        return v


class LiveValueBet(BaseModel):
    """Live value betting opportunity."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    game_id: str
    bookmaker: str
    bet_type: str
    selection: str
    odds: float = Field(gt=1.0)
    fair_odds: float = Field(gt=1.0)
    edge: float = Field(description="Betting edge percentage")
    confidence: float = Field(ge=0.0, le=1.0)
    kelly_fraction: Optional[float] = Field(None, ge=0.0, le=0.25)
    recommended_stake: Optional[float] = None
    is_active: bool = True
    detected_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    
    @validator("edge")
    def validate_edge(cls, v: float, values: Dict[str, Any]) -> float:
        """Validate edge calculation."""
        if "fair_odds" in values and "odds" in values:
            fair_prob = 1.0 / values["fair_odds"]
            implied_prob = 1.0 / values["odds"]
            expected_edge = fair_prob - implied_prob
            if abs(v - expected_edge) > 0.001:  # Small tolerance for floating point
                raise ValueError("Edge calculation incorrect")
        return v


class GameEvent(BaseModel):
    """Game event for WebSocket messages."""
    event_type: str
    description: str
    impact_score: float
    probability_change: Dict[str, float]


class PredictionUpdate(BaseModel):
    """Prediction update for WebSocket messages."""
    model_config = {"protected_namespaces": ()}
    model_version: str
    home_win_probability: float
    away_win_probability: float
    confidence_score: float


class LiveWebSocketMessage(BaseModel):
    """WebSocket message format for live betting."""
    message_type: Literal["odds_update", "game_event", "value_bet", "prediction_update"]
    game_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    data: Union[OddsUpdate, GameEvent, LiveValueBet, PredictionUpdate]


class LiveAlertSubscription(BaseModel):
    """Live betting alert subscription."""
    user_id: str
    subscription_type: Literal["game", "sport", "team"]
    subscription_target: str
    min_edge_threshold: float = Field(default=0.02, ge=0.0, le=1.0)
    is_active: bool = True


class LiveSubscription(BaseModel):
    """User subscription to live updates."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    subscription_type: str
    subscription_target: str
    min_edge_threshold: float = 0.02
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)


class LiveGameSummary(BaseModel):
    """Summary of live game for API responses."""
    game_id: str
    sport: str
    home_team: str
    away_team: str
    current_score: Dict[str, int]
    game_clock: Optional[str] = None
    quarter_period: int
    is_active: bool
    value_bets_count: int = 0
    last_event: Optional[str] = None


class LiveDashboard(BaseModel):
    """Live betting dashboard data."""
    active_games: List[LiveGameSummary]
    user_subscriptions: List[LiveSubscription]
    recent_value_bets: List[LiveValueBet]
    live_alerts_count: int


class ScoreUpdate(BaseModel):
    """Score update data from live feeds."""
    game_id: str
    home_score: int = Field(ge=0)
    away_score: int = Field(ge=0)
    quarter_period: int = Field(ge=1, le=4)
    game_clock: Optional[str] = None
    is_final: bool = False
    scoring_play: Optional[str] = None


class LineMovement(BaseModel):
    """Betting line movement data."""
    game_id: str
    bookmaker: str
    bet_type: str
    old_line: Optional[float] = None
    new_line: Optional[float] = None
    old_odds: float
    new_odds: float
    movement_size: float
    direction: Literal["up", "down", "stable"]
    significance: float = Field(ge=0.0, le=1.0)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class LiveBettingFeatures(BaseModel):
    """Features for live betting ML models."""
    game_id: str
    # Score and game state features
    score_differential: int
    total_points: int
    time_remaining_minutes: float
    quarter_period: int
    
    # Momentum features
    recent_scoring_rate_home: float = 0.0
    recent_scoring_rate_away: float = 0.0
    momentum_score: float = 0.0
    
    # Situational features (sport-specific)
    possession: Optional[str] = None
    down_distance: Optional[str] = None
    field_position: Optional[int] = None
    
    # Market features
    line_movement: float = 0.0
    volume_indicator: float = 0.0
    
    # Historical features
    h2h_performance: float = 0.0
    recent_form_home: float = 0.0
    recent_form_away: float = 0.0


class EventPrediction(BaseModel):
    """Prediction for next game event."""
    game_id: str
    event_type: str
    probability: float = Field(ge=0.0, le=1.0)
    time_window_minutes: int = Field(ge=1, le=30)
    confidence: float = Field(ge=0.0, le=1.0)


class MomentumScore(BaseModel):
    """Game momentum calculation."""
    game_id: str
    momentum_direction: Literal["home", "away", "neutral"]
    momentum_strength: float = Field(ge=0.0, le=1.0)
    recent_events_factor: float = Field(ge=0.0, le=1.0)
    scoring_rate_factor: float = Field(ge=0.0, le=1.0)
    calculated_at: datetime = Field(default_factory=datetime.utcnow)