"""Pydantic models for data validation."""
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator
import uuid


class SportType(str, Enum):
    """Supported sports types."""
    NFL = "americanfootball_nfl"
    NBA = "basketball_nba"
    MLB = "baseball_mlb"
    NHL = "icehockey_nhl"
    SOCCER_EPL = "soccer_epl"
    SOCCER_UEFA_CL = "soccer_uefa_champs_league"
    SOCCER_UEFA_EL = "soccer_uefa_europa_league"
    TENNIS_ATP = "tennis_atp"
    TENNIS_WTA = "tennis_wta"


class OddsFormat(str, Enum):
    """Odds format types."""
    AMERICAN = "american"
    DECIMAL = "decimal"
    FRACTIONAL = "fractional"


class BetType(str, Enum):
    """Bet market types."""
    MONEYLINE = "h2h"
    SPREAD = "spreads"
    TOTALS = "totals"


class BookmakerOdds(BaseModel):
    """Odds from a single bookmaker."""
    bookmaker: str
    odds: float = Field(gt=1.0, description="Decimal odds")
    last_update: datetime
    
    @validator("odds")
    def validate_odds(cls, v: float) -> float:
        """Ensure odds are reasonable."""
        if v < 1.01 or v > 1000:
            raise ValueError("Odds must be between 1.01 and 1000")
        return v


class Team(BaseModel):
    """Team information."""
    name: str
    id: Optional[str] = None


class MarketOdds(BaseModel):
    """Odds for a specific betting market."""
    game_id: str
    sport: SportType
    home_team: str
    away_team: str
    commence_time: datetime
    bet_type: BetType
    bookmaker_odds: List[BookmakerOdds]
    
    @property
    def best_odds(self) -> Optional[BookmakerOdds]:
        """Get the best available odds."""
        if not self.bookmaker_odds:
            return None
        return max(self.bookmaker_odds, key=lambda x: x.odds)
    
    @property
    def implied_probability(self) -> Optional[float]:
        """Calculate implied probability from best odds."""
        best = self.best_odds
        if not best:
            return None
        return 1.0 / best.odds


class ValueBet(BaseModel):
    """A detected value betting opportunity."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    game_id: str
    market: MarketOdds
    true_probability: float = Field(ge=0.0, le=1.0)
    implied_probability: float = Field(ge=0.0, le=1.0)
    edge: float = Field(description="True prob - implied prob")
    expected_value: float
    confidence_score: float = Field(ge=0.0, le=1.0)
    kelly_fraction: float = Field(ge=0.0, le=0.25)
    recommended_stake: Optional[float] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    @validator("edge")
    def validate_edge(cls, v: float, values: Dict[str, Any]) -> float:
        """Ensure edge calculation is correct."""
        if "true_probability" in values and "implied_probability" in values:
            expected_edge = values["true_probability"] - values["implied_probability"]
            if abs(v - expected_edge) > 0.0001:  # Allow small floating point errors
                raise ValueError("Edge must equal true_prob - implied_prob")
        return v


class Alert(BaseModel):
    """Alert notification for users."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    value_bet: ValueBet
    created_at: datetime = Field(default_factory=datetime.utcnow)
    notification_channels: List[str] = Field(default_factory=list)
    status: str = Field(default="pending")
    sent_at: Optional[datetime] = None


class User(BaseModel):
    """User account information."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    username: str
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Preferences
    sports: List[SportType] = Field(default_factory=list)
    min_edge: float = Field(default=0.05, ge=0.0, le=1.0)
    max_kelly_fraction: float = Field(default=0.25, ge=0.0, le=1.0)
    notification_channels: List[str] = Field(default_factory=lambda: ["websocket"])


class OddsResponse(BaseModel):
    """Response from The Odds API."""
    id: str
    sport_key: str
    sport_title: str
    commence_time: datetime
    home_team: str
    away_team: str
    bookmakers: List[Dict[str, Any]]


class BacktestResult(BaseModel):
    """Results from backtesting a strategy."""
    strategy_name: str
    start_date: datetime
    end_date: datetime
    total_bets: int
    winning_bets: int
    win_rate: float = Field(ge=0.0, le=1.0)
    total_profit: float
    roi: float
    sharpe_ratio: float
    max_drawdown: float
    kelly_performance: Dict[str, float]


class WebSocketMessage(BaseModel):
    """WebSocket message format."""
    type: str
    data: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class AuthToken(BaseModel):
    """JWT authentication token."""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Token payload data."""
    user_id: Optional[str] = None
    username: Optional[str] = None