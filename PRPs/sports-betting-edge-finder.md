name: "Sports Betting Edge Finder - Real-Time Value Bet Detection System"
description: |

## Purpose
Build a comprehensive sports betting analysis platform that identifies value bets by aggregating real-time odds, analyzing market inefficiencies, and leveraging ML models to find profitable betting opportunities across multiple sportsbooks.

## Core Principles
1. **Context is King**: Include ALL necessary documentation, examples, and caveats
2. **Validation Loops**: Provide executable tests/lints the AI can run and fix
3. **Information Dense**: Use keywords and patterns from the codebase
4. **Progressive Success**: Start simple, validate, then enhance
5. **Global rules**: Be sure to follow all rules in CLAUDE.md

---

## Goal
Create a production-ready sports betting edge detection system that continuously monitors odds across 20+ sportsbooks, identifies value bets using statistical models and ML, and provides real-time alerts with confidence scoring. The system must handle high-frequency data updates, scale horizontally, and maintain sub-30-second alert latency.

## Why
- **Business value**: Enables profitable sports betting through data-driven edge detection
- **Integration**: Aggregates fragmented sportsbook data into actionable insights
- **Problems solved**: Identifies mispriced odds, arbitrage opportunities, and value bets faster than manual analysis

## What
A scalable platform where:
- Real-time odds aggregate from multiple sportsbooks via APIs
- ML models analyze probabilities vs market odds to find edges
- WebSocket streams deliver instant alerts to users
- Historical backtesting validates strategies
- Risk management enforces bankroll optimization

### Success Criteria
- [ ] Aggregate odds from 10+ sportsbooks in real-time
- [ ] Detect value bets with >5% edge within 30 seconds
- [ ] Achieve 55%+ win rate on -110 bets in backtesting
- [ ] Stream alerts via WebSocket with <1s latency
- [ ] Handle 1000+ concurrent users without degradation
- [ ] All tests pass with >80% coverage

## All Needed Context

### Documentation & References
```yaml
# MUST READ - Include these in your context window
- url: https://the-odds-api.com/liveapi/guides/v4/
  why: The Odds API v4 documentation for aggregating odds
  
- url: https://fastapi.tiangolo.com/advanced/websockets/
  why: FastAPI WebSocket implementation for real-time streaming
  
- url: https://medium.com/@nandagopal05/scaling-websockets-with-pub-sub-using-python-redis-fastapi-b16392ffe291
  why: Scaling WebSockets with Redis pub/sub pattern
  
- url: https://docs.celeryq.dev/en/stable/getting-started/first-steps-with-celery.html
  why: Celery for background task processing
  
- url: https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.VotingClassifier.html
  why: Ensemble ML models for prediction confidence
  
- url: https://xgboost.readthedocs.io/en/stable/python/python_api.html
  why: XGBoost for sports outcome predictions
  
- url: https://github.com/georgedouzas/sports-betting
  why: Sports betting Python library with backtesting
  
- url: https://redis.io/docs/connect/clients/python/
  why: Redis Python client for caching and pub/sub
  
- url: https://docs.timescale.com/use-timescale/latest/
  why: TimescaleDB for time-series odds data

- file: initial.md
  why: Complete feature specification and architecture
```

### Current Codebase tree
```bash
.
├── examples/
├── PRPs/
│   └── templates/
│       └── prp_base.md
├── INITIAL.md
├── CLAUDE.md
├── LICENSE
└── README.md
```

