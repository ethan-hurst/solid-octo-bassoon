"""WebSocket infrastructure for real-time live betting updates."""
import asyncio
import json
import logging
from typing import Dict, List, Set, Optional, Any, Callable
from datetime import datetime, timedelta
from collections import defaultdict
import weakref

import websockets
from websockets.server import WebSocketServerProtocol
from websockets.exceptions import ConnectionClosed, WebSocketException

from src.models.live_schemas import (
    LiveWebSocketMessage, LiveOdds, LiveEvent, LiveValueBet, 
    LivePrediction, LiveSubscription, OddsUpdate, GameEvent,
    PredictionUpdate
)
from src.data_collection.cache_manager import CacheManager

logger = logging.getLogger(__name__)


class WebSocketConnection:
    """Wrapper for WebSocket connection with metadata."""
    
    def __init__(
        self, 
        websocket: WebSocketServerProtocol, 
        user_id: Optional[str] = None,
        connection_id: Optional[str] = None
    ):
        self.websocket = websocket
        self.user_id = user_id
        self.connection_id = connection_id or f"conn_{id(websocket)}"
        self.subscriptions: Set[str] = set()
        self.connected_at = datetime.utcnow()
        self.last_ping = datetime.utcnow()
        self.is_authenticated = user_id is not None
        
    async def send_message(self, message: Dict[str, Any]) -> bool:
        """Send message to websocket connection."""
        try:
            await self.websocket.send(json.dumps(message, default=str))
            return True
        except (ConnectionClosed, WebSocketException) as e:
            logger.debug(f"Connection {self.connection_id} closed: {e}")
            return False
        except Exception as e:
            logger.error(f"Error sending message to {self.connection_id}: {e}")
            return False
    
    async def send_live_message(self, ws_message: LiveWebSocketMessage) -> bool:
        """Send structured live betting message."""
        try:
            message_dict = {
                "type": ws_message.message_type,
                "game_id": ws_message.game_id,
                "timestamp": ws_message.timestamp.isoformat(),
                "data": ws_message.data.model_dump() if hasattr(ws_message.data, 'model_dump') else ws_message.data
            }
            return await self.send_message(message_dict)
        except Exception as e:
            logger.error(f"Error sending live message: {e}")
            return False
    
    def add_subscription(self, subscription_key: str) -> None:
        """Add subscription to this connection."""
        self.subscriptions.add(subscription_key)
        
    def remove_subscription(self, subscription_key: str) -> None:
        """Remove subscription from this connection."""
        self.subscriptions.discard(subscription_key)
        
    def is_subscribed_to(self, subscription_key: str) -> bool:
        """Check if connection is subscribed to a key."""
        return subscription_key in self.subscriptions
    
    @property
    def is_alive(self) -> bool:
        """Check if connection is still alive."""
        return not self.websocket.closed


