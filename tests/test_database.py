"""Tests for database models and operations."""
import pytest
from datetime import datetime, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.database import User, OddsSnapshot, GameResult, Alert, Base
from src.models.schemas import SportType


@pytest.mark.asyncio
async def test_user_model_creation(test_db):
    """Test creating a user model."""
    user = User(
        email="test@example.com",
        username="testuser",
        hashed_password="hashed_password_123",
        is_active=True,
        sports=["NFL", "NBA"],
        min_edge=0.05,
        max_kelly_fraction=0.25,
        notification_channels=["websocket", "email"]
    )
    
    test_db.add(user)
    await test_db.commit()
    
    # Verify user was created
    result = await test_db.execute(select(User).where(User.email == "test@example.com"))
    saved_user = result.scalar_one()
    
    assert saved_user.username == "testuser"
    assert saved_user.is_active is True
    assert "NFL" in saved_user.sports
    assert saved_user.min_edge == 0.05


@pytest.mark.asyncio
async def test_odds_snapshot_model(test_db):
    """Test creating an odds snapshot."""
    snapshot = OddsSnapshot(
        timestamp=datetime.utcnow(),
        game_id="test_game_123",
        sport="NFL",
        bookmaker="DraftKings",
        market_type="h2h",
        odds_data={
            "home_team": "Team A",
            "away_team": "Team B",
            "odds": 2.10
        },
        home_team="Team A",
        away_team="Team B",
        commence_time=datetime.utcnow() + timedelta(hours=24),
        decimal_odds=2.10
    )
    
    test_db.add(snapshot)
    await test_db.commit()
    
    # Verify snapshot was created
    result = await test_db.execute(
        select(OddsSnapshot).where(OddsSnapshot.game_id == "test_game_123")
    )
    saved_snapshot = result.scalar_one()
    
    assert saved_snapshot.sport == "NFL"
    assert saved_snapshot.bookmaker == "DraftKings"
    assert saved_snapshot.decimal_odds == 2.10
    assert saved_snapshot.odds_data["home_team"] == "Team A"


@pytest.mark.asyncio
async def test_game_result_model(test_db):
    """Test creating a game result."""
    game_result = GameResult(
        game_id="test_game_456",
        sport="NBA",
        home_team="Lakers",
        away_team="Celtics",
        home_score=110,
        away_score=108,
        winner="Lakers",
        game_date=datetime.utcnow().date(),
        season="2023-24"
    )
    
    test_db.add(game_result)
    await test_db.commit()
    
    # Verify result was created
    result = await test_db.execute(
        select(GameResult).where(GameResult.game_id == "test_game_456")
    )
    saved_result = result.scalar_one()
    
    assert saved_result.sport == "NBA"
    assert saved_result.winner == "Lakers"
    assert saved_result.home_score == 110
    assert saved_result.away_score == 108


@pytest.mark.asyncio
async def test_alert_model(test_db):
    """Test creating an alert."""
    # First create a user
    user = User(
        email="alert_user@example.com",
        username="alertuser",
        hashed_password="hashed_password_123",
        is_active=True
    )
    test_db.add(user)
    await test_db.commit()
    
    # Create alert
    alert = Alert(
        user_id=user.id,
        value_bet_data={
            "game_id": "test_game_789",
            "edge": 0.10,
            "confidence_score": 0.85
        },
        notification_channels=["websocket", "email"]
    )
    
    test_db.add(alert)
    await test_db.commit()
    
    # Verify alert was created
    result = await test_db.execute(
        select(Alert).where(Alert.user_id == user.id)
    )
    saved_alert = result.scalar_one()
    
    assert saved_alert.value_bet_data["game_id"] == "test_game_789"
    assert saved_alert.value_bet_data["edge"] == 0.10
    assert "websocket" in saved_alert.notification_channels