### Desired Codebase tree with files to be added
```bash
.
├── src/
│   ├── __init__.py
│   ├── data_collection/
│   │   ├── __init__.py
│   │   ├── odds_aggregator.py        # The Odds API integration
│   │   ├── sports_api_client.py      # ESPN/stats APIs
│   │   ├── line_tracker.py           # Line movement monitoring
│   │   └── cache_manager.py          # Redis caching layer
│   ├── analysis/
│   │   ├── __init__.py
│   │   ├── value_calculator.py       # EV calculations
│   │   ├── ml_models.py              # XGBoost/ensemble models
│   │   ├── arbitrage_finder.py       # Cross-book arbitrage
│   │   └── backtester.py             # Historical backtesting
│   ├── alerts/
│   │   ├── __init__.py
│   │   ├── websocket_manager.py      # WebSocket connections
│   │   ├── notification_service.py   # Multi-channel alerts
│   │   └── redis_pubsub.py          # Redis pub/sub manager
│   ├── api/
│   │   ├── __init__.py
│   │   ├── main.py                   # FastAPI app
│   │   ├── routers/
│   │   │   ├── __init__.py
│   │   │   ├── odds.py               # Odds endpoints
│   │   │   ├── alerts.py             # Alert management
│   │   │   └── analysis.py           # Analysis endpoints
│   │   ├── websocket.py              # WebSocket endpoints
│   │   └── dependencies.py           # Shared dependencies
│   ├── models/
│   │   ├── __init__.py
│   │   ├── schemas.py                # Pydantic models
│   │   ├── database.py               # SQLAlchemy models
│   │   └── ml_features.py            # Feature engineering
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py               # Pydantic settings
│   └── utils/
│       ├── __init__.py
│       ├── logger.py                 # Logging configuration
│       └── validators.py             # Input validation
├── tests/
│   ├── __init__.py
│   ├── test_odds_aggregator.py
│   ├── test_value_calculator.py
│   ├── test_ml_models.py
│   ├── test_websocket.py
│   └── test_api.py
├── alembic/                          # Database migrations
│   └── versions/
├── scripts/
│   ├── train_models.py               # ML training pipeline
│   └── backtest.py                   # Backtesting script
├── .env.example
├── requirements.txt
├── docker-compose.yml
├── Dockerfile
├── alembic.ini
├── pyproject.toml
└── README.md
```

### Known Gotchas & Library Quirks
```python
# CRITICAL: The Odds API has rate limits - 500/month free, cache aggressively
# CRITICAL: WebSocket connections require sticky sessions in production
# CRITICAL: Redis pub/sub doesn't guarantee message delivery - implement acknowledgments
# CRITICAL: XGBoost models need periodic retraining as sports seasons progress
# CRITICAL: TimescaleDB requires hypertables for time-series data
# CRITICAL: Celery tasks must be idempotent for retry logic
# CRITICAL: FastAPI WebSockets are async - no blocking operations
# CRITICAL: Always use UTC timestamps for odds data
# CRITICAL: Handle sportsbook API downtimes gracefully with fallbacks
```

## Implementation Blueprint

### Data models and structure

```python
# schemas.py - Core Pydantic models
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict
from datetime import datetime
from enum import Enum

class SportType(str, Enum):
    NFL = "americanfootball_nfl"
    NBA = "basketball_nba"
    MLB = "baseball_mlb"
    NHL = "icehockey_nhl"
    SOCCER_EPL = "soccer_epl"

class OddsFormat(str, Enum):
    AMERICAN = "american"
    DECIMAL = "decimal"

class BetType(str, Enum):
    MONEYLINE = "h2h"
    SPREAD = "spreads"
    TOTALS = "totals"

class BookmakerOdds(BaseModel):
    bookmaker: str
    odds: float
    last_update: datetime
    
class MarketOdds(BaseModel):
    home_team: str
    away_team: str
    bet_type: BetType
    bookmaker_odds: List[BookmakerOdds]
    
class ValueBet(BaseModel):
    game_id: str
    market: MarketOdds
    true_probability: float = Field(ge=0.0, le=1.0)
    implied_probability: float = Field(ge=0.0, le=1.0)
    edge: float = Field(description="True prob - implied prob")
    expected_value: float
    confidence_score: float = Field(ge=0.0, le=1.0)
    kelly_fraction: float = Field(ge=0.0, le=0.25)
    
class Alert(BaseModel):
    id: str
    user_id: str
    value_bet: ValueBet
    created_at: datetime
    notification_channels: List[str]
    
# database.py - SQLAlchemy models
from sqlalchemy import Column, String, Float, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class OddsSnapshot(Base):
    __tablename__ = "odds_snapshots"
    __table_args__ = {"timescaledb_hypertable": {"time_column_name": "timestamp"}}
    
    id = Column(String, primary_key=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    game_id = Column(String, index=True)
    bookmaker = Column(String, index=True)
    market_type = Column(String)
    odds_data = Column(JSON)
```

