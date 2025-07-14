"""WebSocket connection manager for real-time alerts."""
import logging
from typing import Dict, Set, Optional, Any
import asyncio
from fastapi import WebSocket, WebSocketDisconnect
import json

from src.alerts.redis_pubsub import RedisPubSubManager
from src.models.schemas import User, Alert

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections and message routing."""
    
    def __init__(self, redis_pubsub: RedisPubSubManager):
        """Initialize connection manager.
        
        Args:
            redis_pubsub: Redis pub/sub manager for cross-server support
        """
        self.redis_pubsub = redis_pubsub
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_channels: Dict[str, Set[str]] = {}
        self._background_tasks: Set[asyncio.Task] = set()
    
    async def connect(
        self,
        websocket: WebSocket,
        user_id: str
    ) -> None:
        """Accept WebSocket connection and setup user channels.
        
        Args:
            websocket: WebSocket connection
            user_id: User identifier
        """
        await websocket.accept()
        self.active_connections[user_id] = websocket
        
        # Subscribe to user's alert channel
        user_channel = f"alerts:{user_id}"
        await self.redis_pubsub.subscribe(
            user_channel,
            lambda msg: asyncio.create_task(
                self._send_to_user(user_id, msg)
            )
        )
        
        # Subscribe to system broadcast channel
        await self.redis_pubsub.subscribe(
            "system:broadcast",
            lambda msg: asyncio.create_task(
                self._send_to_user(user_id, msg)
            )
        )
        
        # Track subscribed channels
        if user_id not in self.user_channels:
            self.user_channels[user_id] = set()
        self.user_channels[user_id].add(user_channel)
        self.user_channels[user_id].add("system:broadcast")
        
        logger.info(f"WebSocket connected for user {user_id}")
        
        # Send welcome message
        await self.send_personal_message(
            user_id,
            {
                "type": "connection",
                "status": "connected",
                "message": "Connected to real-time alerts"
            }
        )
    
    async def disconnect(self, user_id: str) -> None:
        """Disconnect WebSocket and cleanup subscriptions.
        
        Args:
            user_id: User identifier
        """
        # Remove connection
        websocket = self.active_connections.pop(user_id, None)
        
        # Unsubscribe from channels
        if user_id in self.user_channels:
            for channel in self.user_channels[user_id]:
                await self.redis_pubsub.unsubscribe(channel)
            del self.user_channels[user_id]
        
        # Cancel any background tasks for this user
        tasks_to_cancel = [
            task for task in self._background_tasks
            if task.get_name() == f"user_task_{user_id}"
        ]
        for task in tasks_to_cancel:
            task.cancel()
            self._background_tasks.discard(task)
        
        logger.info(f"WebSocket disconnected for user {user_id}")
    
    async def send_personal_message(
        self,
        user_id: str,
        message: Dict[str, Any]
    ) -> None:
        """Send message directly to a user's WebSocket.
        
        Args:
            user_id: User identifier
            message: Message dictionary to send
        """
        websocket = self.active_connections.get(user_id)
        if websocket:
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Error sending to user {user_id}: {e}")
                await self.disconnect(user_id)
    
    async def _send_to_user(
        self,
        user_id: str,
        message: Dict[str, Any]
    ) -> None:
        """Internal method to send Redis message to user.
        
        Args:
            user_id: User identifier
            message: Message from Redis pub/sub
        """
        await self.send_personal_message(user_id, message)
    
    async def broadcast(self, message: Dict[str, Any]) -> None:
        """Broadcast message to all connected users.
        
        Args:
            message: Message to broadcast
        """
        # Use Redis pub/sub for cross-server broadcast
        await self.redis_pubsub.publish("system:broadcast", message)
    
    async def send_to_group(
        self,
        group_id: str,
        message: Dict[str, Any]
    ) -> None:
        """Send message to a group of users.
        
        Args:
            group_id: Group identifier (e.g., sport type)
            message: Message to send
        """
        # Publish to group channel
        channel = f"group:{group_id}"
        await self.redis_pubsub.publish(channel, message)
    
    async def subscribe_to_sport(
        self,
        user_id: str,
        sport: str
    ) -> None:
        """Subscribe user to sport-specific updates.
        
        Args:
            user_id: User identifier
            sport: Sport to subscribe to
        """
        channel = f"market:{sport}"
        
        # Subscribe to channel if not already
        if channel not in self.user_channels.get(user_id, set()):
            await self.redis_pubsub.subscribe(
                channel,
                lambda msg: asyncio.create_task(
                    self._send_to_user(user_id, msg)
                )
            )
            self.user_channels[user_id].add(channel)
            
            logger.info(f"User {user_id} subscribed to {sport}")
    
    async def unsubscribe_from_sport(
        self,
        user_id: str,
        sport: str
    ) -> None:
        """Unsubscribe user from sport-specific updates.
        
        Args:
            user_id: User identifier
            sport: Sport to unsubscribe from
        """
        channel = f"market:{sport}"
        
        if channel in self.user_channels.get(user_id, set()):
            await self.redis_pubsub.unsubscribe(channel)
            self.user_channels[user_id].discard(channel)
            
            logger.info(f"User {user_id} unsubscribed from {sport}")
    
    async def handle_websocket(
        self,
        websocket: WebSocket,
        user_id: str
    ) -> None:
        """Handle WebSocket connection lifecycle.
        
        Args:
            websocket: WebSocket connection
            user_id: User identifier
        """
        await self.connect(websocket, user_id)
        
        try:
            while True:
                # Receive and handle messages from client
                data = await websocket.receive_json()
                await self._handle_client_message(user_id, data)
                
        except WebSocketDisconnect:
            logger.info(f"Client {user_id} disconnected")
        except Exception as e:
            logger.error(f"WebSocket error for {user_id}: {e}")
        finally:
            await self.disconnect(user_id)
    
    async def _handle_client_message(
        self,
        user_id: str,
        data: Dict[str, Any]
    ) -> None:
        """Handle message received from client.
        
        Args:
            user_id: User identifier
            data: Message data from client
        """
        message_type = data.get("type")
        
        if message_type == "subscribe":
            # Subscribe to specific channels
            channel_type = data.get("channel_type")
            channel_id = data.get("channel_id")
            
            if channel_type == "sport":
                await self.subscribe_to_sport(user_id, channel_id)
            
            # Send confirmation
            await self.send_personal_message(
                user_id,
                {
                    "type": "subscription_confirmed",
                    "channel_type": channel_type,
                    "channel_id": channel_id
                }
            )
        
        elif message_type == "unsubscribe":
            # Unsubscribe from channels
            channel_type = data.get("channel_type")
            channel_id = data.get("channel_id")
            
            if channel_type == "sport":
                await self.unsubscribe_from_sport(user_id, channel_id)
            
            # Send confirmation
            await self.send_personal_message(
                user_id,
                {
                    "type": "unsubscription_confirmed",
                    "channel_type": channel_type,
                    "channel_id": channel_id
                }
            )
        
        elif message_type == "ping":
            # Respond to ping
            await self.send_personal_message(
                user_id,
                {"type": "pong", "timestamp": data.get("timestamp")}
            )
        
        else:
            logger.warning(f"Unknown message type from {user_id}: {message_type}")
    
    def get_connection_count(self) -> int:
        """Get number of active connections.
        
        Returns:
            Number of active WebSocket connections
        """
        return len(self.active_connections)
    
    def get_user_connections(self) -> Set[str]:
        """Get set of connected user IDs.
        
        Returns:
            Set of user IDs with active connections
        """
        return set(self.active_connections.keys())
    
    async def send_alert(
        self,
        alert: Alert
    ) -> None:
        """Send alert to user through appropriate channels.
        
        Args:
            alert: Alert object to send
        """
        # Determine channels based on notification preferences
        for channel in alert.notification_channels:
            if channel == "websocket":
                # Send via WebSocket
                await self.send_personal_message(
                    alert.user_id,
                    {
                        "type": "alert",
                        "alert": alert.model_dump()
                    }
                )
            
            # Other channels (email, SMS) would be handled elsewhere