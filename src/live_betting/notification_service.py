"""Live betting alert and notification service."""
import asyncio
import logging
from typing import Dict, List, Optional, Set, Any, Union
from datetime import datetime, timedelta
from collections import defaultdict, deque
from enum import Enum
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from src.models.live_schemas import (
    LiveValueBet, LiveEvent, LiveOdds, LivePrediction,
    LiveSubscription, LiveAlertSubscription
)
from src.data_collection.cache_manager import CacheManager
from src.live_betting.websocket_manager import LiveBettingWebSocketManager

logger = logging.getLogger(__name__)


class NotificationChannel(str, Enum):
    """Available notification channels."""
    WEBSOCKET = "websocket"
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    DISCORD = "discord"
    SLACK = "slack"


class AlertType(str, Enum):
    """Types of alerts."""
    VALUE_BET = "value_bet"
    LINE_MOVEMENT = "line_movement"
    GAME_EVENT = "game_event"
    PREDICTION_UPDATE = "prediction_update"
    SYSTEM = "system"


class AlertPriority(str, Enum):
    """Alert priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class NotificationTemplate:
    """Template for notifications."""
    
    def __init__(self, channel: NotificationChannel):
        self.channel = channel
        
    def format_value_bet_alert(self, value_bet: LiveValueBet, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Format value bet alert."""
        if self.channel == NotificationChannel.WEBSOCKET:
            return {
                "type": "value_bet_alert",
                "priority": "high",
                "title": f"Value Bet Alert: {value_bet.edge:.1%} Edge",
                "message": f"{value_bet.bet_type} bet on {value_bet.selection}",
                "data": {
                    "game_id": value_bet.game_id,
                    "bookmaker": value_bet.bookmaker,
                    "odds": value_bet.odds,
                    "edge": value_bet.edge,
                    "kelly_fraction": value_bet.kelly_fraction,
                    "confidence": value_bet.confidence
                },
                "timestamp": datetime.utcnow().isoformat()
            }
            
        elif self.channel == NotificationChannel.EMAIL:
            return {
                "subject": f"Value Bet Alert: {value_bet.edge:.1%} Edge Found",
                "html_body": self._create_email_template(value_bet, user_data),
                "text_body": self._create_text_template(value_bet)
            }
            
        elif self.channel == NotificationChannel.SMS:
            return {
                "message": f"Value Bet: {value_bet.edge:.1%} edge on {value_bet.selection} at {value_bet.bookmaker}. Odds: {value_bet.odds}"
            }
            
        return {"message": "Value bet alert"}
    
    def format_line_movement_alert(self, odds: LiveOdds, movement_data: Dict[str, Any]) -> Dict[str, Any]:
        """Format line movement alert."""
        movement_size = movement_data.get("movement_size", 0)
        direction = movement_data.get("direction", "unknown")
        
        if self.channel == NotificationChannel.WEBSOCKET:
            return {
                "type": "line_movement_alert",
                "priority": "medium",
                "title": f"Line Movement: {movement_size:.2f} points {direction}",
                "message": f"{odds.bet_type} line moved at {odds.bookmaker}",
                "data": {
                    "game_id": odds.game_id,
                    "bookmaker": odds.bookmaker,
                    "new_odds": odds.odds,
                    "movement_size": movement_size,
                    "direction": direction
                },
                "timestamp": datetime.utcnow().isoformat()
            }
            
        return {"message": f"Line movement: {movement_size:.2f} {direction}"}
    
    def format_game_event_alert(self, event: LiveEvent) -> Dict[str, Any]:
        """Format game event alert."""
        if self.channel == NotificationChannel.WEBSOCKET:
            return {
                "type": "game_event_alert",
                "priority": "medium" if event.impact_score > 0.1 else "low",
                "title": f"Game Event: {event.event_type.value.title()}",
                "message": event.description,
                "data": {
                    "game_id": event.game_id,
                    "event_type": event.event_type.value,
                    "impact_score": event.impact_score,
                    "probability_change": event.probability_change
                },
                "timestamp": event.timestamp.isoformat()
            }
            
        return {"message": event.description}
    
    def _create_email_template(self, value_bet: LiveValueBet, user_data: Dict[str, Any]) -> str:
        """Create HTML email template."""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; }}
                .header {{ background-color: #2c3e50; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; }}
                .value-bet {{ background-color: #e8f5e8; border: 1px solid #27ae60; padding: 15px; margin: 10px 0; }}
                .metrics {{ display: flex; justify-content: space-between; margin: 15px 0; }}
                .metric {{ text-align: center; }}
                .footer {{ background-color: #f8f9fa; padding: 15px; text-align: center; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🎯 Value Bet Alert</h1>
                <p>A high-value betting opportunity has been detected!</p>
            </div>
            
            <div class="content">
                <div class="value-bet">
                    <h2>{value_bet.bet_type.title()} Bet on {value_bet.selection}</h2>
                    <p><strong>Bookmaker:</strong> {value_bet.bookmaker}</p>
                    <p><strong>Game:</strong> {value_bet.game_id}</p>
                    
                    <div class="metrics">
                        <div class="metric">
                            <h3>{value_bet.edge:.1%}</h3>
                            <p>Edge</p>
                        </div>
                        <div class="metric">
                            <h3>{value_bet.odds}</h3>
                            <p>Odds</p>
                        </div>
                        <div class="metric">
                            <h3>{value_bet.confidence:.1%}</h3>
                            <p>Confidence</p>
                        </div>
                        <div class="metric">
                            <h3>{value_bet.kelly_fraction:.1%}</h3>
                            <p>Kelly %</p>
                        </div>
                    </div>
                    
                    <p><strong>Fair Odds:</strong> {value_bet.fair_odds:.2f}</p>
                    <p><strong>Detected At:</strong> {value_bet.detected_at.strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
                    <p><strong>Expires At:</strong> {value_bet.expires_at.strftime('%Y-%m-%d %H:%M:%S UTC') if value_bet.expires_at else 'No expiry'}</p>
                </div>
                
                <p><strong>Note:</strong> This alert was generated based on our ML models and current market data. 
                Please verify the bet is still available and consider your risk tolerance before placing any bets.</p>
            </div>
            
            <div class="footer">
                <p>Sports Betting Edge Finder - Live Betting Alerts</p>
                <p>To unsubscribe or modify your alert preferences, visit your dashboard.</p>
            </div>
        </body>
        </html>
        """
    
    def _create_text_template(self, value_bet: LiveValueBet) -> str:
        """Create plain text email template."""
        return f"""
        VALUE BET ALERT
        
        A high-value betting opportunity has been detected!
        
        Bet Details:
        - Type: {value_bet.bet_type}
        - Selection: {value_bet.selection}
        - Bookmaker: {value_bet.bookmaker}
        - Game: {value_bet.game_id}
        
        Metrics:
        - Edge: {value_bet.edge:.1%}
        - Odds: {value_bet.odds}
        - Fair Odds: {value_bet.fair_odds:.2f}
        - Confidence: {value_bet.confidence:.1%}
        - Kelly Fraction: {value_bet.kelly_fraction:.1%}
        
        Detected: {value_bet.detected_at.strftime('%Y-%m-%d %H:%M:%S UTC')}
        Expires: {value_bet.expires_at.strftime('%Y-%m-%d %H:%M:%S UTC') if value_bet.expires_at else 'No expiry'}
        
        Please verify the bet is still available before placing.
        
        Sports Betting Edge Finder
        """


class UserPreferences:
    """User notification preferences."""
    
    def __init__(
        self,
        user_id: str,
        channels: List[NotificationChannel] = None,
        min_edge: float = 0.02,
        min_confidence: float = 0.65,
        sports: List[str] = None,
        teams: List[str] = None,
        quiet_hours: Dict[str, str] = None,
        max_alerts_per_hour: int = 10
    ):
        """Initialize user preferences.
        
        Args:
            user_id: User identifier
            channels: Preferred notification channels
            min_edge: Minimum edge threshold
            min_confidence: Minimum confidence threshold
            sports: Preferred sports
            teams: Preferred teams
            quiet_hours: Quiet hours (start/end time)
            max_alerts_per_hour: Rate limit for alerts
        """
        self.user_id = user_id
        self.channels = channels or [NotificationChannel.WEBSOCKET]
        self.min_edge = min_edge
        self.min_confidence = min_confidence
        self.sports = sports or []
        self.teams = teams or []
        self.quiet_hours = quiet_hours or {}
        self.max_alerts_per_hour = max_alerts_per_hour
        self.is_active = True
    
    def should_send_alert(self, alert_data: Dict[str, Any]) -> bool:
        """Check if alert should be sent based on preferences.
        
        Args:
            alert_data: Alert data
            
        Returns:
            True if alert should be sent
        """
        try:
            # Check if notifications are active
            if not self.is_active:
                return False
            
            # Check quiet hours
            if self._is_quiet_time():
                return False
            
            # Check thresholds for value bets
            if alert_data.get("type") == "value_bet_alert":
                data = alert_data.get("data", {})
                edge = data.get("edge", 0)
                confidence = data.get("confidence", 0)
                
                if edge < self.min_edge or confidence < self.min_confidence:
                    return False
            
            # Check sport/team preferences
            game_id = alert_data.get("data", {}).get("game_id", "")
            if self.sports and not any(sport in game_id for sport in self.sports):
                return False
            
            if self.teams and not any(team in game_id for team in self.teams):
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking alert preferences: {e}")
            return False
    
    def _is_quiet_time(self) -> bool:
        """Check if current time is in quiet hours."""
        try:
            if not self.quiet_hours:
                return False
            
            start_time = self.quiet_hours.get("start")
            end_time = self.quiet_hours.get("end")
            
            if not start_time or not end_time:
                return False
            
            now = datetime.utcnow().time()
            start = datetime.strptime(start_time, "%H:%M").time()
            end = datetime.strptime(end_time, "%H:%M").time()
            
            if start <= end:
                return start <= now <= end
            else:  # Crosses midnight
                return now >= start or now <= end
                
        except Exception as e:
            logger.error(f"Error checking quiet time: {e}")
            return False


class RateLimiter:
    """Rate limiting for notifications."""
    
    def __init__(self):
        self.user_alerts: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        
    def can_send_alert(self, user_id: str, max_per_hour: int = 10) -> bool:
        """Check if user can receive another alert.
        
        Args:
            user_id: User identifier
            max_per_hour: Maximum alerts per hour
            
        Returns:
            True if alert can be sent
        """
        try:
            now = datetime.utcnow()
            hour_ago = now - timedelta(hours=1)
            
            # Clean old alerts
            user_alerts = self.user_alerts[user_id]
            while user_alerts and user_alerts[0] < hour_ago:
                user_alerts.popleft()
            
            # Check rate limit
            if len(user_alerts) >= max_per_hour:
                return False
            
            # Add current alert
            user_alerts.append(now)
            return True
            
        except Exception as e:
            logger.error(f"Error checking rate limit: {e}")
            return False


class NotificationDeliveryService:
    """Handle delivery of notifications across different channels."""
    
    def __init__(self, websocket_manager: Optional[LiveBettingWebSocketManager] = None):
        """Initialize delivery service.
        
        Args:
            websocket_manager: WebSocket manager for real-time notifications
        """
        self.websocket_manager = websocket_manager
        self.email_config = self._load_email_config()
        self.delivery_stats = defaultdict(int)
        
    def _load_email_config(self) -> Dict[str, Any]:
        """Load email configuration."""
        # In production, load from settings
        return {
            "smtp_server": "smtp.gmail.com",
            "smtp_port": 587,
            "username": "",  # Load from env
            "password": "",  # Load from env
            "from_email": "alerts@sportsbettingedgefinder.com"
        }
    
    async def send_websocket(self, user_id: str, alert_data: Dict[str, Any]) -> bool:
        """Send WebSocket notification.
        
        Args:
            user_id: User identifier
            alert_data: Alert data
            
        Returns:
            True if sent successfully
        """
        try:
            if not self.websocket_manager:
                return False
            
            success = await self.websocket_manager.send_user_alert(user_id, alert_data)
            
            if success:
                self.delivery_stats["websocket_success"] += 1
            else:
                self.delivery_stats["websocket_failed"] += 1
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending WebSocket notification: {e}")
            self.delivery_stats["websocket_error"] += 1
            return False
    
    async def send_email(self, user_email: str, alert_data: Dict[str, Any]) -> bool:
        """Send email notification.
        
        Args:
            user_email: User email address
            alert_data: Alert data
            
        Returns:
            True if sent successfully
        """
        try:
            if not self.email_config.get("username") or not user_email:
                return False
            
            # Create message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = alert_data.get("subject", "Sports Betting Alert")
            msg["From"] = self.email_config["from_email"]
            msg["To"] = user_email
            
            # Add text and HTML parts
            if "text_body" in alert_data:
                text_part = MIMEText(alert_data["text_body"], "plain")
                msg.attach(text_part)
            
            if "html_body" in alert_data:
                html_part = MIMEText(alert_data["html_body"], "html")
                msg.attach(html_part)
            
            # Send email
            with smtplib.SMTP(self.email_config["smtp_server"], self.email_config["smtp_port"]) as server:
                server.starttls()
                server.login(self.email_config["username"], self.email_config["password"])
                server.send_message(msg)
            
            self.delivery_stats["email_success"] += 1
            return True
            
        except Exception as e:
            logger.error(f"Error sending email notification: {e}")
            self.delivery_stats["email_error"] += 1
            return False
    
    async def send_sms(self, phone_number: str, message: str) -> bool:
        """Send SMS notification.
        
        Args:
            phone_number: Phone number
            message: SMS message
            
        Returns:
            True if sent successfully
        """
        try:
            # This would integrate with SMS service (Twilio, AWS SNS, etc.)
            # For now, just log the message
            logger.info(f"SMS to {phone_number}: {message}")
            self.delivery_stats["sms_success"] += 1
            return True
            
        except Exception as e:
            logger.error(f"Error sending SMS notification: {e}")
            self.delivery_stats["sms_error"] += 1
            return False
    
    async def send_push(self, device_token: str, alert_data: Dict[str, Any]) -> bool:
        """Send push notification.
        
        Args:
            device_token: Device token
            alert_data: Alert data
            
        Returns:
            True if sent successfully
        """
        try:
            # This would integrate with push service (Firebase, APNs, etc.)
            # For now, just log the notification
            logger.info(f"Push to {device_token}: {alert_data.get('title', 'Alert')}")
            self.delivery_stats["push_success"] += 1
            return True
            
        except Exception as e:
            logger.error(f"Error sending push notification: {e}")
            self.delivery_stats["push_error"] += 1
            return False
    
    def get_delivery_stats(self) -> Dict[str, int]:
        """Get delivery statistics."""
        return dict(self.delivery_stats)


class LiveAlertService:
    """Main live betting alert and notification service."""
    
    def __init__(
        self,
        cache_manager: CacheManager,
        websocket_manager: Optional[LiveBettingWebSocketManager] = None
    ):
        """Initialize alert service.
        
        Args:
            cache_manager: Cache manager
            websocket_manager: WebSocket manager
        """
        self.cache_manager = cache_manager
        self.websocket_manager = websocket_manager
        self.delivery_service = NotificationDeliveryService(websocket_manager)
        self.rate_limiter = RateLimiter()
        
        # User management
        self.user_preferences: Dict[str, UserPreferences] = {}
        self.user_contacts: Dict[str, Dict[str, str]] = {}  # user_id -> contact info
        
        # Alert tracking
        self.alert_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.alert_stats = {
            "total_alerts": 0,
            "alerts_sent": 0,
            "alerts_filtered": 0,
            "last_reset": datetime.utcnow()
        }
        
        # Templates
        self.templates = {
            channel: NotificationTemplate(channel) 
            for channel in NotificationChannel
        }
    
    async def send_value_bet_alert(self, value_bet: LiveValueBet) -> Dict[str, int]:
        """Send value bet alert to relevant users.
        
        Args:
            value_bet: Value bet data
            
        Returns:
            Delivery statistics
        """
        try:
            self.alert_stats["total_alerts"] += 1
            sent_count = 0
            filtered_count = 0
            
            # Get users who should receive this alert
            relevant_users = await self._find_relevant_users(value_bet)
            
            for user_id in relevant_users:
                preferences = self.user_preferences.get(user_id)
                if not preferences:
                    continue
                
                # Check rate limiting
                if not self.rate_limiter.can_send_alert(user_id, preferences.max_alerts_per_hour):
                    filtered_count += 1
                    continue
                
                # Send across preferred channels
                for channel in preferences.channels:
                    success = await self._send_channel_alert(
                        user_id, channel, value_bet, preferences
                    )
                    if success:
                        sent_count += 1
            
            self.alert_stats["alerts_sent"] += sent_count
            self.alert_stats["alerts_filtered"] += filtered_count
            
            # Store alert in history
            await self._store_alert_history("value_bet", value_bet.model_dump())
            
            logger.info(f"Value bet alert sent to {sent_count} users, filtered {filtered_count}")
            
            return {
                "sent": sent_count,
                "filtered": filtered_count,
                "total_users": len(relevant_users)
            }
            
        except Exception as e:
            logger.error(f"Error sending value bet alert: {e}")
            return {"sent": 0, "filtered": 0, "total_users": 0}
    
    async def send_line_movement_alert(
        self, 
        odds: LiveOdds, 
        movement_data: Dict[str, Any]
    ) -> Dict[str, int]:
        """Send line movement alert.
        
        Args:
            odds: Odds data
            movement_data: Movement details
            
        Returns:
            Delivery statistics
        """
        try:
            # Only send for significant movements
            significance = movement_data.get("significance", 0)
            if significance < 0.05:  # 5% threshold
                return {"sent": 0, "filtered": 0, "total_users": 0}
            
            self.alert_stats["total_alerts"] += 1
            sent_count = 0
            
            # Get users subscribed to this game/sport
            relevant_users = await self._find_users_for_game(odds.game_id)
            
            for user_id in relevant_users:
                preferences = self.user_preferences.get(user_id)
                if not preferences:
                    continue
                
                # Send line movement alert
                for channel in preferences.channels:
                    template = self.templates[channel]
                    alert_data = template.format_line_movement_alert(odds, movement_data)
                    
                    if preferences.should_send_alert(alert_data):
                        success = await self._deliver_alert(user_id, channel, alert_data)
                        if success:
                            sent_count += 1
            
            self.alert_stats["alerts_sent"] += sent_count
            
            return {"sent": sent_count, "filtered": 0, "total_users": len(relevant_users)}
            
        except Exception as e:
            logger.error(f"Error sending line movement alert: {e}")
            return {"sent": 0, "filtered": 0, "total_users": 0}
    
    async def send_game_event_alert(self, event: LiveEvent) -> Dict[str, int]:
        """Send game event alert.
        
        Args:
            event: Game event
            
        Returns:
            Delivery statistics
        """
        try:
            # Only send for significant events
            if event.impact_score < 0.1:  # 10% impact threshold
                return {"sent": 0, "filtered": 0, "total_users": 0}
            
            self.alert_stats["total_alerts"] += 1
            sent_count = 0
            
            # Get users subscribed to this game
            relevant_users = await self._find_users_for_game(event.game_id)
            
            for user_id in relevant_users:
                preferences = self.user_preferences.get(user_id)
                if not preferences:
                    continue
                
                # Send game event alert
                for channel in preferences.channels:
                    template = self.templates[channel]
                    alert_data = template.format_game_event_alert(event)
                    
                    if preferences.should_send_alert(alert_data):
                        success = await self._deliver_alert(user_id, channel, alert_data)
                        if success:
                            sent_count += 1
            
            self.alert_stats["alerts_sent"] += sent_count
            
            return {"sent": sent_count, "filtered": 0, "total_users": len(relevant_users)}
            
        except Exception as e:
            logger.error(f"Error sending game event alert: {e}")
            return {"sent": 0, "filtered": 0, "total_users": 0}
    
    async def _find_relevant_users(self, value_bet: LiveValueBet) -> List[str]:
        """Find users who should receive value bet alert.
        
        Args:
            value_bet: Value bet data
            
        Returns:
            List of user IDs
        """
        try:
            relevant_users = []
            
            for user_id, preferences in self.user_preferences.items():
                # Check if user meets thresholds
                if (value_bet.edge >= preferences.min_edge and 
                    value_bet.confidence >= preferences.min_confidence):
                    relevant_users.append(user_id)
            
            return relevant_users
            
        except Exception as e:
            logger.error(f"Error finding relevant users: {e}")
            return []
    
    async def _find_users_for_game(self, game_id: str) -> List[str]:
        """Find users subscribed to a specific game.
        
        Args:
            game_id: Game identifier
            
        Returns:
            List of user IDs
        """
        try:
            # Get subscriptions from cache/database
            game_subscriptions = await self.cache_manager.get(f"game_subscriptions:{game_id}") or []
            return game_subscriptions
            
        except Exception as e:
            logger.error(f"Error finding users for game: {e}")
            return []
    
    async def _send_channel_alert(
        self,
        user_id: str,
        channel: NotificationChannel,
        value_bet: LiveValueBet,
        preferences: UserPreferences
    ) -> bool:
        """Send alert through specific channel.
        
        Args:
            user_id: User identifier
            channel: Notification channel
            value_bet: Value bet data
            preferences: User preferences
            
        Returns:
            True if sent successfully
        """
        try:
            template = self.templates[channel]
            user_data = {"user_id": user_id}
            alert_data = template.format_value_bet_alert(value_bet, user_data)
            
            # Check if alert should be sent
            if not preferences.should_send_alert(alert_data):
                return False
            
            # Deliver alert
            return await self._deliver_alert(user_id, channel, alert_data)
            
        except Exception as e:
            logger.error(f"Error sending channel alert: {e}")
            return False
    
    async def _deliver_alert(
        self,
        user_id: str,
        channel: NotificationChannel,
        alert_data: Dict[str, Any]
    ) -> bool:
        """Deliver alert through specific channel.
        
        Args:
            user_id: User identifier
            channel: Notification channel
            alert_data: Alert data
            
        Returns:
            True if delivered successfully
        """
        try:
            if channel == NotificationChannel.WEBSOCKET:
                return await self.delivery_service.send_websocket(user_id, alert_data)
            
            elif channel == NotificationChannel.EMAIL:
                user_email = self.user_contacts.get(user_id, {}).get("email")
                if user_email:
                    return await self.delivery_service.send_email(user_email, alert_data)
            
            elif channel == NotificationChannel.SMS:
                phone_number = self.user_contacts.get(user_id, {}).get("phone")
                if phone_number:
                    message = alert_data.get("message", "Alert")
                    return await self.delivery_service.send_sms(phone_number, message)
            
            elif channel == NotificationChannel.PUSH:
                device_token = self.user_contacts.get(user_id, {}).get("device_token")
                if device_token:
                    return await self.delivery_service.send_push(device_token, alert_data)
            
            return False
            
        except Exception as e:
            logger.error(f"Error delivering alert: {e}")
            return False
    
    async def _store_alert_history(self, alert_type: str, alert_data: Dict[str, Any]) -> None:
        """Store alert in history.
        
        Args:
            alert_type: Type of alert
            alert_data: Alert data
        """
        try:
            history_entry = {
                "type": alert_type,
                "data": alert_data,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Store in memory
            self.alert_history[alert_type].append(history_entry)
            
            # Store in cache
            await self.cache_manager.set(
                f"alert_history:{alert_type}:{datetime.utcnow().isoformat()}",
                history_entry,
                ttl=86400  # 24 hours
            )
            
        except Exception as e:
            logger.error(f"Error storing alert history: {e}")
    
    async def add_user_preferences(
        self,
        user_id: str,
        preferences: UserPreferences
    ) -> None:
        """Add or update user preferences.
        
        Args:
            user_id: User identifier
            preferences: User preferences
        """
        try:
            self.user_preferences[user_id] = preferences
            
            # Cache preferences
            await self.cache_manager.set(
                f"user_preferences:{user_id}",
                {
                    "channels": [c.value for c in preferences.channels],
                    "min_edge": preferences.min_edge,
                    "min_confidence": preferences.min_confidence,
                    "sports": preferences.sports,
                    "teams": preferences.teams,
                    "quiet_hours": preferences.quiet_hours,
                    "max_alerts_per_hour": preferences.max_alerts_per_hour,
                    "is_active": preferences.is_active
                },
                ttl=86400  # 24 hours
            )
            
            logger.info(f"Updated preferences for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error adding user preferences: {e}")
    
    async def add_user_contacts(
        self,
        user_id: str,
        contacts: Dict[str, str]
    ) -> None:
        """Add or update user contact information.
        
        Args:
            user_id: User identifier
            contacts: Contact information (email, phone, device_token, etc.)
        """
        try:
            self.user_contacts[user_id] = contacts
            
            # Cache contacts (without sensitive data in logs)
            await self.cache_manager.set(
                f"user_contacts:{user_id}",
                contacts,
                ttl=86400  # 24 hours
            )
            
            logger.info(f"Updated contacts for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error adding user contacts: {e}")
    
    def get_alert_stats(self) -> Dict[str, Any]:
        """Get alert statistics.
        
        Returns:
            Alert statistics
        """
        return {
            **self.alert_stats,
            "delivery_stats": self.delivery_service.get_delivery_stats(),
            "active_users": len(self.user_preferences),
            "uptime_minutes": (datetime.utcnow() - self.alert_stats["last_reset"]).total_seconds() / 60
        }
    
    async def cleanup_old_alerts(self, days: int = 7) -> int:
        """Clean up old alert history.
        
        Args:
            days: Number of days to keep
            
        Returns:
            Number of alerts cleaned up
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            cleaned_count = 0
            
            # Clean memory history
            for alert_type in self.alert_history:
                original_count = len(self.alert_history[alert_type])
                
                # Filter out old alerts
                self.alert_history[alert_type] = deque(
                    [alert for alert in self.alert_history[alert_type]
                     if datetime.fromisoformat(alert["timestamp"].replace('Z', '+00:00')) > cutoff_date],
                    maxlen=1000
                )
                
                cleaned_count += original_count - len(self.alert_history[alert_type])
            
            # Clean cache (would require pattern matching and deletion)
            # This is simplified for the demo
            
            if cleaned_count > 0:
                logger.info(f"Cleaned up {cleaned_count} old alerts")
            
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Error cleaning up old alerts: {e}")
            return 0