"""Pytest configuration and fixtures."""
import pytest
import asyncio
from typing import AsyncGenerator, Generator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from fastapi.testclient import TestClient
from httpx import AsyncClient
import os

# Set test environment
os.environ["TESTING"] = "1"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["REDIS_URL"] = "redis://localhost:6379/15"  # Use test database
os.environ["ODDS_API_KEY"] = "test_api_key"

from src.api.main import app
from src.models.database import Base
from src.config.settings import settings


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_engine():
    """Create test database engine."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        future=True
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    await engine.dispose()


@pytest.fixture
async def test_db(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create test database session."""
    async_session = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session
        await session.rollback()


@pytest.fixture
def test_client() -> Generator[TestClient, None, None]:
    """Create test client for FastAPI app."""
    with TestClient(app) as client:
        yield client


@pytest.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Create async test client."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
def mock_odds_response():
    """Mock response from The Odds API."""
    return [
        {
            "id": "test_game_123",
            "sport_key": "americanfootball_nfl",
            "sport_title": "NFL",
            "commence_time": "2024-01-20T18:00:00Z",
            "home_team": "Kansas City Chiefs",
            "away_team": "Buffalo Bills",
            "bookmakers": [
                {
                    "key": "draftkings",
                    "title": "DraftKings",
                    "markets": [
                        {
                            "key": "h2h",
                            "outcomes": [
                                {
                                    "name": "Kansas City Chiefs",
                                    "price": 1.91
                                },
                                {
                                    "name": "Buffalo Bills",
                                    "price": 1.91
                                }
                            ]
                        }
                    ]
                }
            ]
        }
    ]


@pytest.fixture
def test_user():
    """Create test user data."""
    from src.models.schemas import User, SportType
    
    return User(
        id="test_user_123",
        email="test@example.com",
        username="testuser",
        is_active=True,
        sports=[SportType.NFL, SportType.NBA],
        min_edge=0.05,
        max_kelly_fraction=0.25,
        notification_channels=["websocket", "email"]
    )


@pytest.fixture
def test_value_bet():
    """Create test value bet."""
    from src.models.schemas import ValueBet, MarketOdds, BookmakerOdds, SportType, BetType
    from datetime import datetime, timedelta
    
    market_odds = MarketOdds(
        game_id="test_game_123",
        sport=SportType.NFL,
        home_team="Team A",
        away_team="Team B",
        commence_time=datetime.utcnow() + timedelta(hours=24),
        bet_type=BetType.MONEYLINE,
        bookmaker_odds=[
            BookmakerOdds(
                bookmaker="DraftKings",
                odds=2.10,
                last_update=datetime.utcnow()
            )
        ]
    )
    
    return ValueBet(
        game_id="test_game_123",
        market=market_odds,
        true_probability=0.52,
        implied_probability=0.476,
        edge=0.044,
        expected_value=0.092,
        confidence_score=0.75,
        kelly_fraction=0.022
    )


@pytest.fixture
def auth_headers(test_user):
    """Create authentication headers."""
    from jose import jwt
    from src.config.settings import settings
    
    token_data = {"sub": test_user.id}
    token = jwt.encode(token_data, settings.secret_key, algorithm=settings.algorithm)
    
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def mock_cache_manager():
    """Create mock cache manager."""
    from unittest.mock import AsyncMock, MagicMock
    
    cache = AsyncMock()
    cache.get = AsyncMock(return_value=None)
    cache.set = AsyncMock(return_value=True)
    cache.delete = AsyncMock(return_value=True)
    cache.connect = AsyncMock()
    cache.disconnect = AsyncMock()
    
    return cache


@pytest.fixture
async def mock_ml_predictor():
    """Create mock ML predictor."""
    from unittest.mock import AsyncMock
    
    predictor = AsyncMock()
    predictor.predict_probability = AsyncMock(return_value=0.55)
    
    return predictor