### List of tasks to be completed

```yaml
Task 1: Setup Configuration and Database
CREATE src/config/settings.py:
  - PATTERN: Use pydantic-settings for env management
  - Load API keys, Redis URL, database connections
  - Validate all required settings present
  
CREATE alembic migrations:
  - Initialize TimescaleDB hypertables
  - Create indexes for game_id, timestamp
  - Setup user and alert tables

Task 2: Implement Odds Aggregation
CREATE src/data_collection/odds_aggregator.py:
  - PATTERN: Async HTTP client with retry logic
  - Implement The Odds API v4 client
  - Handle rate limiting with exponential backoff
  - Cache responses in Redis with TTL
  
CREATE src/data_collection/cache_manager.py:
  - Redis connection pool management
  - Implement get/set with JSON serialization
  - Add cache warming for popular markets

Task 3: Build ML Models and Analysis
CREATE src/models/ml_features.py:
  - Feature engineering for sports data
  - Handle missing data gracefully
  - Create lag features for time series
  
CREATE src/analysis/ml_models.py:
  - XGBoost classifier for game outcomes
  - Ensemble voting classifier
  - Model serialization/loading
  - Confidence scoring based on historical accuracy

Task 4: Implement Value Detection
CREATE src/analysis/value_calculator.py:
  - Calculate true probabilities from ML models
  - Compare with implied odds
  - Kelly Criterion implementation
  - Risk-adjusted sizing

Task 5: Create WebSocket Infrastructure
CREATE src/alerts/redis_pubsub.py:
  - Redis pub/sub manager class
  - Channel subscription handling
  - Message serialization
  
CREATE src/api/websocket.py:
  - WebSocket connection manager
  - Authentication via JWT
  - Graceful disconnection handling
  - Redis pub/sub integration

Task 6: Build FastAPI Application
CREATE src/api/main.py:
  - FastAPI app with lifespan events
  - CORS configuration
  - Exception handlers
  - Startup/shutdown for Redis/DB
  
CREATE src/api/routers/:
  - RESTful endpoints for odds, alerts
  - Pagination and filtering
  - Input validation

Task 7: Implement Background Tasks
CREATE celery_app.py:
  - Celery configuration with Redis broker
  - Periodic tasks for odds fetching
  - Model retraining pipeline
  
CREATE src/data_collection/line_tracker.py:
  - Monitor line movements
  - Detect steam moves
  - Store historical movements

Task 8: Add Comprehensive Testing
CREATE tests/:
  - Mock external APIs
  - Test value calculations
  - WebSocket connection tests
  - Integration tests with Redis

Task 9: Create Documentation and Scripts
CREATE README.md:
  - Architecture overview
  - Setup instructions
  - API documentation
  
CREATE scripts/:
  - Model training pipeline
  - Backtesting framework
  - Data migration scripts
```

### Per task pseudocode