class SubscriptionManager:
    """Manage user subscriptions to live betting updates."""
    
    def __init__(self):
        self.subscriptions: Dict[str, List[WebSocketConnection]] = defaultdict(list)
        self.user_subscriptions: Dict[str, List[str]] = defaultdict(list)
        
    def add_subscription(
        self, 
        connection: WebSocketConnection, 
        subscription_key: str
    ) -> None:
        """Add a subscription for a connection."""
        try:
            # Add to connection
            connection.add_subscription(subscription_key)
            
            # Add to subscription registry
            if connection not in self.subscriptions[subscription_key]:
                self.subscriptions[subscription_key].append(connection)
            
            # Track user subscriptions
            if connection.user_id:
                if subscription_key not in self.user_subscriptions[connection.user_id]:
                    self.user_subscriptions[connection.user_id].append(subscription_key)
            
            logger.debug(f"Added subscription {subscription_key} for {connection.connection_id}")
            
        except Exception as e:
            logger.error(f"Error adding subscription: {e}")
    
    def remove_subscription(
        self, 
        connection: WebSocketConnection, 
        subscription_key: str
    ) -> None:
        """Remove a subscription for a connection."""
        try:
            # Remove from connection
            connection.remove_subscription(subscription_key)
            
            # Remove from subscription registry
            if connection in self.subscriptions[subscription_key]:
                self.subscriptions[subscription_key].remove(connection)
            
            # Clean up empty subscription lists
            if not self.subscriptions[subscription_key]:
                del self.subscriptions[subscription_key]
            
            # Update user subscriptions
            if connection.user_id:
                if subscription_key in self.user_subscriptions[connection.user_id]:
                    self.user_subscriptions[connection.user_id].remove(subscription_key)
            
            logger.debug(f"Removed subscription {subscription_key} for {connection.connection_id}")
            
        except Exception as e:
            logger.error(f"Error removing subscription: {e}")
    
    def get_subscribers(self, subscription_key: str) -> List[WebSocketConnection]:
        """Get all connections subscribed to a key."""
        return [conn for conn in self.subscriptions.get(subscription_key, []) if conn.is_alive]
    
    def cleanup_dead_connections(self) -> int:
        """Remove dead connections from all subscriptions."""
        cleaned_count = 0
        
        for subscription_key in list(self.subscriptions.keys()):
            original_count = len(self.subscriptions[subscription_key])
            self.subscriptions[subscription_key] = [
                conn for conn in self.subscriptions[subscription_key] if conn.is_alive
            ]
            cleaned_count += original_count - len(self.subscriptions[subscription_key])
            
            # Remove empty subscriptions
            if not self.subscriptions[subscription_key]:
                del self.subscriptions[subscription_key]
        
        if cleaned_count > 0:
            logger.info(f"Cleaned up {cleaned_count} dead connections")
        
        return cleaned_count
    
    def get_subscription_stats(self) -> Dict[str, Any]:
        """Get subscription statistics."""
        total_subscriptions = len(self.subscriptions)
        total_connections = sum(len(conns) for conns in self.subscriptions.values())
        active_connections = sum(
            len([c for c in conns if c.is_alive]) 
            for conns in self.subscriptions.values()
        )
        
        return {
            "total_subscription_keys": total_subscriptions,
            "total_connections": total_connections,
            "active_connections": active_connections,
            "unique_users": len(self.user_subscriptions)
        }


