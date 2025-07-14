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