```python
# Task 2: Odds Aggregator
import httpx
from typing import List, Dict
import asyncio
from datetime import datetime

class OddsAggregator:
    def __init__(self, api_key: str, cache: CacheManager):
        self.api_key = api_key
        self.base_url = "https://api.the-odds-api.com/v4"
        self.cache = cache
        
    async def fetch_odds(self, sport: SportType, markets: List[str]) -> List[MarketOdds]:
        # PATTERN: Check cache first
        cache_key = f"odds:{sport}:{','.join(markets)}"
        cached = await self.cache.get(cache_key)
        if cached:
            return cached
            
        # GOTCHA: Rate limit is 500/month on free tier
        async with httpx.AsyncClient() as client:
            params = {
                "apiKey": self.api_key,
                "sport": sport,
                "markets": ",".join(markets),
                "oddsFormat": "decimal"
            }
            
            # PATTERN: Retry with backoff
            for attempt in range(3):
                try:
                    response = await client.get(
                        f"{self.base_url}/sports/{sport}/odds",
                        params=params,
                        timeout=30.0
                    )
                    response.raise_for_status()
                    break
                except httpx.HTTPStatusError as e:
                    if e.response.status_code == 429:  # Rate limited
                        await asyncio.sleep(2 ** attempt)
                    else:
                        raise
            
            # Parse and cache
            data = response.json()
            odds = self._parse_odds_response(data)
            await self.cache.set(cache_key, odds, ttl=60)  # 1 minute cache
            
            return odds

# Task 4: Value Calculator
class ValueCalculator:
    def __init__(self, ml_model: MLPredictor):
        self.ml_model = ml_model
        
    async def find_value_bets(self, odds: List[MarketOdds]) -> List[ValueBet]:
        value_bets = []
        
        for market in odds:
            # Get ML prediction
            features = self._extract_features(market)
            true_prob = await self.ml_model.predict_probability(features)
            
            # Find best odds
            best_odds = max(market.bookmaker_odds, key=lambda x: x.odds)
            implied_prob = 1 / best_odds.odds
            
            # Calculate edge
            edge = true_prob - implied_prob
            
            # PATTERN: Only flag if edge > 5%
            if edge > 0.05:
                ev = (best_odds.odds * true_prob) - 1
                kelly = self._calculate_kelly(true_prob, best_odds.odds)
                
                value_bet = ValueBet(
                    game_id=market.game_id,
                    market=market,
                    true_probability=true_prob,
                    implied_probability=implied_prob,
                    edge=edge,
                    expected_value=ev,
                    confidence_score=self._calculate_confidence(edge, true_prob),
                    kelly_fraction=kelly
                )
                value_bets.append(value_bet)
                
        return value_bets

# Task 5: WebSocket Manager
class ConnectionManager:
    def __init__(self, redis_client: Redis):
        self.active_connections: Dict[str, WebSocket] = {}
        self.redis = redis_client
        self.pubsub = None
        
    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        self.active_connections[user_id] = websocket
        
        # Subscribe to user's channel
        if not self.pubsub:
            self.pubsub = self.redis.pubsub()
        await self.pubsub.subscribe(f"alerts:{user_id}")
        
    async def broadcast_alert(self, user_id: str, alert: Alert):
        # Publish to Redis for multi-server support
        await self.redis.publish(
            f"alerts:{user_id}",
            alert.model_dump_json()
        )
        
    async def listen_for_alerts(self):
        # PATTERN: Async generator for pub/sub messages
        async for message in self.pubsub.listen():
            if message["type"] == "message":
                user_id = message["channel"].split(":")[-1]
                if user_id in self.active_connections:
                    websocket = self.active_connections[user_id]
                    await websocket.send_text(message["data"])
```

### Integration Points
```yaml
DATABASE:
  - migration: |
      CREATE EXTENSION IF NOT EXISTS timescaledb;
      SELECT create_hypertable('odds_snapshots', 'timestamp');
      CREATE INDEX idx_odds_game_time ON odds_snapshots(game_id, timestamp DESC);
  
ENVIRONMENT:
  - add to: .env
  - vars: |
      # API Keys
      ODDS_API_KEY=your_key_here
      REDIS_URL=redis://localhost:6379/0
      DATABASE_URL=postgresql://user:pass@localhost/sportsbetting
      
      # Settings
      ALERT_THRESHOLD_EDGE=0.05
      MAX_KELLY_FRACTION=0.25
      CACHE_TTL_SECONDS=60
      
      # Celery
      CELERY_BROKER_URL=redis://localhost:6379/1
      CELERY_RESULT_BACKEND=redis://localhost:6379/2
  
DEPENDENCIES:
  - Update requirements.txt with: |
      fastapi==0.104.1
      uvicorn[standard]==0.24.0
      httpx==0.25.1
      redis==5.0.1
      celery==5.3.4
      sqlalchemy==2.0.23
      alembic==1.12.1
      psycopg2-binary==2.9.9
      scikit-learn==1.3.2
      xgboost==2.0.2
      pandas==2.1.3
      numpy==1.26.2
      pydantic==2.5.0
      pydantic-settings==2.1.0
      python-multipart==0.0.6
      websockets==12.0
      
DOCKER:
  - services: PostgreSQL with TimescaleDB, Redis, Celery worker
  - Use docker-compose for local development
```

## Validation Loop

