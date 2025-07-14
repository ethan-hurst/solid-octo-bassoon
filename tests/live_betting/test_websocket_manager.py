"""Unit tests for WebSocket manager."""
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime, timedelta
import json

from fastapi import WebSocket
from src.live_betting.websocket_manager import (
    ConnectionManager, WebSocketClient, SubscriptionManager,
    MessageBroadcaster, RateLimiter, ConnectionPool
)
from src.models.live_schemas import LiveGameState, LiveOdds, LiveEvent


class TestConnectionManager:
    """Test WebSocket connection management."""
    
    @pytest.fixture
    def manager(self):
        """Create connection manager instance."""
        return ConnectionManager()
    
    @pytest.fixture
    def mock_websocket(self):
        """Create mock WebSocket."""
        mock = Mock(spec=WebSocket)
        mock.accept = AsyncMock()
        mock.send_json = AsyncMock()
        mock.send_text = AsyncMock()
        mock.close = AsyncMock()
        mock.client = Mock(host="127.0.0.1")
        return mock
    
    @pytest.mark.asyncio
    async def test_connect_client(self, manager, mock_websocket):
        """Test client connection."""
        client_id = await manager.connect(mock_websocket, user_id="user123")
        
        assert client_id is not None
        assert client_id in manager.active_connections
        assert manager.active_connections[client_id].user_id == "user123"
        mock_websocket.accept.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_disconnect_client(self, manager, mock_websocket):
        """Test client disconnection."""
        client_id = await manager.connect(mock_websocket, user_id="user123")
        
        await manager.disconnect(client_id)
        assert client_id not in manager.active_connections
    
    @pytest.mark.asyncio
    async def test_broadcast_to_all(self, manager):
        """Test broadcasting to all clients."""
        # Connect multiple clients
        clients = []
        for i in range(3):
            mock_ws = Mock(spec=WebSocket)
            mock_ws.send_json = AsyncMock()
            mock_ws.accept = AsyncMock()
            mock_ws.client = Mock(host=f"127.0.0.{i}")
            client_id = await manager.connect(mock_ws, user_id=f"user{i}")
            clients.append((client_id, mock_ws))
        
        message = {"type": "update", "data": "test"}
        await manager.broadcast(message)
        
        # All clients should receive message
        for _, mock_ws in clients:
            mock_ws.send_json.assert_called_with(message)
    
    @pytest.mark.asyncio
    async def test_send_personal_message(self, manager, mock_websocket):
        """Test sending message to specific client."""
        client_id = await manager.connect(mock_websocket, user_id="user123")
        
        message = {"type": "personal", "data": "for you"}
        await manager.send_personal_message(message, client_id)
        
        mock_websocket.send_json.assert_called_with(message)
    
    @pytest.mark.asyncio
    async def test_connection_error_handling(self, manager, mock_websocket):
        """Test handling of connection errors."""
        client_id = await manager.connect(mock_websocket, user_id="user123")
        
        # Simulate send error
        mock_websocket.send_json.side_effect = Exception("Connection lost")
        
        # Should handle error gracefully
        await manager.send_personal_message({"test": "data"}, client_id)
        
        # Client should be disconnected
        assert client_id not in manager.active_connections


class TestWebSocketClient:
    """Test WebSocket client functionality."""
    
    def test_client_creation(self):
        """Test client object creation."""
        mock_ws = Mock(spec=WebSocket)
        client = WebSocketClient(
            client_id="client123",
            websocket=mock_ws,
            user_id="user123"
        )
        
        assert client.client_id == "client123"
        assert client.websocket == mock_ws
        assert client.user_id == "user123"
        assert isinstance(client.connected_at, datetime)
        assert client.subscriptions == set()
    
    def test_add_remove_subscriptions(self):
        """Test subscription management."""
        client = WebSocketClient(
            client_id="client123",
            websocket=Mock(),
            user_id="user123"
        )
        
        client.add_subscription("game:123")
        client.add_subscription("sport:NBA")
        
        assert "game:123" in client.subscriptions
        assert "sport:NBA" in client.subscriptions
        
        client.remove_subscription("game:123")
        assert "game:123" not in client.subscriptions
        assert "sport:NBA" in client.subscriptions


