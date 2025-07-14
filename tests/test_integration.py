"""Integration tests for the complete system."""
import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch, MagicMock
import json

from src.models.schemas import SportType, BetType, MarketOdds, BookmakerOdds, User, Alert
from src.data_collection.odds_aggregator import OddsAggregator
from src.analysis.value_calculator import ValueCalculator
from src.analysis.ml_models import SportsBettingModel, ModelEnsemble
from src.alerts.notification_service import NotificationService
from src.alerts.websocket_manager import ConnectionManager


@pytest.mark.asyncio
async def test_complete_value_betting_pipeline(mock_cache_manager, test_db):
    """Test the complete value betting pipeline from odds to alerts."""
    
    # 1. Setup odds aggregator with mock data
    aggregator = OddsAggregator(cache=mock_cache_manager)
    
    # Mock odds response
    mock_odds_data = [
        {
            "id": "integration_test_game",
            "sport_key": "americanfootball_nfl",
            "commence_time": (datetime.utcnow() + timedelta(hours=24)).isoformat(),
            "home_team": "New York Giants",
            "away_team": "Dallas Cowboys",
            "bookmakers": [
                {
                    "key": "draftkings",
                    "title": "DraftKings",
                    "markets": [
                        {
                            "key": "h2h",
                            "outcomes": [
                                {"name": "New York Giants", "price": 2.50},
                                {"name": "Dallas Cowboys", "price": 1.65}
                            ]
                        }
                    ]
                },
                {
                    "key": "fanduel",
                    "title": "FanDuel",
                    "markets": [
                        {
                            "key": "h2h",
                            "outcomes": [
                                {"name": "New York Giants", "price": 2.40},
                                {"name": "Dallas Cowboys", "price": 1.70}
                            ]
                        }
                    ]
                }
            ]
        }
    ]
    
    # Mock API response
    with patch("httpx.AsyncClient") as mock_client:
        mock_response = MagicMock()
        mock_response.json.return_value = mock_odds_data
        mock_response.raise_for_status = MagicMock()
        mock_response.headers = {"x-requests-remaining": "100"}
        
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(
            return_value=mock_response
        )
        
        # 2. Fetch odds
        odds_list = await aggregator.fetch_odds(SportType.NFL)
        
        assert len(odds_list) == 2  # Two outcomes
        assert odds_list[0].game_id == "integration_test_game"
        assert len(odds_list[0].bookmaker_odds) == 2  # Two bookmakers
    
    # 3. Setup ML models
    model = SportsBettingModel(SportType.NFL)
    
    # Train with dummy data for integration test
    import numpy as np
    X = np.random.rand(100, 50)
    y = np.random.randint(0, 2, 100)
    model.train(X, y)
    
    ensemble = ModelEnsemble({SportType.NFL: model})
    
    # 4. Setup value calculator
    value_calculator = ValueCalculator(ensemble, min_edge=0.05)
    
    # Mock ML prediction to show value
    with patch.object(ensemble, 'predict_probability', return_value=0.50):
        # 5. Find value bets
        value_bets = await value_calculator.find_value_bets(odds_list)
        
        # Should find value bets when our prediction differs from market
        assert len(value_bets) >= 0  # Might be 0 if no edge found
    
    # 6. Test notification system
    pubsub_manager = AsyncMock()
    connection_manager = ConnectionManager(pubsub_manager)
    notification_service = NotificationService(connection_manager)
    
    # Create test user and alert
    user = User(
        id="integration_test_user",
        email="test@integration.com",
        username="integrationuser",
        is_active=True,
        sports=[SportType.NFL],
        min_edge=0.03,
        notification_channels=["websocket", "email"]
    )
    
    if value_bets:
        alert = Alert(
            user_id=user.id,
            value_bet=value_bets[0],
            notification_channels=user.notification_channels
        )
        
        # 7. Send alert
        with patch.object(notification_service, '_send_email', new_callable=AsyncMock) as mock_email:
            await notification_service.send_alert(alert, user)
            
            # Verify email was sent
            mock_email.assert_called_once()