### Level 1: Syntax & Style
```bash
# Setup virtual environment first
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt

# Run these FIRST - fix any errors before proceeding
ruff check src/ --fix           # Auto-fix style issues
mypy src/ --ignore-missing-imports  # Type checking

# Expected: No errors. If errors, READ and fix.
```

### Level 2: Unit Tests
```python
# test_value_calculator.py
import pytest
from src.analysis.value_calculator import ValueCalculator
from src.models.schemas import MarketOdds, BookmakerOdds

@pytest.mark.asyncio
async def test_find_value_bets():
    """Test value bet detection with mocked ML model"""
    mock_ml = MockMLPredictor(predicted_prob=0.65)
    calculator = ValueCalculator(mock_ml)
    
    # Create test odds where implied prob is 0.55
    odds = MarketOdds(
        home_team="Team A",
        away_team="Team B", 
        bet_type="h2h",
        bookmaker_odds=[
            BookmakerOdds(bookmaker="DK", odds=1.82, last_update=datetime.now())
        ]
    )
    
    value_bets = await calculator.find_value_bets([odds])
    
    assert len(value_bets) == 1
    assert value_bets[0].edge > 0.05  # 65% - 55% = 10% edge
    assert value_bets[0].expected_value > 0

# test_websocket.py
@pytest.mark.asyncio
async def test_websocket_connection():
    """Test WebSocket alert streaming"""
    async with TestClient(app) as client:
        async with client.websocket_connect("/ws/alerts") as websocket:
            # Send auth
            await websocket.send_json({"token": "test_jwt"})
            
            # Trigger test alert
            test_alert = Alert(
                id="test123",
                user_id="user1",
                value_bet=create_test_value_bet(),
                created_at=datetime.now(),
                notification_channels=["websocket"]
            )
            
            await redis_client.publish("alerts:user1", test_alert.json())
            
            # Receive alert
            data = await websocket.receive_json()
            assert data["id"] == "test123"
```

```bash
# Run tests iteratively until passing:
pytest tests/ -v --cov=src --cov-report=term-missing

# If failing: Debug specific test, fix code, re-run
pytest tests/test_value_calculator.py::test_find_value_bets -v -s
```

### Level 3: Integration Test
```bash
# Start services
docker-compose up -d postgres redis

# Run migrations
alembic upgrade head

# Start the API
uvicorn src.api.main:app --reload

# Test odds endpoint
curl http://localhost:8000/api/odds/nfl

# Test WebSocket connection
wscat -c ws://localhost:8000/ws/alerts \
  -H "Authorization: Bearer <token>"

# Start Celery worker
celery -A src.celery_app worker --loglevel=info

# Verify background tasks
celery -A src.celery_app inspect active
```

## Final Validation Checklist
- [ ] All tests pass: `pytest tests/ -v`
- [ ] No linting errors: `ruff check src/`
- [ ] No type errors: `mypy src/`
- [ ] API returns odds data: `curl localhost:8000/api/odds/nfl`
- [ ] WebSocket streams alerts in real-time
- [ ] Redis pub/sub works across multiple connections
- [ ] Celery processes background tasks
- [ ] TimescaleDB stores time-series data efficiently
- [ ] ML models load and predict successfully
- [ ] Docker Compose starts all services
- [ ] README has complete setup instructions

---

## Anti-Patterns to Avoid
- ❌ Don't store API keys in code - use environment variables
- ❌ Don't skip caching - API rate limits are strict
- ❌ Don't use synchronous code in async handlers
- ❌ Don't forget to handle WebSocket disconnections
- ❌ Don't ignore timezone issues - always use UTC
- ❌ Don't train ML models on biased data
- ❌ Don't bet more than Kelly fraction suggests
- ❌ Don't skip backtesting new strategies

## Confidence Score: 8.5/10

High confidence due to:
- Well-documented external APIs (The Odds API)
- Proven architectural patterns (FastAPI + Redis + Celery)
- Existing sports betting Python libraries
- Clear ML pipeline with XGBoost

Slight uncertainty on:
- Initial ML model accuracy without historical data
- Handling all edge cases in odds parsing
- Production scaling beyond 1000 users

The implementation should succeed with careful attention to rate limiting, caching, and gradual feature rollout.