"""Tests for websocket_manager functionality."""
import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from src.alerts.websocket_manager import ConnectionManager
from src.alerts.redis_pubsub import RedisPubSubManager
from src.models.schemas import ValueBet, Alert, SportType


@pytest.mark.asyncio
async def test_connection_manager_init():
    """Test ConnectionManager initialization."""
    pubsub = AsyncMock()
    manager = ConnectionManager(pubsub)
    
    assert manager.pubsub == pubsub
    assert manager.active_connections == {}
    assert manager.user_connections == {}


@pytest.mark.asyncio
async def test_connect_websocket():
    """Test connecting a WebSocket."""
    pubsub = AsyncMock()
    manager = ConnectionManager(pubsub)
    
    websocket = AsyncMock()
    websocket.accept = AsyncMock()
    
    user_id = "test_user_123"
    
    await manager.connect(websocket, user_id)
    
    websocket.accept.assert_called_once()
    assert user_id in manager.active_connections
    assert websocket in manager.user_connections[user_id]


@pytest.mark.asyncio
async def test_disconnect_websocket():
    """Test disconnecting a WebSocket."""
    pubsub = AsyncMock()
    manager = ConnectionManager(pubsub)
    
    websocket = AsyncMock()
    user_id = "test_user_123"
    
    # First connect
    manager.active_connections[user_id] = websocket
    manager.user_connections[user_id] = [websocket]
    
    # Then disconnect
    await manager.disconnect(websocket, user_id)
    
    assert user_id not in manager.active_connections
    assert user_id not in manager.user_connections


@pytest.mark.asyncio
async def test_send_personal_message():
    """Test sending personal message."""
    pubsub = AsyncMock()
    manager = ConnectionManager(pubsub)
    
    websocket = AsyncMock()
    websocket.send_text = AsyncMock()
    
    user_id = "test_user_123"
    manager.active_connections[user_id] = websocket
    
    message = {"type": "alert", "data": "test"}
    await manager.send_personal_message(message, user_id)
    
    websocket.send_text.assert_called_once_with(json.dumps(message))


@pytest.mark.asyncio
async def test_broadcast_to_sport():
    """Test broadcasting to sport subscribers."""
    pubsub = AsyncMock()
    pubsub.publish = AsyncMock()
    
    manager = ConnectionManager(pubsub)
    
    message = {"type": "odds_update", "sport": "NFL"}
    sport = SportType.NFL
    
    await manager.broadcast_to_sport(message, sport)
    
    pubsub.publish.assert_called_once_with(
        f"sport:{sport.value}",
        json.dumps(message)
    )


@pytest.mark.asyncio
async def test_broadcast_to_all():
    """Test broadcasting to all connected clients."""
    pubsub = AsyncMock()
    pubsub.publish = AsyncMock()
    
    manager = ConnectionManager(pubsub)
    
    message = {"type": "system", "data": "maintenance"}
    
    await manager.broadcast_to_all(message)
    
    pubsub.publish.assert_called_once_with(
        "broadcast:all",
        json.dumps(message)
    )


@pytest.mark.asyncio
async def test_handle_websocket_error():
    """Test handling WebSocket errors."""
    pubsub = AsyncMock()
    manager = ConnectionManager(pubsub)
    
    websocket = AsyncMock()
    websocket.send_text = AsyncMock(side_effect=Exception("Connection closed"))
    
    user_id = "test_user_123"
    manager.active_connections[user_id] = websocket
    manager.user_connections[user_id] = [websocket]
    
    # Should handle error gracefully
    message = {"type": "test"}
    await manager.send_personal_message(message, user_id)
    
    # Connection should be removed after error
    assert user_id not in manager.active_connections


@pytest.mark.asyncio
async def test_subscribe_to_channel():
    """Test subscribing to channels."""
    pubsub = AsyncMock()
    pubsub.subscribe = AsyncMock()
    
    manager = ConnectionManager(pubsub)
    
    user_id = "test_user_123"
    channels = ["sport:NFL", "sport:NBA", f"user:{user_id}"]
    
    await manager.subscribe_to_channels(user_id, channels)
    
    for channel in channels:
        pubsub.subscribe.assert_any_call(channel)