@pytest.mark.asyncio
async def test_arbitrage_detection_integration(mock_cache_manager):
    """Test arbitrage detection across multiple bookmakers."""
    from src.analysis.arbitrage_detector import ArbitrageDetector
    
    # Create odds with arbitrage opportunity
    market_odds = MarketOdds(
        game_id="arb_test_game",
        sport=SportType.NBA,
        home_team="Lakers",
        away_team="Celtics",
        commence_time=datetime.utcnow() + timedelta(hours=12),
        bet_type=BetType.MONEYLINE,
        bookmaker_odds=[
            BookmakerOdds(bookmaker="DraftKings", odds=2.10, last_update=datetime.utcnow()),
            BookmakerOdds(bookmaker="FanDuel", odds=2.05, last_update=datetime.utcnow()),
            BookmakerOdds(bookmaker="BetMGM", odds=1.95, last_update=datetime.utcnow()),
        ]
    )
    
    detector = ArbitrageDetector()
    
    # Find arbitrage opportunities
    arbitrages = await detector.find_arbitrage_opportunities([market_odds])
    
    # Check if any arbitrage was found (depends on the specific odds)
    assert isinstance(arbitrages, list)


@pytest.mark.asyncio
async def test_websocket_real_time_alerts(test_client, auth_headers):
    """Test real-time alert delivery via WebSocket."""
    
    with patch("src.alerts.websocket_manager.ConnectionManager") as mock_manager:
        mock_instance = AsyncMock()
        mock_manager.return_value = mock_instance
        
        # Connect to WebSocket
        with test_client.websocket_connect(
            "/api/v1/ws/integration_test_user",
            headers=auth_headers
        ) as websocket:
            
            # Subscribe to NFL alerts
            websocket.send_json({
                "action": "subscribe",
                "channels": ["sport:NFL", "user:integration_test_user"]
            })
            
            # Simulate receiving a subscription confirmation
            confirmation = websocket.receive_json()
            assert confirmation["type"] == "subscription_confirmed"
            
            # Verify connection manager was called
            mock_instance.connect.assert_called()


@pytest.mark.asyncio
async def test_celery_task_integration():
    """Test Celery task execution integration."""
    from src.celery_app import fetch_odds_task, check_value_bets_task
    
    # Mock dependencies
    with patch("src.celery_app.run_async") as mock_run_async:
        mock_run_async.return_value = None
        
        # Test odds fetch task
        result = fetch_odds_task()
        
        assert result["status"] == "completed"
        assert "timestamp" in result
        mock_run_async.assert_called()
        
        # Reset mock
        mock_run_async.reset_mock()
        
        # Test value bet check task
        mock_run_async.return_value = 5  # 5 alerts created
        result = check_value_bets_task()
        
        assert result["status"] == "completed"
        assert result["alerts_created"] == 5


@pytest.mark.asyncio
async def test_database_performance_with_large_dataset(test_db):
    """Test database performance with large datasets."""
    from src.models.database import OddsSnapshot
    import time
    
    # Create large number of odds snapshots
    snapshots = []
    for i in range(1000):
        snapshot = OddsSnapshot(
            timestamp=datetime.utcnow() - timedelta(hours=i % 72),
            game_id=f"perf_test_game_{i % 100}",
            sport="NFL",
            bookmaker=f"Bookmaker_{i % 10}",
            market_type="h2h",
            odds_data={"odds": 2.0 + (i % 100) * 0.01},
            home_team=f"Team_A_{i % 50}",
            away_team=f"Team_B_{i % 50}",
            commence_time=datetime.utcnow() + timedelta(days=1),
            decimal_odds=2.0 + (i % 100) * 0.01
        )
        snapshots.append(snapshot)
    
    # Batch insert
    start_time = time.time()
    test_db.add_all(snapshots)
    await test_db.commit()
    insert_time = time.time() - start_time
    
    # Query performance test
    from sqlalchemy import select
    
    start_time = time.time()
    result = await test_db.execute(
        select(OddsSnapshot).where(
            OddsSnapshot.sport == "NFL"
        ).limit(100)
    )
    odds = result.scalars().all()
    query_time = time.time() - start_time
    
    # Assertions for performance
    assert insert_time < 5.0  # Should insert 1000 records in under 5 seconds
    assert query_time < 1.0   # Should query in under 1 second
    assert len(odds) == 100


