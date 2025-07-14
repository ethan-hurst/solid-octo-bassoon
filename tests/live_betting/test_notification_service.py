"""Unit tests for notification service."""
import pytest
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime, timedelta
import json

from src.live_betting.notification_service import (
    NotificationService, NotificationChannel, NotificationPriority,
    UserPreferences, NotificationQueue, RateLimiter,
    EmailNotifier, SMSNotifier, PushNotifier, WebSocketNotifier,
    NotificationFormatter, NotificationHistory
)
from src.models.live_schemas import LiveValueBet, LiveEvent, LiveEventType


class TestNotificationService:
    """Test main NotificationService class."""
    
    @pytest.fixture
    def notification_service(self):
        """Create notification service instance."""
        return NotificationService()
    
    @pytest.fixture
    def sample_value_bet(self):
        """Create sample value bet."""
        return LiveValueBet(
            bet_id="bet123",
            game_id="game456",
            bookmaker="BookA",
            bet_type="MONEYLINE",
            selection="Lakers",
            odds=2.10,
            true_probability=0.55,
            edge=0.05,
            expected_value=0.155,
            stake_recommendation=50.0,
            confidence=0.85,
            timestamp=datetime.utcnow()
        )
    
    @pytest.mark.asyncio
    async def test_send_notification(self, notification_service):
        """Test sending notification through service."""
        user_id = "user123"
        notification = {
            "type": "value_bet",
            "data": {"bet_id": "123", "edge": 0.08}
        }
        
        # Mock channel notifiers
        notification_service.notifiers[NotificationChannel.EMAIL] = Mock(
            send=AsyncMock(return_value=True)
        )
        
        # Mock user preferences
        with patch.object(
            notification_service,
            'get_user_preferences',
            return_value=Mock(
                channels=[NotificationChannel.EMAIL],
                min_edge=0.05
            )
        ):
            result = await notification_service.send_notification(
                user_id, notification, NotificationPriority.HIGH
            )
            
            assert result["success"]
            assert NotificationChannel.EMAIL in result["channels_sent"]
    
    @pytest.mark.asyncio
    async def test_send_value_bet_alert(self, notification_service, sample_value_bet):
        """Test value bet alert sending."""
        user_id = "user123"
        
        # Mock notifiers
        for channel in NotificationChannel:
            notification_service.notifiers[channel] = Mock(
                send=AsyncMock(return_value=True)
            )
        
        with patch.object(
            notification_service,
            'get_user_preferences',
            return_value=Mock(
                channels=[NotificationChannel.WEBSOCKET, NotificationChannel.PUSH],
                min_edge=0.03,
                value_bet_alerts=True
            )
        ):
            await notification_service.send_value_bet_alert(user_id, sample_value_bet)
            
            # Should send to both channels
            notification_service.notifiers[NotificationChannel.WEBSOCKET].send.assert_called()
            notification_service.notifiers[NotificationChannel.PUSH].send.assert_called()
    
    @pytest.mark.asyncio
    async def test_rate_limiting(self, notification_service):
        """Test notification rate limiting."""
        user_id = "user123"
        
        # Mock rate limiter to block
        with patch.object(
            notification_service.rate_limiter,
            'check_rate_limit',
            return_value=False
        ):
            result = await notification_service.send_notification(
                user_id, {"test": "data"}, NotificationPriority.LOW
            )
            
            assert not result["success"]
            assert "rate_limited" in result
    
    @pytest.mark.asyncio
    async def test_priority_queue_processing(self, notification_service):
        """Test priority-based queue processing."""
        # Add notifications with different priorities
        notification_service.queue.add(
            "user1", {"msg": "low"}, NotificationPriority.LOW
        )
        notification_service.queue.add(
            "user2", {"msg": "high"}, NotificationPriority.HIGH
        )
        notification_service.queue.add(
            "user3", {"msg": "medium"}, NotificationPriority.MEDIUM
        )
        
        # Process queue - should handle high priority first
        processed = []
        while not notification_service.queue.is_empty():
            item = notification_service.queue.get()
            processed.append(item)
        
        assert processed[0]["notification"]["msg"] == "high"
        assert processed[-1]["notification"]["msg"] == "low"