@pytest.mark.asyncio
async def test_user_relationships(test_db):
    """Test user relationships with alerts."""
    # Create user
    user = User(
        email="relationship_test@example.com",
        username="relationuser",
        hashed_password="hashed_password_123",
        is_active=True
    )
    test_db.add(user)
    await test_db.commit()
    
    # Create multiple alerts for the user
    for i in range(3):
        alert = Alert(
            user_id=user.id,
            value_bet_data={"game_id": f"game_{i}", "edge": 0.05 + i * 0.01},
            notification_channels=["websocket"]
        )
        test_db.add(alert)
    
    await test_db.commit()
    
    # Query user with alerts
    result = await test_db.execute(
        select(User).where(User.id == user.id)
    )
    user_with_alerts = result.scalar_one()
    
    # Query alerts for this user
    alerts_result = await test_db.execute(
        select(Alert).where(Alert.user_id == user.id)
    )
    user_alerts = alerts_result.scalars().all()
    
    assert len(user_alerts) == 3
    assert all(alert.user_id == user.id for alert in user_alerts)


@pytest.mark.asyncio
async def test_odds_snapshot_querying(test_db):
    """Test querying odds snapshots."""
    # Create multiple snapshots for different sports
    sports = ["NFL", "NBA", "MLB"]
    
    for i, sport in enumerate(sports):
        for j in range(2):
            snapshot = OddsSnapshot(
                timestamp=datetime.utcnow() - timedelta(hours=i*j),
                game_id=f"{sport.lower()}_game_{j}",
                sport=sport,
                bookmaker=f"Bookmaker_{j}",
                market_type="h2h",
                odds_data={"odds": 2.0 + j * 0.1},
                home_team=f"Home_{sport}_{j}",
                away_team=f"Away_{sport}_{j}",
                commence_time=datetime.utcnow() + timedelta(days=1),
                decimal_odds=2.0 + j * 0.1
            )
            test_db.add(snapshot)
    
    await test_db.commit()
    
    # Query NFL snapshots only
    nfl_result = await test_db.execute(
        select(OddsSnapshot).where(OddsSnapshot.sport == "NFL")
    )
    nfl_snapshots = nfl_result.scalars().all()
    
    assert len(nfl_snapshots) == 2
    assert all(snapshot.sport == "NFL" for snapshot in nfl_snapshots)
    
    # Query by bookmaker
    bookmaker_result = await test_db.execute(
        select(OddsSnapshot).where(OddsSnapshot.bookmaker == "Bookmaker_0")
    )
    bookmaker_snapshots = bookmaker_result.scalars().all()
    
    assert len(bookmaker_snapshots) == 3  # One for each sport


@pytest.mark.asyncio
async def test_database_constraints(test_db):
    """Test database constraints and validations."""
    # Test unique email constraint
    user1 = User(
        email="unique@example.com",
        username="user1",
        hashed_password="password1",
        is_active=True
    )
    test_db.add(user1)
    await test_db.commit()
    
    # Try to create another user with same email
    user2 = User(
        email="unique@example.com",
        username="user2",
        hashed_password="password2",
        is_active=True
    )
    test_db.add(user2)
    
    # This should raise an error due to unique constraint
    with pytest.raises(Exception):
        await test_db.commit()


@pytest.mark.asyncio
async def test_timestamp_defaults(test_db):
    """Test that timestamps are set automatically."""
    user = User(
        email="timestamp_test@example.com",
        username="timestampuser",
        hashed_password="password",
        is_active=True
    )
    test_db.add(user)
    await test_db.commit()
    
    # Check that created_at was set
    assert user.created_at is not None
    assert isinstance(user.created_at, datetime)
    
    # Check that created_at is recent (within last minute)
    assert datetime.utcnow() - user.created_at < timedelta(minutes=1)


def test_user_model_repr():
    """Test user model string representation."""
    user = User(
        email="repr_test@example.com",
        username="repruser",
        hashed_password="password",
        is_active=True
    )
    
    repr_str = repr(user)
    assert "repruser" in repr_str
    assert "User" in repr_str


def test_odds_snapshot_repr():
    """Test odds snapshot string representation."""
    snapshot = OddsSnapshot(
        timestamp=datetime.utcnow(),
        game_id="repr_game",
        sport="NFL",
        bookmaker="TestBookmaker",
        market_type="h2h",
        odds_data={},
        home_team="Home",
        away_team="Away",
        commence_time=datetime.utcnow(),
        decimal_odds=2.0
    )
    
    repr_str = repr(snapshot)
    assert "repr_game" in repr_str
    assert "NFL" in repr_str