class LiveBettingWebSocketManager:
    """Main WebSocket manager for live betting updates."""
    
    def __init__(self, cache_manager: CacheManager):
        self.cache_manager = cache_manager
        self.subscription_manager = SubscriptionManager()
        self.connections: Dict[str, WebSocketConnection] = {}
        self.server = None
        self.is_running = False
        
        # Rate limiting
        self.rate_limits: Dict[str, List[datetime]] = defaultdict(list)
        self.max_messages_per_minute = 60
        
        # Message handlers
        self.message_handlers: Dict[str, Callable] = {
            "subscribe": self._handle_subscribe,
            "unsubscribe": self._handle_unsubscribe,
            "ping": self._handle_ping,
            "authenticate": self._handle_authenticate
        }
        
    async def start_server(self, host: str = "localhost", port: int = 8765) -> None:
        """Start the WebSocket server."""
        try:
            self.server = await websockets.serve(
                self._handle_connection,
                host,
                port,
                ping_interval=30,
                ping_timeout=10,
                close_timeout=10
            )
            
            self.is_running = True
            
            # Start background cleanup task
            asyncio.create_task(self._cleanup_task())
            
            logger.info(f"Live betting WebSocket server started on {host}:{port}")
            
        except Exception as e:
            logger.error(f"Error starting WebSocket server: {e}")
            raise
    
    async def stop_server(self) -> None:
        """Stop the WebSocket server."""
        try:
            self.is_running = False
            
            if self.server:
                self.server.close()
                await self.server.wait_closed()
            
            # Close all connections
            for connection in list(self.connections.values()):
                await self._disconnect_client(connection)
            
            logger.info("Live betting WebSocket server stopped")
            
        except Exception as e:
            logger.error(f"Error stopping WebSocket server: {e}")
    
    async def _handle_connection(self, websocket: WebSocketServerProtocol, path: str) -> None:
        """Handle new WebSocket connection."""
        connection = WebSocketConnection(websocket)
        self.connections[connection.connection_id] = connection
        
        logger.info(f"New WebSocket connection: {connection.connection_id}")
        
        try:
            # Send welcome message
            await connection.send_message({
                "type": "welcome",
                "connection_id": connection.connection_id,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # Handle messages
            async for message in websocket:
                if not self.is_running:
                    break
                    
                try:
                    data = json.loads(message)
                    await self._process_message(connection, data)
                except json.JSONDecodeError:
                    await connection.send_message({
                        "type": "error",
                        "message": "Invalid JSON format"
                    })
                except Exception as e:
                    logger.error(f"Error processing message from {connection.connection_id}: {e}")
                    await connection.send_message({
                        "type": "error",
                        "message": "Internal server error"
                    })
                    
        except ConnectionClosed:
            logger.debug(f"Connection {connection.connection_id} closed normally")
        except Exception as e:
            logger.error(f"Connection {connection.connection_id} error: {e}")
        finally:
            await self._disconnect_client(connection)
    
    async def _process_message(self, connection: WebSocketConnection, data: Dict[str, Any]) -> None:
        """Process incoming WebSocket message."""
        try:
            # Rate limiting check
            if not self._check_rate_limit(connection.connection_id):
                await connection.send_message({
                    "type": "error",
                    "message": "Rate limit exceeded"
                })
                return
            
            message_type = data.get("type")
            if not message_type:
                await connection.send_message({
                    "type": "error",
                    "message": "Message type required"
                })
                return
            
            # Handle message
            handler = self.message_handlers.get(message_type)
            if handler:
                await handler(connection, data)
            else:
                await connection.send_message({
                    "type": "error",
                    "message": f"Unknown message type: {message_type}"
                })
                
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            await connection.send_message({
                "type": "error",
                "message": "Failed to process message"
            })
    
    async def _handle_subscribe(self, connection: WebSocketConnection, data: Dict[str, Any]) -> None:
        """Handle subscription request."""
        try:
            subscription_type = data.get("subscription_type")
            target = data.get("target")
            
            if not subscription_type or not target:
                await connection.send_message({
                    "type": "error",
                    "message": "subscription_type and target required"
                })
                return
            
            # Create subscription key
            subscription_key = f"{subscription_type}:{target}"
            
            # Add subscription
            self.subscription_manager.add_subscription(connection, subscription_key)
            
            await connection.send_message({
                "type": "subscribed",
                "subscription_type": subscription_type,
                "target": target,
                "subscription_key": subscription_key
            })
            
            logger.info(f"Connection {connection.connection_id} subscribed to {subscription_key}")
            
        except Exception as e:
            logger.error(f"Error handling subscribe: {e}")
            await connection.send_message({
                "type": "error",
                "message": "Failed to process subscription"
            })
    
    async def _handle_unsubscribe(self, connection: WebSocketConnection, data: Dict[str, Any]) -> None:
        """Handle unsubscription request."""
        try:
            subscription_type = data.get("subscription_type")
            target = data.get("target")
            
            if not subscription_type or not target:
                await connection.send_message({
                    "type": "error",
                    "message": "subscription_type and target required"
                })
                return
            
            # Create subscription key
            subscription_key = f"{subscription_type}:{target}"
            
            # Remove subscription
            self.subscription_manager.remove_subscription(connection, subscription_key)
            
            await connection.send_message({
                "type": "unsubscribed",
                "subscription_type": subscription_type,
                "target": target,
                "subscription_key": subscription_key
            })
            
            logger.info(f"Connection {connection.connection_id} unsubscribed from {subscription_key}")
            
        except Exception as e:
            logger.error(f"Error handling unsubscribe: {e}")
            await connection.send_message({
                "type": "error",
                "message": "Failed to process unsubscription"
            })
    
    async def _handle_ping(self, connection: WebSocketConnection, data: Dict[str, Any]) -> None:
        """Handle ping request."""
        connection.last_ping = datetime.utcnow()
        await connection.send_message({
            "type": "pong",
            "timestamp": datetime.utcnow().isoformat()
        })
    
    async def _handle_authenticate(self, connection: WebSocketConnection, data: Dict[str, Any]) -> None:
        """Handle authentication request."""
        try:
            user_id = data.get("user_id")
            token = data.get("token")
            
            if not user_id or not token:
                await connection.send_message({
                    "type": "auth_error",
                    "message": "user_id and token required"
                })
                return
            
            # In production, validate token against auth service
            # For now, accept any valid format
            if len(token) >= 10:
                connection.user_id = user_id
                connection.is_authenticated = True
                
                await connection.send_message({
                    "type": "authenticated",
                    "user_id": user_id
                })
                
                logger.info(f"Connection {connection.connection_id} authenticated as {user_id}")
            else:
                await connection.send_message({
                    "type": "auth_error",
                    "message": "Invalid token"
                })
                
        except Exception as e:
            logger.error(f"Error handling authentication: {e}")
            await connection.send_message({
                "type": "auth_error",
                "message": "Authentication failed"
            })
    
    def _check_rate_limit(self, connection_id: str) -> bool:
        """Check if connection is within rate limits."""
        now = datetime.utcnow()
        cutoff = now - timedelta(minutes=1)
        
        # Clean old messages
        self.rate_limits[connection_id] = [
            msg_time for msg_time in self.rate_limits[connection_id]
            if msg_time > cutoff
        ]
        
        # Check limit
        if len(self.rate_limits[connection_id]) >= self.max_messages_per_minute:
            return False
        
        # Add current message
        self.rate_limits[connection_id].append(now)
        return True
    
    async def _disconnect_client(self, connection: WebSocketConnection) -> None:
        """Clean disconnect for a client."""
        try:
            # Remove from connections
            if connection.connection_id in self.connections:
                del self.connections[connection.connection_id]
            
            # Remove all subscriptions
            for subscription_key in list(connection.subscriptions):
                self.subscription_manager.remove_subscription(connection, subscription_key)
            
            # Clean rate limits
            if connection.connection_id in self.rate_limits:
                del self.rate_limits[connection.connection_id]
            
            logger.debug(f"Disconnected client {connection.connection_id}")
            
        except Exception as e:
            logger.error(f"Error disconnecting client: {e}")
    
    async def _cleanup_task(self) -> None:
        """Background task for cleanup operations."""
        while self.is_running:
            try:
                await asyncio.sleep(60)  # Run every minute
                
                # Cleanup dead connections
                self.subscription_manager.cleanup_dead_connections()
                
                # Clean old rate limit data
                cutoff = datetime.utcnow() - timedelta(minutes=5)
                for conn_id in list(self.rate_limits.keys()):
                    self.rate_limits[conn_id] = [
                        msg_time for msg_time in self.rate_limits[conn_id]
                        if msg_time > cutoff
                    ]
                    
                    if not self.rate_limits[conn_id]:
                        del self.rate_limits[conn_id]
                
                # Log stats
                stats = self.subscription_manager.get_subscription_stats()
                logger.debug(f"WebSocket stats: {stats}")
                
            except Exception as e:
                logger.error(f"Error in cleanup task: {e}")
    
    # Public broadcast methods
    
    async def broadcast_odds_update(self, odds: LiveOdds) -> int:
        """Broadcast odds update to subscribed clients."""
        try:
            # Create WebSocket message
            odds_update = OddsUpdate(
                bookmaker=odds.bookmaker,
                bet_type=odds.bet_type.value,
                old_odds=0.0,  # Would need to track previous odds
                new_odds=odds.odds,
                line_movement=0.0,
                significance=0.1
            )
            
            ws_message = LiveWebSocketMessage(
                message_type="odds_update",
                game_id=odds.game_id,
                data=odds_update
            )
            
            # Get subscribers
            subscription_keys = [
                f"game:{odds.game_id}",
                f"odds:{odds.game_id}",
                f"bookmaker:{odds.bookmaker}"
            ]
            
            sent_count = 0
            for subscription_key in subscription_keys:
                subscribers = self.subscription_manager.get_subscribers(subscription_key)
                for connection in subscribers:
                    if await connection.send_live_message(ws_message):
                        sent_count += 1
            
            logger.debug(f"Broadcasted odds update to {sent_count} clients")
            return sent_count
            
        except Exception as e:
            logger.error(f"Error broadcasting odds update: {e}")
            return 0
    
    async def broadcast_game_event(self, event: LiveEvent) -> int:
        """Broadcast game event to subscribed clients."""
        try:
            # Create WebSocket message
            game_event = GameEvent(
                event_type=event.event_type.value,
                description=event.description,
                impact_score=event.impact_score,
                probability_change=event.probability_change
            )
            
            ws_message = LiveWebSocketMessage(
                message_type="game_event",
                game_id=event.game_id,
                data=game_event
            )
            
            # Get subscribers
            subscription_keys = [
                f"game:{event.game_id}",
                f"events:{event.game_id}"
            ]
            
            sent_count = 0
            for subscription_key in subscription_keys:
                subscribers = self.subscription_manager.get_subscribers(subscription_key)
                for connection in subscribers:
                    if await connection.send_live_message(ws_message):
                        sent_count += 1
            
            logger.debug(f"Broadcasted game event to {sent_count} clients")
            return sent_count
            
        except Exception as e:
            logger.error(f"Error broadcasting game event: {e}")
            return 0
    
    async def broadcast_value_bet(self, value_bet: LiveValueBet) -> int:
        """Broadcast value bet alert to subscribed clients."""
        try:
            ws_message = LiveWebSocketMessage(
                message_type="value_bet",
                game_id=value_bet.game_id,
                data=value_bet
            )
            
            # Get subscribers
            subscription_keys = [
                f"game:{value_bet.game_id}",
                f"value_bets:{value_bet.game_id}",
                "value_bets:all"
            ]
            
            sent_count = 0
            for subscription_key in subscription_keys:
                subscribers = self.subscription_manager.get_subscribers(subscription_key)
                for connection in subscribers:
                    if await connection.send_live_message(ws_message):
                        sent_count += 1
            
            logger.info(f"Broadcasted value bet alert to {sent_count} clients")
            return sent_count
            
        except Exception as e:
            logger.error(f"Error broadcasting value bet: {e}")
            return 0
    
    async def broadcast_prediction_update(self, prediction: LivePrediction) -> int:
        """Broadcast prediction update to subscribed clients."""
        try:
            # Create WebSocket message
            prediction_update = PredictionUpdate(
                model_version=prediction.model_version,
                home_win_probability=prediction.home_win_probability,
                away_win_probability=prediction.away_win_probability,
                confidence_score=prediction.confidence_score
            )
            
            ws_message = LiveWebSocketMessage(
                message_type="prediction_update",
                game_id=prediction.game_id,
                data=prediction_update
            )
            
            # Get subscribers
            subscription_keys = [
                f"game:{prediction.game_id}",
                f"predictions:{prediction.game_id}"
            ]
            
            sent_count = 0
            for subscription_key in subscription_keys:
                subscribers = self.subscription_manager.get_subscribers(subscription_key)
                for connection in subscribers:
                    if await connection.send_live_message(ws_message):
                        sent_count += 1
            
            logger.debug(f"Broadcasted prediction update to {sent_count} clients")
            return sent_count
            
        except Exception as e:
            logger.error(f"Error broadcasting prediction update: {e}")
            return 0
    
    async def send_user_alert(self, user_id: str, alert_data: Dict[str, Any]) -> bool:
        """Send alert to specific user."""
        try:
            # Find user connections
            user_connections = [
                conn for conn in self.connections.values()
                if conn.user_id == user_id and conn.is_authenticated
            ]
            
            if not user_connections:
                logger.warning(f"No active connections found for user {user_id}")
                return False
            
            message = {
                "type": "user_alert",
                "timestamp": datetime.utcnow().isoformat(),
                "data": alert_data
            }
            
            sent_count = 0
            for connection in user_connections:
                if await connection.send_message(message):
                    sent_count += 1
            
            logger.info(f"Sent alert to {sent_count} connections for user {user_id}")
            return sent_count > 0
            
        except Exception as e:
            logger.error(f"Error sending user alert: {e}")
            return False
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get connection statistics."""
        total_connections = len(self.connections)
        authenticated_connections = sum(1 for c in self.connections.values() if c.is_authenticated)
        active_connections = sum(1 for c in self.connections.values() if c.is_alive)
        
        subscription_stats = self.subscription_manager.get_subscription_stats()
        
        return {
            "total_connections": total_connections,
            "authenticated_connections": authenticated_connections,
            "active_connections": active_connections,
            "subscription_stats": subscription_stats,
            "server_running": self.is_running
        }