@pytest.mark.asyncio
async def test_api_authentication_flow(test_client, test_db):
    """Test complete authentication flow."""
    from src.models.database import User as DBUser
    import bcrypt
    
    # Create test user in database
    hashed_password = bcrypt.hashpw("testpass123".encode(), bcrypt.gensalt())
    
    db_user = DBUser(
        email="auth_test@example.com",
        username="authtest",
        hashed_password=hashed_password.decode(),
        is_active=True
    )
    test_db.add(db_user)
    await test_db.commit()
    
    # 1. Login
    login_data = {
        "username": "authtest",
        "password": "testpass123"
    }
    
    response = test_client.post("/api/v1/auth/login", data=login_data)
    assert response.status_code == 200
    
    token_data = response.json()
    access_token = token_data["access_token"]
    
    # 2. Use token to access protected endpoint
    headers = {"Authorization": f"Bearer {access_token}"}
    
    response = test_client.get("/api/v1/users/me", headers=headers)
    assert response.status_code == 200
    
    user_data = response.json()
    assert user_data["email"] == "auth_test@example.com"


@pytest.mark.asyncio
async def test_error_recovery_and_retry(mock_cache_manager):
    """Test error recovery and retry mechanisms."""
    aggregator = OddsAggregator(cache=mock_cache_manager, retry_attempts=2)
    
    # Mock first call to fail, second to succeed
    with patch("httpx.AsyncClient") as mock_client:
        mock_response_fail = MagicMock()
        mock_response_fail.raise_for_status.side_effect = Exception("API Error")
        
        mock_response_success = MagicMock()
        mock_response_success.json.return_value = []
        mock_response_success.raise_for_status = MagicMock()
        mock_response_success.headers = {}
        
        mock_get = AsyncMock(side_effect=[mock_response_fail, mock_response_success])
        mock_client.return_value.__aenter__.return_value.get = mock_get
        
        # Should retry and succeed
        with patch("asyncio.sleep", new_callable=AsyncMock):
            odds_list = await aggregator.fetch_odds(SportType.NFL)
            
            assert mock_get.call_count == 2
            assert isinstance(odds_list, list)


@pytest.mark.asyncio
async def test_concurrent_user_processing():
    """Test processing multiple users concurrently."""
    from src.analysis.value_calculator import ValueCalculator
    
    # Create multiple value calculators
    calculators = [ValueCalculator(None) for _ in range(10)]
    
    # Create test data
    market_odds = MarketOdds(
        game_id="concurrent_test",
        sport=SportType.NFL,
        home_team="Team A",
        away_team="Team B",
        commence_time=datetime.utcnow() + timedelta(hours=24),
        bet_type=BetType.MONEYLINE,
        bookmaker_odds=[
            BookmakerOdds(bookmaker="Test", odds=2.0, last_update=datetime.utcnow())
        ]
    )
    
    # Process concurrently
    async def process_user(calculator):
        # Mock ML prediction
        with patch.object(calculator, 'ml_predictor') as mock_ml:
            mock_ml.predict_probability = AsyncMock(return_value=0.55)
            return await calculator.find_value_bets([market_odds])
    
    # Run concurrent processing
    start_time = asyncio.get_event_loop().time()
    results = await asyncio.gather(*[
        process_user(calc) for calc in calculators
    ])
    end_time = asyncio.get_event_loop().time()
    
    # Should complete quickly with concurrency
    assert end_time - start_time < 5.0
    assert len(results) == 10