class TestUserPreferences:
    """Test user preference management."""
    
    def test_default_preferences(self):
        """Test default preference creation."""
        prefs = UserPreferences()
        
        assert prefs.channels == [NotificationChannel.WEBSOCKET]
        assert prefs.min_edge == 0.05
        assert prefs.quiet_hours_start is None
        assert prefs.value_bet_alerts
    
    def test_preference_validation(self):
        """Test preference validation."""
        prefs = UserPreferences(
            channels=[NotificationChannel.EMAIL, NotificationChannel.SMS],
            min_edge=0.08,
            max_notifications_per_hour=20
        )
        
        assert NotificationChannel.EMAIL in prefs.channels
        assert prefs.min_edge == 0.08
        assert prefs.max_notifications_per_hour == 20
    
    def test_quiet_hours_check(self):
        """Test quiet hours functionality."""
        prefs = UserPreferences(
            quiet_hours_start=22,  # 10 PM
            quiet_hours_end=8      # 8 AM
        )
        
        # During quiet hours
        with patch('datetime.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2024, 1, 1, 23, 0)  # 11 PM
            assert prefs.is_quiet_hours()
        
        # Outside quiet hours
        with patch('datetime.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2024, 1, 1, 12, 0)  # Noon
            assert not prefs.is_quiet_hours()


class TestNotificationQueue:
    """Test notification queue functionality."""
    
    @pytest.fixture
    def queue(self):
        """Create notification queue instance."""
        return NotificationQueue()
    
    def test_add_and_get_notifications(self, queue):
        """Test adding and retrieving notifications."""
        queue.add("user1", {"data": "test1"}, NotificationPriority.HIGH)
        queue.add("user2", {"data": "test2"}, NotificationPriority.LOW)
        
        assert not queue.is_empty()
        
        # Should get high priority first
        item = queue.get()
        assert item["user_id"] == "user1"
        assert item["priority"] == NotificationPriority.HIGH
    
    def test_batch_processing(self, queue):
        """Test batch notification processing."""
        # Add multiple notifications
        for i in range(10):
            queue.add(f"user{i}", {"data": f"test{i}"}, NotificationPriority.MEDIUM)
        
        batch = queue.get_batch(5)
        assert len(batch) == 5
        assert queue.size() == 5
    
    def test_priority_ordering(self, queue):
        """Test priority-based ordering."""
        queue.add("user1", {"msg": "urgent"}, NotificationPriority.URGENT)
        queue.add("user2", {"msg": "high"}, NotificationPriority.HIGH)
        queue.add("user3", {"msg": "medium"}, NotificationPriority.MEDIUM)
        queue.add("user4", {"msg": "low"}, NotificationPriority.LOW)
        
        # Get all in order
        order = []
        while not queue.is_empty():
            item = queue.get()
            order.append(item["notification"]["msg"])
        
        assert order == ["urgent", "high", "medium", "low"]


class TestEmailNotifier:
    """Test email notification functionality."""
    
    @pytest.fixture
    def email_notifier(self):
        """Create email notifier instance."""
        return EmailNotifier()
    
    @pytest.mark.asyncio
    async def test_send_email(self, email_notifier):
        """Test email sending."""
        with patch('smtplib.SMTP') as mock_smtp:
            mock_server = Mock()
            mock_smtp.return_value.__enter__.return_value = mock_server
            
            result = await email_notifier.send(
                user_id="user123",
                notification={
                    "subject": "Value Bet Alert",
                    "body": "New value bet available"
                }
            )
            
            assert result
            mock_server.send_message.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_email_formatting(self, email_notifier):
        """Test email content formatting."""
        value_bet = Mock(
            selection="Lakers",
            odds=2.10,
            edge=0.08,
            expected_value=0.168,
            bookmaker="BookA"
        )
        
        formatted = email_notifier.format_value_bet_email(value_bet)
        assert "Lakers" in formatted["body"]
        assert "2.10" in formatted["body"]
        assert "8.0%" in formatted["body"]
        assert "BookA" in formatted["body"]


class TestSMSNotifier:
    """Test SMS notification functionality."""
    
    @pytest.fixture
    def sms_notifier(self):
        """Create SMS notifier instance."""
        return SMSNotifier()
    
    @pytest.mark.asyncio
    async def test_send_sms(self, sms_notifier):
        """Test SMS sending."""
        with patch.object(sms_notifier, 'twilio_client') as mock_twilio:
            mock_twilio.messages.create.return_value = Mock(sid="MSG123")
            
            result = await sms_notifier.send(
                user_id="user123",
                notification={
                    "message": "Value bet: Lakers @ 2.10 (8% edge)"
                }
            )
            
            assert result
            mock_twilio.messages.create.assert_called_once()
    
    def test_sms_length_limit(self, sms_notifier):
        """Test SMS message length limiting."""
        long_message = "A" * 200
        truncated = sms_notifier.truncate_message(long_message)
        assert len(truncated) <= 160
        assert truncated.endswith("...")


class TestPushNotifier:
    """Test push notification functionality."""
    
    @pytest.fixture
    def push_notifier(self):
        """Create push notifier instance."""
        return PushNotifier()
    
    @pytest.mark.asyncio
    async def test_send_push_notification(self, push_notifier):
        """Test push notification sending."""
        with patch.object(push_notifier, 'fcm_client') as mock_fcm:
            mock_fcm.send.return_value = Mock(success=True)
            
            result = await push_notifier.send(
                user_id="user123",
                notification={
                    "title": "Value Bet Alert",
                    "body": "New opportunity available",
                    "data": {"bet_id": "123"}
                }
            )
            
            assert result
    
    def test_push_payload_formatting(self, push_notifier):
        """Test push notification payload formatting."""
        payload = push_notifier.format_push_payload(
            title="Test Alert",
            body="Test message",
            data={"key": "value"},
            badge=1
        )
        
        assert payload["notification"]["title"] == "Test Alert"
        assert payload["notification"]["body"] == "Test message"
        assert payload["data"]["key"] == "value"
        assert payload["notification"]["badge"] == 1


class TestWebSocketNotifier:
    """Test WebSocket notification functionality."""
    
    @pytest.fixture
    def ws_notifier(self):
        """Create WebSocket notifier instance."""
        manager = Mock()
        return WebSocketNotifier(connection_manager=manager)
    
    @pytest.mark.asyncio
    async def test_send_websocket_notification(self, ws_notifier):
        """Test WebSocket notification sending."""
        ws_notifier.connection_manager.send_to_user = AsyncMock()
        
        result = await ws_notifier.send(
            user_id="user123",
            notification={
                "type": "value_bet",
                "data": {"bet_id": "123"}
            }
        )
        
        assert result
        ws_notifier.connection_manager.send_to_user.assert_called_once_with(
            "user123",
            {
                "type": "notification",
                "payload": {
                    "type": "value_bet",
                    "data": {"bet_id": "123"}
                }
            }
        )


class TestNotificationFormatter:
    """Test notification formatting functionality."""
    
    @pytest.fixture
    def formatter(self):
        """Create formatter instance."""
        return NotificationFormatter()
    
    def test_format_value_bet(self, formatter):
        """Test value bet formatting."""
        value_bet = Mock(
            selection="Lakers -5.5",
            odds=1.95,
            edge=0.065,
            expected_value=0.127,
            bookmaker="Pinnacle",
            stake_recommendation=75.0
        )
        
        formatted = formatter.format_value_bet(value_bet)
        assert "Lakers -5.5" in formatted["title"]
        assert "6.5%" in formatted["body"]
        assert "1.95" in formatted["body"]
        assert "$75" in formatted["body"]
    
    def test_format_live_event(self, formatter):
        """Test live event formatting."""
        event = Mock(
            event_type=LiveEventType.MOMENTUM_SHIFT,
            team="Celtics",
            description="10-0 run in last 2 minutes",
            impact_score=4.5
        )
        
        formatted = formatter.format_live_event(event)
        assert "Momentum Shift" in formatted["title"]
        assert "Celtics" in formatted["body"]
        assert "10-0 run" in formatted["body"]
    
    def test_format_for_channel(self, formatter):
        """Test channel-specific formatting."""
        notification = {
            "title": "Test Alert",
            "body": "This is a test message with some details",
            "data": {"id": "123"}
        }
        
        # Email should be verbose
        email_format = formatter.format_for_channel(
            notification, NotificationChannel.EMAIL
        )
        assert len(email_format["body"]) >= len(notification["body"])
        
        # SMS should be concise
        sms_format = formatter.format_for_channel(
            notification, NotificationChannel.SMS
        )
        assert len(sms_format["body"]) < 160


class TestNotificationHistory:
    """Test notification history tracking."""
    
    @pytest.fixture
    def history(self):
        """Create notification history instance."""
        return NotificationHistory()
    
    def test_add_notification(self, history):
        """Test adding notification to history."""
        history.add(
            user_id="user123",
            notification_type="value_bet",
            channel=NotificationChannel.EMAIL,
            success=True
        )
        
        user_history = history.get_user_history("user123")
        assert len(user_history) == 1
        assert user_history[0]["type"] == "value_bet"
        assert user_history[0]["success"]
    
    def test_get_recent_notifications(self, history):
        """Test retrieving recent notifications."""
        # Add notifications at different times
        base_time = datetime.utcnow()
        for i in range(10):
            with patch('datetime.datetime') as mock_dt:
                mock_dt.utcnow.return_value = base_time - timedelta(hours=i)
                history.add(
                    user_id="user123",
                    notification_type="alert",
                    channel=NotificationChannel.PUSH,
                    success=True
                )
        
        # Get last hour
        recent = history.get_recent(
            user_id="user123",
            hours=1
        )
        assert len(recent) <= 2  # Only notifications from last hour
    
    def test_notification_statistics(self, history):
        """Test notification statistics calculation."""
        # Add mix of successful and failed notifications
        for i in range(10):
            history.add(
                user_id="user123",
                notification_type="value_bet",
                channel=NotificationChannel.EMAIL,
                success=i % 3 != 0  # Every 3rd fails
            )
        
        stats = history.get_user_stats("user123")
        assert stats["total"] == 10
        assert stats["successful"] == 7
        assert stats["failed"] == 3
        assert stats["success_rate"] == 0.7