"""SQLAlchemy database models."""
from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Column, String, Float, DateTime, JSON, Boolean, 
    Integer, ForeignKey, Index, Text, UniqueConstraint
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, Session
from sqlalchemy.dialects.postgresql import UUID
import uuid

Base = declarative_base()


class OddsSnapshot(Base):
    """Time-series table for odds data (TimescaleDB hypertable)."""
    __tablename__ = "odds_snapshots"
    __table_args__ = (
        Index("idx_odds_game_time", "game_id", "timestamp"),
        Index("idx_odds_bookmaker", "bookmaker", "timestamp"),
        {"timescaledb_hypertable": {"time_column_name": "timestamp"}},
    )
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    timestamp = Column(DateTime, nullable=False, index=True)
    game_id = Column(String, nullable=False)
    sport = Column(String, nullable=False)
    bookmaker = Column(String, nullable=False)
    market_type = Column(String, nullable=False)
    odds_data = Column(JSON, nullable=False)
    
    # Denormalized fields for faster queries
    home_team = Column(String)
    away_team = Column(String)
    commence_time = Column(DateTime)
    decimal_odds = Column(Float)


class User(Base):
    """User account table."""
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("email", name="uq_user_email"),
        UniqueConstraint("username", name="uq_user_username"),
    )
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, nullable=False, index=True)
    username = Column(String, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # User preferences
    sports = Column(JSON, default=list)
    min_edge = Column(Float, default=0.05)
    max_kelly_fraction = Column(Float, default=0.25)
    notification_channels = Column(JSON, default=lambda: ["websocket"])
    
    # Relationships
    alerts = relationship("Alert", back_populates="user", cascade="all, delete-orphan")
    bets = relationship("Bet", back_populates="user", cascade="all, delete-orphan")


class Alert(Base):
    """Alert notifications table."""
    __tablename__ = "alerts"
    __table_args__ = (
        Index("idx_alert_user_created", "user_id", "created_at"),
        Index("idx_alert_status", "status"),
    )
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    value_bet_data = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    notification_channels = Column(JSON, default=list)
    status = Column(String, default="pending", index=True)
    sent_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="alerts")


class Bet(Base):
    """User betting history table."""
    __tablename__ = "bets"
    __table_args__ = (
        Index("idx_bet_user_placed", "user_id", "placed_at"),
        Index("idx_bet_game", "game_id"),
    )
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    game_id = Column(String, nullable=False)
    sport = Column(String, nullable=False)
    market_type = Column(String, nullable=False)
    bookmaker = Column(String, nullable=False)
    
    # Bet details
    stake = Column(Float, nullable=False)
    odds = Column(Float, nullable=False)
    predicted_probability = Column(Float, nullable=False)
    edge = Column(Float, nullable=False)
    kelly_fraction = Column(Float)
    
    # Timestamps
    placed_at = Column(DateTime, default=datetime.utcnow)
    settled_at = Column(DateTime, nullable=True)
    
    # Result
    status = Column(String, default="pending")  # pending, won, lost, void
    profit = Column(Float, nullable=True)
    
    # Metadata
    metadata = Column(JSON, default=dict)
    
    # Relationships
    user = relationship("User", back_populates="bets")


class MLModel(Base):
    """Trained ML models metadata."""
    __tablename__ = "ml_models"
    __table_args__ = (
        UniqueConstraint("sport", "model_type", "version", name="uq_model_version"),
    )
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sport = Column(String, nullable=False)
    model_type = Column(String, nullable=False)  # xgboost, ensemble, etc.
    version = Column(String, nullable=False)
    
    # Model performance metrics
    accuracy = Column(Float)
    precision = Column(Float)
    recall = Column(Float)
    f1_score = Column(Float)
    log_loss = Column(Float)
    
    # Training details
    trained_at = Column(DateTime, default=datetime.utcnow)
    training_samples = Column(Integer)
    features = Column(JSON)
    hyperparameters = Column(JSON)
    
    # Model file path
    model_path = Column(String, nullable=False)
    is_active = Column(Boolean, default=False)


class BacktestRun(Base):
    """Backtesting run history."""
    __tablename__ = "backtest_runs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    strategy_name = Column(String, nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    
    # Results
    total_bets = Column(Integer, default=0)
    winning_bets = Column(Integer, default=0)
    win_rate = Column(Float)
    total_profit = Column(Float)
    roi = Column(Float)
    sharpe_ratio = Column(Float)
    max_drawdown = Column(Float)
    
    # Configuration
    config = Column(JSON)
    results = Column(JSON)
    
    created_at = Column(DateTime, default=datetime.utcnow)


class LiveGame(Base):
    """Live game tracking table."""
    __tablename__ = "live_games"
    __table_args__ = (
        Index("idx_live_games_active", "is_active", "last_updated"),
        Index("idx_live_games_sport", "sport", "is_active"),
    )
    
    game_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sport = Column(String(50), nullable=False)
    home_team = Column(String(100), nullable=False)
    away_team = Column(String(100), nullable=False)
    game_state = Column(JSON, nullable=False)
    current_score = Column(JSON, nullable=False)
    game_clock = Column(String(20))
    quarter_period = Column(Integer)
    is_active = Column(Boolean, default=True)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    odds_updates = relationship("LiveOddsUpdate", back_populates="game", cascade="all, delete-orphan")
    events = relationship("LiveEvent", back_populates="game", cascade="all, delete-orphan")
    predictions = relationship("LivePrediction", back_populates="game", cascade="all, delete-orphan")
    value_bets = relationship("LiveValueBet", back_populates="game", cascade="all, delete-orphan")