class TestSubscriptionManager:
    """Test subscription management functionality."""
    
    @pytest.fixture
    def sub_manager(self):
        """Create subscription manager instance."""
        return SubscriptionManager()
    
    def test_subscribe_client(self, sub_manager):
        """Test client subscription."""
        sub_manager.subscribe("client123", "game:456")
        sub_manager.subscribe("client123", "sport:NBA")
        sub_manager.subscribe("client456", "game:456")
        
        # Check client subscriptions
        assert "game:456" in sub_manager.get_client_subscriptions("client123")
        assert "sport:NBA" in sub_manager.get_client_subscriptions("client123")
        
        # Check topic subscribers
        assert "client123" in sub_manager.get_topic_subscribers("game:456")
        assert "client456" in sub_manager.get_topic_subscribers("game:456")
    
    def test_unsubscribe_client(self, sub_manager):
        """Test client unsubscription."""
        sub_manager.subscribe("client123", "game:456")
        sub_manager.subscribe("client123", "sport:NBA")
        
        sub_manager.unsubscribe("client123", "game:456")
        
        assert "game:456" not in sub_manager.get_client_subscriptions("client123")
        assert "sport:NBA" in sub_manager.get_client_subscriptions("client123")
    
    def test_remove_client(self, sub_manager):
        """Test removing client from all subscriptions."""
        sub_manager.subscribe("client123", "game:456")
        sub_manager.subscribe("client123", "sport:NBA")
        sub_manager.subscribe("client123", "team:Lakers")
        
        sub_manager.remove_client("client123")
        
        assert len(sub_manager.get_client_subscriptions("client123")) == 0
        assert "client123" not in sub_manager.get_topic_subscribers("game:456")
    
    def test_pattern_matching(self, sub_manager):
        """Test subscription pattern matching."""
        sub_manager.subscribe("client123", "game:*")
        sub_manager.subscribe("client456", "game:123")
        
        # Should match both clients
        matches = sub_manager.get_matching_subscribers("game:123")
        assert "client123" in matches  # Wildcard match
        assert "client456" in matches  # Exact match
        
        # Should only match wildcard
        matches = sub_manager.get_matching_subscribers("game:789")
        assert "client123" in matches
        assert "client456" not in matches


class TestMessageBroadcaster:
    """Test message broadcasting functionality."""
    
    @pytest.fixture
    def broadcaster(self):
        """Create broadcaster instance."""
        manager = Mock()
        sub_manager = Mock()
        return MessageBroadcaster(manager, sub_manager)
    
    @pytest.mark.asyncio
    async def test_broadcast_game_update(self, broadcaster):
        """Test broadcasting game updates."""
        game_state = LiveGameState(
            game_id="game123",
            sport="NBA",
            home_team="Lakers",
            away_team="Celtics",
            home_score=85,
            away_score=82,
            period=3,
            time_remaining="5:30",
            status="LIVE",
            start_time=datetime.utcnow()
        )
        
        # Mock subscribers
        broadcaster.subscription_manager.get_matching_subscribers.return_value = {
            "client1", "client2"
        }
        
        await broadcaster.broadcast_game_update(game_state)
        
        # Should query for game and sport subscribers
        calls = broadcaster.subscription_manager.get_matching_subscribers.call_args_list
        topics = [call[0][0] for call in calls]
        assert "game:game123" in topics
        assert "sport:NBA" in topics
    
    @pytest.mark.asyncio
    async def test_broadcast_odds_update(self, broadcaster):
        """Test broadcasting odds updates."""
        odds = LiveOdds(
            odds_id="odds123",
            game_id="game123",
            bookmaker="BookA",
            bet_type="MONEYLINE",
            selection="Lakers",
            odds=1.85,
            timestamp=datetime.utcnow()
        )
        
        broadcaster.subscription_manager.get_matching_subscribers.return_value = {
            "client1"
        }
        
        await broadcaster.broadcast_odds_update(odds)
        
        broadcaster.subscription_manager.get_matching_subscribers.assert_called()
    
    @pytest.mark.asyncio
    async def test_broadcast_with_filters(self, broadcaster):
        """Test broadcasting with client filters."""
        # Set up client with filters
        broadcaster.connection_manager.active_connections = {
            "client1": Mock(
                user_id="user1",
                filters={"min_edge": 0.05}
            ),
            "client2": Mock(
                user_id="user2",
                filters={"min_edge": 0.10}
            )
        }
        
        value_bet = Mock(edge=0.07)
        
        # Should only send to client1
        recipients = await broadcaster.apply_client_filters(
            {"client1", "client2"}, value_bet, "value_bet"
        )
        
        assert "client1" in recipients
        assert "client2" not in recipients


