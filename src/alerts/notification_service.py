"""Multi-channel notification service for alerts."""
import logging
from typing import List, Dict, Any, Optional
import asyncio
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import httpx

from src.models.schemas import Alert, ValueBet, User
from src.alerts.websocket_manager import ConnectionManager
from src.config.settings import settings

logger = logging.getLogger(__name__)


class NotificationService:
    """Handles multi-channel alert notifications."""
    
    def __init__(
        self,
        connection_manager: Optional[ConnectionManager] = None
    ):
        """Initialize notification service.
        
        Args:
            connection_manager: WebSocket connection manager
        """
        self.connection_manager = connection_manager
        self._email_configured = self._check_email_config()
    
    def _check_email_config(self) -> bool:
        """Check if email is properly configured."""
        # Check for SMTP settings in environment
        return bool(getattr(settings, "smtp_host", None))
    
    async def send_alert(
        self,
        alert: Alert,
        user: User
    ) -> Dict[str, bool]:
        """Send alert through all configured channels.
        
        Args:
            alert: Alert to send
            user: User to receive alert
            
        Returns:
            Dictionary of channel -> success status
        """
        results = {}
        
        for channel in alert.notification_channels:
            try:
                if channel == "websocket":
                    success = await self._send_websocket_alert(alert, user)
                elif channel == "email":
                    success = await self._send_email_alert(alert, user)
                elif channel == "discord":
                    success = await self._send_discord_alert(alert, user)
                elif channel == "telegram":
                    success = await self._send_telegram_alert(alert, user)
                else:
                    logger.warning(f"Unknown notification channel: {channel}")
                    success = False
                
                results[channel] = success
                
            except Exception as e:
                logger.error(f"Error sending {channel} notification: {e}")
                results[channel] = False
        
        return results
    
    async def _send_websocket_alert(
        self,
        alert: Alert,
        user: User
    ) -> bool:
        """Send alert via WebSocket.
        
        Args:
            alert: Alert to send
            user: User to receive alert
            
        Returns:
            True if sent successfully
        """
        if not self.connection_manager:
            return False
        
        try:
            await self.connection_manager.send_alert(alert)
            return True
        except Exception as e:
            logger.error(f"WebSocket send error: {e}")
            return False
    
    async def _send_email_alert(
        self,
        alert: Alert,
        user: User
    ) -> bool:
        """Send alert via email.
        
        Args:
            alert: Alert to send
            user: User to receive alert
            
        Returns:
            True if sent successfully
        """
        if not self._email_configured:
            logger.warning("Email not configured")
            return False
        
        try:
            # Format email content
            subject = self._format_email_subject(alert)
            body = self._format_email_body(alert)
            
            # Create message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = getattr(settings, "smtp_from", "alerts@sportsbetting.com")
            msg["To"] = user.email
            
            # Add HTML content
            html_part = MIMEText(body, "html")
            msg.attach(html_part)
            
            # Send email
            with smtplib.SMTP(
                getattr(settings, "smtp_host", ""),
                getattr(settings, "smtp_port", 587)
            ) as server:
                if getattr(settings, "smtp_use_tls", True):
                    server.starttls()
                
                if getattr(settings, "smtp_username", None):
                    server.login(
                        getattr(settings, "smtp_username", ""),
                        getattr(settings, "smtp_password", "")
                    )
                
                server.send_message(msg)
            
            return True
            
        except Exception as e:
            logger.error(f"Email send error: {e}")
            return False
    
    def _format_email_subject(self, alert: Alert) -> str:
        """Format email subject for alert.
        
        Args:
            alert: Alert to format
            
        Returns:
            Email subject string
        """
        value_bet = alert.value_bet
        return (
            f"🎯 Value Bet Alert: {value_bet.market.home_team} vs "
            f"{value_bet.market.away_team} - {value_bet.edge:.1%} Edge"
        )
    
    def _format_email_body(self, alert: Alert) -> str:
        """Format email body for alert.
        
        Args:
            alert: Alert to format
            
        Returns:
            HTML email body
        """
        value_bet = alert.value_bet
        market = value_bet.market
        
        html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; color: #333;">
            <h2 style="color: #2c5282;">Value Bet Opportunity</h2>
            
            <div style="background-color: #f7fafc; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <h3>{market.home_team} vs {market.away_team}</h3>
                <p><strong>Sport:</strong> {market.sport.value}</p>
                <p><strong>Start Time:</strong> {market.commence_time.strftime('%Y-%m-%d %H:%M UTC')}</p>
                <p><strong>Market:</strong> {market.bet_type.value}</p>
            </div>
            
            <div style="background-color: #e6fffa; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <h3>Betting Details</h3>
                <p><strong>Best Odds:</strong> {market.best_odds.odds:.2f} @ {market.best_odds.bookmaker}</p>
                <p><strong>True Probability:</strong> {value_bet.true_probability:.1%}</p>
                <p><strong>Implied Probability:</strong> {value_bet.implied_probability:.1%}</p>
                <p><strong>Edge:</strong> 
                   <span style="color: #38a169; font-weight: bold;">{value_bet.edge:.1%}</span></p>
                <p><strong>Expected Value:</strong> {value_bet.expected_value:.1%}</p>
                <p><strong>Confidence Score:</strong> {value_bet.confidence_score:.1%}</p>
                <p><strong>Kelly Fraction:</strong> {value_bet.kelly_fraction:.1%}</p>
            </div>
            
            <div style="background-color: #fef5e7; padding: 15px; border-radius: 8px; margin: 20px 0;">
                <p><strong>⚠️ Remember:</strong> Only bet what you can afford to lose. 
                   This is not financial advice.</p>
            </div>
            
            <hr style="margin: 30px 0;">
            <p style="font-size: 12px; color: #718096;">
                You received this alert because you subscribed to value bet notifications.
                <br>
                To manage your preferences, visit your account settings.
            </p>
        </body>
        </html>
        """
        
        return html
    
    async def _send_discord_alert(
        self,
        alert: Alert,
        user: User
    ) -> bool:
        """Send alert via Discord webhook.
        
        Args:
            alert: Alert to send
            user: User to receive alert
            
        Returns:
            True if sent successfully
        """
        webhook_url = getattr(user, "discord_webhook", None)
        if not webhook_url:
            return False
        
        try:
            value_bet = alert.value_bet
            market = value_bet.market
            
            # Create Discord embed
            embed = {
                "title": f"💰 Value Bet: {market.home_team} vs {market.away_team}",
                "color": 0x00ff00,  # Green
                "fields": [
                    {
                        "name": "Sport",
                        "value": market.sport.value,
                        "inline": True
                    },
                    {
                        "name": "Start Time",
                        "value": market.commence_time.strftime('%Y-%m-%d %H:%M UTC'),
                        "inline": True
                    },
                    {
                        "name": "Best Odds",
                        "value": f"{market.best_odds.odds:.2f} @ {market.best_odds.bookmaker}",
                        "inline": True
                    },
                    {
                        "name": "Edge",
                        "value": f"{value_bet.edge:.1%}",
                        "inline": True
                    },
                    {
                        "name": "Expected Value",
                        "value": f"{value_bet.expected_value:.1%}",
                        "inline": True
                    },
                    {
                        "name": "Confidence",
                        "value": f"{value_bet.confidence_score:.1%}",
                        "inline": True
                    }
                ],
                "timestamp": alert.created_at.isoformat()
            }
            
            payload = {
                "embeds": [embed],
                "username": "Sports Betting Bot"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(webhook_url, json=payload)
                return response.status_code == 204
                
        except Exception as e:
            logger.error(f"Discord send error: {e}")
            return False
    
    async def _send_telegram_alert(
        self,
        alert: Alert,
        user: User
    ) -> bool:
        """Send alert via Telegram bot.
        
        Args:
            alert: Alert to send
            user: User to receive alert
            
        Returns:
            True if sent successfully
        """
        telegram_chat_id = getattr(user, "telegram_chat_id", None)
        bot_token = getattr(settings, "telegram_bot_token", None)
        
        if not telegram_chat_id or not bot_token:
            return False
        
        try:
            value_bet = alert.value_bet
            market = value_bet.market
            
            # Format Telegram message
            message = (
                f"🎯 *Value Bet Alert*\n\n"
                f"*{market.home_team} vs {market.away_team}*\n"
                f"Sport: {market.sport.value}\n"
                f"Start: {market.commence_time.strftime('%Y-%m-%d %H:%M UTC')}\n\n"
                f"📊 *Betting Details*\n"
                f"Best Odds: {market.best_odds.odds:.2f} @ {market.best_odds.bookmaker}\n"
                f"Edge: *{value_bet.edge:.1%}*\n"
                f"EV: {value_bet.expected_value:.1%}\n"
                f"Confidence: {value_bet.confidence_score:.1%}\n"
                f"Kelly: {value_bet.kelly_fraction:.1%}\n\n"
                f"⚠️ _Bet responsibly_"
            )
            
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            payload = {
                "chat_id": telegram_chat_id,
                "text": message,
                "parse_mode": "Markdown"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload)
                return response.status_code == 200
                
        except Exception as e:
            logger.error(f"Telegram send error: {e}")
            return False
    
    async def send_batch_alerts(
        self,
        alerts: List[Alert],
        users: Dict[str, User]
    ) -> Dict[str, Dict[str, bool]]:
        """Send multiple alerts efficiently.
        
        Args:
            alerts: List of alerts to send
            users: Dictionary of user_id -> User
            
        Returns:
            Dictionary of alert_id -> channel -> success
        """
        tasks = []
        
        for alert in alerts:
            user = users.get(alert.user_id)
            if user:
                task = self.send_alert(alert, user)
                tasks.append((alert.id, task))
        
        results = {}
        for alert_id, task in tasks:
            channel_results = await task
            results[alert_id] = channel_results
        
        return results