@pytest.mark.asyncio
async def test_redis_pubsub_manager():
    """Test Redis PubSub manager."""
    with patch("redis.asyncio.Redis") as mock_redis:
        mock_redis_instance = AsyncMock()
        mock_redis.from_url.return_value = mock_redis_instance
        
        pubsub_manager = RedisPubSubManager()
        await pubsub_manager.connect()
        
        # Test publish
        await pubsub_manager.publish("test_channel", "test_message")
        mock_redis_instance.publish.assert_called_with("test_channel", "test_message")
        
        # Test subscribe
        callback = AsyncMock()
        await pubsub_manager.subscribe("test_channel", callback)
        
        # Test disconnect
        await pubsub_manager.disconnect()
        mock_redis_instance.close.assert_called_once()


@pytest.mark.asyncio
async def test_process_pubsub_message():
    """Test processing pubsub messages."""
    pubsub = AsyncMock()
    manager = ConnectionManager(pubsub)
    
    # Setup WebSocket connections
    websocket1 = AsyncMock()
    websocket2 = AsyncMock()
    
    manager.active_connections = {
        "user1": websocket1,
        "user2": websocket2
    }
    
    # Test user-specific message
    user_message = {
        "channel": "user:user1",
        "data": json.dumps({"type": "alert", "content": "test"})
    }
    
    await manager._process_message(user_message)
    
    websocket1.send_text.assert_called_once()
    websocket2.send_text.assert_not_called()


@pytest.mark.asyncio
async def test_alert_serialization():
    """Test alert serialization for WebSocket."""
    from src.alerts.websocket_manager import ConnectionManager
    
    pubsub = AsyncMock()
    manager = ConnectionManager(pubsub)
    
    # Create test alert
    value_bet = ValueBet(
        game_id="test_game",
        market=None,
        true_probability=0.60,
        implied_probability=0.45,
        edge=0.15,
        expected_value=0.20,
        confidence_score=0.85,
        kelly_fraction=0.10
    )
    
    alert = Alert(
        user_id="test_user",
        value_bet=value_bet,
        notification_channels=["websocket"]
    )
    
    # Format alert for WebSocket
    formatted = manager.format_alert(alert)
    
    assert formatted["type"] == "value_bet_alert"
    assert formatted["timestamp"] is not None
    assert formatted["data"]["edge"] == 0.15
    assert formatted["data"]["confidence_score"] == 0.85


@pytest.mark.asyncio
async def test_websocket_heartbeat():
    """Test WebSocket heartbeat mechanism."""
    pubsub = AsyncMock()
    manager = ConnectionManager(pubsub)
    
    websocket = AsyncMock()
    websocket.send_text = AsyncMock()
    
    user_id = "test_user"
    manager.active_connections[user_id] = websocket
    
    # Send heartbeat
    await manager.send_heartbeat(user_id)
    
    websocket.send_text.assert_called_once()
    call_args = websocket.send_text.call_args[0][0]
    message = json.loads(call_args)
    
    assert message["type"] == "heartbeat"
    assert "timestamp" in message


@pytest.mark.asyncio
async def test_multiple_connections_same_user():
    """Test handling multiple connections from same user."""
    pubsub = AsyncMock()
    manager = ConnectionManager(pubsub)
    
    user_id = "test_user"
    websocket1 = AsyncMock()
    websocket2 = AsyncMock()
    
    # Connect first WebSocket
    await manager.connect(websocket1, user_id)
    
    # Connect second WebSocket
    await manager.connect(websocket2, user_id)
    
    # Both should be in user_connections
    assert len(manager.user_connections[user_id]) == 2
    assert websocket1 in manager.user_connections[user_id]
    assert websocket2 in manager.user_connections[user_id]
    
    # Send message should go to both
    message = {"type": "test"}
    await manager.send_personal_message(message, user_id)
    
    websocket1.send_text.assert_called_once()
    websocket2.send_text.assert_called_once()


@pytest.mark.asyncio
async def test_connection_cleanup_on_error():
    """Test connection cleanup when error occurs."""
    pubsub = AsyncMock()
    manager = ConnectionManager(pubsub)
    
    # Create multiple connections
    websocket1 = AsyncMock()
    websocket2 = AsyncMock()
    websocket2.send_text = AsyncMock(side_effect=Exception("Connection lost"))
    
    user_id = "test_user"
    manager.user_connections[user_id] = [websocket1, websocket2]
    manager.active_connections[user_id] = websocket1
    
    # Send message - websocket2 should fail and be removed
    message = {"type": "test"}
    await manager.send_personal_message(message, user_id)
    
    # Only websocket1 should remain
    assert len(manager.user_connections[user_id]) == 1
    assert websocket1 in manager.user_connections[user_id]
    assert websocket2 not in manager.user_connections[user_id]