class TestRateLimiter:
    """Test rate limiting functionality."""
    
    @pytest.fixture
    def rate_limiter(self):
        """Create rate limiter instance."""
        return RateLimiter(max_messages=10, window_seconds=60)
    
    @pytest.mark.asyncio
    async def test_rate_limit_enforcement(self, rate_limiter):
        """Test rate limit enforcement."""
        client_id = "client123"
        
        # Should allow initial messages
        for i in range(10):
            allowed = await rate_limiter.check_rate_limit(client_id)
            assert allowed
        
        # Should block after limit
        allowed = await rate_limiter.check_rate_limit(client_id)
        assert not allowed
    
    @pytest.mark.asyncio
    async def test_rate_limit_window_reset(self, rate_limiter):
        """Test rate limit window reset."""
        client_id = "client123"
        
        # Use up rate limit
        for i in range(10):
            await rate_limiter.check_rate_limit(client_id)
        
        # Simulate time passing
        rate_limiter.client_messages[client_id] = []
        
        # Should allow messages again
        allowed = await rate_limiter.check_rate_limit(client_id)
        assert allowed
    
    def test_cleanup_old_entries(self, rate_limiter):
        """Test cleanup of old rate limit entries."""
        # Add old entries
        old_time = datetime.utcnow() - timedelta(seconds=120)
        rate_limiter.client_messages["client1"] = [old_time] * 5
        rate_limiter.client_messages["client2"] = [datetime.utcnow()]
        
        rate_limiter.cleanup_old_entries()
        
        assert len(rate_limiter.client_messages["client1"]) == 0
        assert len(rate_limiter.client_messages["client2"]) == 1


class TestConnectionPool:
    """Test connection pooling functionality."""
    
    @pytest.fixture
    def pool(self):
        """Create connection pool instance."""
        return ConnectionPool(max_connections=100)
    
    def test_connection_limit(self, pool):
        """Test connection limit enforcement."""
        # Add connections up to limit
        for i in range(100):
            assert pool.can_accept_connection()
            pool.add_connection(f"client{i}", Mock())
        
        # Should reject beyond limit
        assert not pool.can_accept_connection()
    
    def test_connection_recycling(self, pool):
        """Test connection recycling."""
        # Fill pool
        for i in range(100):
            pool.add_connection(f"client{i}", Mock())
        
        # Remove some connections
        for i in range(10):
            pool.remove_connection(f"client{i}")
        
        # Should accept new connections
        assert pool.can_accept_connection()
        assert pool.get_connection_count() == 90
    
    def test_user_connection_limit(self, pool):
        """Test per-user connection limits."""
        pool.max_per_user = 3
        
        # Add connections for same user
        for i in range(3):
            assert pool.can_accept_user_connection("user123")
            pool.add_connection(f"client{i}", Mock(user_id="user123"))
        
        # Should reject 4th connection for same user
        assert not pool.can_accept_user_connection("user123")
        
        # Should allow for different user
        assert pool.can_accept_user_connection("user456")