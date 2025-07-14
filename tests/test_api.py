"""Tests for API endpoints."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timedelta
import json

from src.models.schemas import SportType, BetType, MarketOdds, BookmakerOdds, ValueBet


@pytest.mark.asyncio
async def test_health_check(test_client):
    """Test health check endpoint."""
    response = test_client.get("/health")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert "version" in data


@pytest.mark.asyncio
async def test_get_supported_sports(test_client):
    """Test getting supported sports."""
    response = test_client.get("/api/v1/odds/sports")
    
    assert response.status_code == 200
    sports = response.json()
    assert isinstance(sports, list)
    assert len(sports) > 0
    assert all(sport in [s.value for s in SportType] for sport in sports)


@pytest.mark.asyncio
async def test_get_current_odds(test_client, mock_cache_manager):
    """Test getting current odds."""
    with patch("src.api.routers.odds.cache_manager", mock_cache_manager):
        with patch("src.api.routers.odds.OddsAggregator") as mock_aggregator:
            # Mock odds data
            mock_odds = [
                MarketOdds(
                    game_id="test_game_1",
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
            ]
            
            mock_aggregator.return_value.fetch_odds = AsyncMock(return_value=mock_odds)
            
            response = test_client.get("/api/v1/odds/current/NFL")
            
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["game_id"] == "test_game_1"


@pytest.mark.asyncio
async def test_get_odds_history(test_client, test_db):
    """Test getting odds history."""
    from src.models.database import OddsSnapshot
    
    # Create test snapshots
    snapshots = []
    for i in range(5):
        snapshot = OddsSnapshot(
            timestamp=datetime.utcnow() - timedelta(hours=i),
            game_id="test_game_1",
            sport="NFL",
            bookmaker="DraftKings",
            market_type="h2h",
            odds_data={"odds": 2.0 + (i * 0.1)},
            home_team="Team A",
            away_team="Team B",
            commence_time=datetime.utcnow() + timedelta(days=1),
            decimal_odds=2.0 + (i * 0.1)
        )
        test_db.add(snapshot)
        snapshots.append(snapshot)
    
    await test_db.commit()
    
    response = test_client.get("/api/v1/odds/history/test_game_1")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 5


@pytest.mark.asyncio
async def test_get_value_bets_authenticated(test_client, auth_headers):
    """Test getting value bets (authenticated)."""
    with patch("src.api.routers.analysis.ValueCalculator") as mock_calculator:
        mock_value_bets = [
            ValueBet(
                game_id="test_game_1",
                market=None,
                true_probability=0.60,
                implied_probability=0.45,
                edge=0.15,
                expected_value=0.20,
                confidence_score=0.85,
                kelly_fraction=0.10
            )
        ]
        
        mock_calculator.return_value.find_value_bets = AsyncMock(
            return_value=mock_value_bets
        )
        
        response = test_client.get(
            "/api/v1/analysis/value-bets?sport=NFL",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["edge"] == 0.15


@pytest.mark.asyncio
async def test_get_value_bets_unauthenticated(test_client):
    """Test getting value bets without authentication."""
    response = test_client.get("/api/v1/analysis/value-bets?sport=NFL")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_find_arbitrage(test_client, auth_headers):
    """Test finding arbitrage opportunities."""
    with patch("src.api.routers.analysis.ArbitrageDetector") as mock_detector:
        mock_arbs = [
            {
                "game_id": "test_game_1",
                "profit_percentage": 2.5,
                "bets": [
                    {"bookmaker": "DraftKings", "outcome": "Team A", "odds": 2.20},
                    {"bookmaker": "FanDuel", "outcome": "Team B", "odds": 2.10}
                ]
            }
        ]
        
        mock_detector.return_value.find_arbitrage_opportunities = AsyncMock(
            return_value=mock_arbs
        )
        
        response = test_client.get(
            "/api/v1/analysis/arbitrage?sport=NFL",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["profit_percentage"] == 2.5


@pytest.mark.asyncio
async def test_calculate_bet_size(test_client, auth_headers, test_value_bet):
    """Test calculating bet size."""
    request_data = {
        "value_bet": test_value_bet.model_dump(),
        "bankroll": 10000,
        "existing_exposure": 0
    }
    
    response = test_client.post(
        "/api/v1/analysis/bet-size",
        json=request_data,
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "bet_size" in data
    assert "percentage_of_bankroll" in data
    assert data["bet_size"] > 0
    assert data["bet_size"] < 10000


@pytest.mark.asyncio
async def test_get_alerts(test_client, auth_headers, test_db):
    """Test getting user alerts."""
    from src.models.database import Alert as DBAlert
    
    # Create test alerts
    for i in range(3):
        alert = DBAlert(
            user_id=1,  # Matches test user
            value_bet_data={
                "game_id": f"test_game_{i}",
                "edge": 0.10 + (i * 0.02)
            },
            notification_channels=["websocket"],
            sent_at=datetime.utcnow() if i < 2 else None
        )
        test_db.add(alert)
    
    await test_db.commit()
    
    response = test_client.get("/api/v1/alerts/", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3


@pytest.mark.asyncio
async def test_update_alert_preferences(test_client, auth_headers):
    """Test updating alert preferences."""
    preferences = {
        "min_edge": 0.08,
        "sports": ["NFL", "NBA"],
        "notification_channels": ["websocket", "email"],
        "max_alerts_per_day": 10
    }
    
    response = test_client.put(
        "/api/v1/alerts/preferences",
        json=preferences,
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["min_edge"] == 0.08
    assert "NFL" in data["sports"]


@pytest.mark.asyncio
async def test_mark_alert_read(test_client, auth_headers, test_db):
    """Test marking alert as read."""
    from src.models.database import Alert as DBAlert
    
    # Create test alert
    alert = DBAlert(
        user_id=1,
        value_bet_data={"game_id": "test_game_1"},
        notification_channels=["websocket"]
    )
    test_db.add(alert)
    await test_db.commit()
    
    response = test_client.patch(
        f"/api/v1/alerts/{alert.id}/read",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    
    # Verify in database
    await test_db.refresh(alert)
    assert alert.read_at is not None


@pytest.mark.asyncio
async def test_websocket_endpoint(test_client, auth_headers):
    """Test WebSocket connection endpoint."""
    with test_client.websocket_connect(
        "/api/v1/ws/test_user_123",
        headers=auth_headers
    ) as websocket:
        # Send subscription message
        websocket.send_json({
            "action": "subscribe",
            "channels": ["sport:NFL", "sport:NBA"]
        })
        
        # Receive acknowledgment
        data = websocket.receive_json()
        assert data["type"] == "subscription_confirmed"


@pytest.mark.asyncio
async def test_rate_limiting(test_client):
    """Test API rate limiting."""
    # Make multiple requests quickly
    responses = []
    for _ in range(150):  # Exceed rate limit
        response = test_client.get("/api/v1/odds/sports")
        responses.append(response)
    
    # Check that some requests were rate limited
    rate_limited = [r for r in responses if r.status_code == 429]
    assert len(rate_limited) > 0


@pytest.mark.asyncio
async def test_get_user_profile(test_client, auth_headers):
    """Test getting user profile."""
    response = test_client.get("/api/v1/users/me", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["username"] == "testuser"


@pytest.mark.asyncio
async def test_update_user_profile(test_client, auth_headers):
    """Test updating user profile."""
    update_data = {
        "username": "newusername",
        "sports": ["NFL", "NBA", "MLB"],
        "min_edge": 0.06
    }
    
    response = test_client.put(
        "/api/v1/users/me",
        json=update_data,
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "newusername"
    assert len(data["sports"]) == 3


@pytest.mark.asyncio
async def test_error_handling_invalid_sport(test_client):
    """Test error handling for invalid sport."""
    response = test_client.get("/api/v1/odds/current/INVALID_SPORT")
    
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data


@pytest.mark.asyncio
async def test_error_handling_database_error(test_client, auth_headers):
    """Test error handling for database errors."""
    with patch("src.api.routers.alerts.get_db") as mock_get_db:
        mock_get_db.side_effect = Exception("Database connection failed")
        
        response = test_client.get("/api/v1/alerts/", headers=auth_headers)
        
        assert response.status_code == 500
        data = response.json()
        assert "detail" in data


@pytest.mark.asyncio
async def test_cors_headers(test_client):
    """Test CORS headers are properly set."""
    response = test_client.options("/api/v1/odds/sports")
    
    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers
    assert "access-control-allow-methods" in response.headers


@pytest.mark.asyncio
async def test_request_id_tracking(test_client):
    """Test request ID is included in responses."""
    response = test_client.get("/api/v1/odds/sports")
    
    assert response.status_code == 200
    assert "x-request-id" in response.headers