class LiveOddsUpdate(Base):
    """Live odds updates table (TimescaleDB hypertable)."""
    __tablename__ = "live_odds_updates"
    __table_args__ = (
        Index("idx_live_odds_game_timestamp", "game_id", "timestamp"),
        Index("idx_live_odds_bookmaker_timestamp", "bookmaker", "timestamp"),
        {"timescaledb_hypertable": {"time_column_name": "timestamp"}},
    )
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    game_id = Column(UUID(as_uuid=True), ForeignKey("live_games.game_id"), nullable=False)
    bookmaker = Column(String(50), nullable=False)
    bet_type = Column(String(50), nullable=False)
    odds_before = Column(Float)
    odds_after = Column(Float)
    line_before = Column(Float)
    line_after = Column(Float)
    significance_score = Column(Float)
    timestamp = Column(DateTime, nullable=False, index=True, default=datetime.utcnow)
    
    # Relationships
    game = relationship("LiveGame", back_populates="odds_updates")


class LiveEvent(Base):
    """Live game events table (TimescaleDB hypertable)."""
    __tablename__ = "live_events"
    __table_args__ = (
        Index("idx_live_events_game_timestamp", "game_id", "timestamp"),
        Index("idx_live_events_type", "event_type", "timestamp"),
        {"timescaledb_hypertable": {"time_column_name": "timestamp"}},
    )
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    game_id = Column(UUID(as_uuid=True), ForeignKey("live_games.game_id"), nullable=False)
    event_type = Column(String(50), nullable=False)
    event_description = Column(Text)
    event_data = Column(JSON)
    game_clock = Column(String(20))
    impact_score = Column(Float)
    probability_change = Column(JSON)
    timestamp = Column(DateTime, nullable=False, index=True, default=datetime.utcnow)
    
    # Relationships
    game = relationship("LiveGame", back_populates="events")


class LivePrediction(Base):
    """Live ML predictions table (TimescaleDB hypertable)."""
    __tablename__ = "live_predictions"
    __table_args__ = (
        Index("idx_live_predictions_game_timestamp", "game_id", "prediction_timestamp"),
        Index("idx_live_predictions_model", "model_version", "prediction_timestamp"),
        {"timescaledb_hypertable": {"time_column_name": "prediction_timestamp"}},
    )
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    game_id = Column(UUID(as_uuid=True), ForeignKey("live_games.game_id"), nullable=False)
    model_version = Column(String(50), nullable=False)
    home_win_probability = Column(Float, nullable=False)
    away_win_probability = Column(Float, nullable=False)
    draw_probability = Column(Float)
    confidence_score = Column(Float, nullable=False)
    features_used = Column(JSON)
    prediction_timestamp = Column(DateTime, nullable=False, index=True, default=datetime.utcnow)
    
    # Relationships
    game = relationship("LiveGame", back_populates="predictions")


class LiveValueBet(Base):
    """Live value betting opportunities table (TimescaleDB hypertable)."""
    __tablename__ = "live_value_bets"
    __table_args__ = (
        Index("idx_live_value_bets_active", "is_active", "detected_at"),
        Index("idx_live_value_bets_game", "game_id", "is_active"),
        Index("idx_live_value_bets_edge", "edge", postgresql_where="is_active = true"),
        {"timescaledb_hypertable": {"time_column_name": "detected_at"}},
    )
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    game_id = Column(UUID(as_uuid=True), ForeignKey("live_games.game_id"), nullable=False)
    bookmaker = Column(String(50), nullable=False)
    bet_type = Column(String(50), nullable=False)
    selection = Column(String(100), nullable=False)
    odds = Column(Float, nullable=False)
    fair_odds = Column(Float, nullable=False)
    edge = Column(Float, nullable=False)
    confidence = Column(Float, nullable=False)
    kelly_fraction = Column(Float)
    recommended_stake = Column(Float)
    is_active = Column(Boolean, default=True)
    detected_at = Column(DateTime, nullable=False, index=True, default=datetime.utcnow)
    expires_at = Column(DateTime)
    
    # Relationships
    game = relationship("LiveGame", back_populates="value_bets")


class LiveSubscription(Base):
    """User subscriptions to live betting alerts."""
    __tablename__ = "live_subscriptions"
    __table_args__ = (
        Index("idx_live_subscriptions_user", "user_id", "is_active"),
        Index("idx_live_subscriptions_type_target", "subscription_type", "subscription_target"),
    )
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    subscription_type = Column(String(50), nullable=False)  # 'game', 'sport', 'team'
    subscription_target = Column(String(100), nullable=False)  # game_id, sport, team_name
    min_edge_threshold = Column(Float, default=0.02)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User")