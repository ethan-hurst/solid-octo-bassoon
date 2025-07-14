"""Applying changes to gracefully disconnect from Redis pub/sub."""
"""Redis pub/sub manager for real-time alerts."""
import json
import logging
from typing import Dict, Any, Optional, Set, Callable
import asyncio
import redis.asyncio as redis

from src.config.settings import settings

logger = logging.getLogger(__name__)


class RedisPubSubManager:
    """Manages Redis pub/sub for WebSocket communications."""

    def __init__(self, redis_url: Optional[str] = None):
        """Initialize Redis pub/sub manager.

        Args:
            redis_url: Redis connection URL
        """
        self.redis_url = redis_url or settings.redis_url
        self._redis: Optional[redis.Redis] = None
        self._pubsub: Optional[redis.client.PubSub] = None
        self._channels: Set[str] = set()
        self._handlers: Dict[str, Callable] = {}
        self._listener_task: Optional[asyncio.Task] = None
        self._running = False

    async def connect(self) -> None:
        """Establish Redis connection and create pub/sub client."""
        if not self._redis:
            self._redis = await redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            self._pubsub = self._redis.pubsub()
            logger.info("Connected to Redis pub/sub")

    async def disconnect(self) -> None:
        """Disconnect from Redis pub/sub."""
        try:
            if self._pubsub:
                await self._pubsub.unsubscribe()
                await self._pubsub.aclose()
        except Exception as e:
            logger.warning(f"Error disconnecting from Redis pub/sub: {e}")

        try:
            if self._redis:
                await self._redis.aclose()
        except Exception as e:
            logger.warning(f"Error closing Redis connection: {e}")

        logger.info("Disconnected from Redis pub/sub")

    async def subscribe(
        self,
        channel: str,
        handler: Optional[Callable[[Dict[str, Any]], Any]] = None
    ) -> None:
        """Subscribe to a channel.

        Args:
            channel: Channel name to subscribe to
            handler: Optional message handler for this channel
        """
        if not self._pubsub:
            await self.connect()

        await self._pubsub.subscribe(channel)
        self._channels.add(channel)

        if handler:
            self._handlers[channel] = handler

        logger.info(f"Subscribed to channel: {channel}")

        # Start listener if not running
        if not self._listener_task or self._listener_task.done():
            self._listener_task = asyncio.create_task(self._listen())

    async def unsubscribe(self, channel: str) -> None:
        """Unsubscribe from a channel.

        Args:
            channel: Channel name to unsubscribe from
        """
        if self._pubsub and channel in self._channels:
            await self._pubsub.unsubscribe(channel)
            self._channels.discard(channel)
            self._handlers.pop(channel, None)
            logger.info(f"Unsubscribed from channel: {channel}")

    async def publish(
        self,
        channel: str,
        message: Dict[str, Any]
    ) -> int:
        """Publish message to a channel.

        Args:
            channel: Channel name to publish to
            message: Message dictionary to publish

        Returns:
            Number of subscribers that received the message
        """
        if not self._redis:
            await self.connect()

        try:
            json_message = json.dumps(message, default=str)
            subscribers = await self._redis.publish(channel, json_message)
            logger.debug(f"Published to {channel}, {subscribers} subscribers")
            return subscribers
        except Exception as e:
            logger.error(f"Publish error to {channel}: {e}")
            return 0

    async def _listen(self) -> None:
        """Listen for messages on subscribed channels."""
        self._running = True
        logger.info("Started Redis pub/sub listener")

        try:
            while self._running:
                try:
                    # Use get_message with timeout to allow cancellation
                    message = await self._pubsub.get_message(
                        ignore_subscribe_messages=True,
                        timeout=1.0
                    )

                    if message and message["type"] == "message":
                        await self._handle_message(message)

                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Listener error: {e}")
                    await asyncio.sleep(1)  # Brief pause before retry

        finally:
            self._running = False
            logger.info("Stopped Redis pub/sub listener")

    async def _handle_message(self, message: Dict[str, Any]) -> None:
        """Handle incoming pub/sub message.

        Args:
            message: Redis message dictionary
        """
        channel = message.get("channel", "")
        data = message.get("data", "")

        try:
            # Parse JSON data
            parsed_data = json.loads(data) if isinstance(data, str) else data

            # Call channel-specific handler if exists
            handler = self._handlers.get(channel)
            if handler:
                await handler(parsed_data)
            else:
                # Default handling - could emit to WebSocket
                logger.debug(f"Message on {channel}: {parsed_data}")

        except json.JSONDecodeError:
            logger.error(f"Invalid JSON in message from {channel}: {data}")
        except Exception as e:
            logger.error(f"Error handling message from {channel}: {e}")

    async def pattern_subscribe(
        self,
        pattern: str,
        handler: Optional[Callable[[Dict[str, Any]], Any]] = None
    ) -> None:
        """Subscribe to channels matching a pattern.

        Args:
            pattern: Channel pattern (e.g., "alerts:*")
            handler: Optional message handler for matching channels
        """
        if not self._pubsub:
            await self.connect()

        await self._pubsub.psubscribe(pattern)

        if handler:
            self._handlers[pattern] = handler

        logger.info(f"Pattern subscribed: {pattern}")

        # Start listener if not running
        if not self._listener_task or self._listener_task.done():
            self._listener_task = asyncio.create_task(self._listen())


class AlertPublisher:
    """Publishes alerts to Redis channels."""

    def __init__(self, pubsub_manager: RedisPubSubManager):
        """Initialize alert publisher.

        Args:
            pubsub_manager: Redis pub/sub manager instance
        """
        self.pubsub = pubsub_manager

    async def publish_value_bet_alert(
        self,
        user_id: str,
        alert_data: Dict[str, Any]
    ) -> None:
        """Publish value bet alert to user's channel.

        Args:
            user_id: User ID to send alert to
            alert_data: Alert data dictionary
        """
        channel = f"alerts:{user_id}"

        message = {
            "type": "value_bet",
            "data": alert_data,
            "timestamp": asyncio.get_event_loop().time()
        }

        await self.pubsub.publish(channel, message)

    async def publish_arbitrage_alert(
        self,
        user_id: str,
        arbitrage_data: Dict[str, Any]
    ) -> None:
        """Publish arbitrage alert to user's channel.

        Args:
            user_id: User ID to send alert to
            arbitrage_data: Arbitrage opportunity data
        """
        channel = f"alerts:{user_id}"

        message = {
            "type": "arbitrage",
            "data": arbitrage_data,
            "timestamp": asyncio.get_event_loop().time()
        }

        await self.pubsub.publish(channel, message)

    async def broadcast_system_message(
        self,
        message: str,
        level: str = "info"
    ) -> None:
        """Broadcast system message to all users.

        Args:
            message: Message text
            level: Message level (info, warning, error)
        """
        channel = "system:broadcast"

        data = {
            "type": "system",
            "message": message,
            "level": level,
            "timestamp": asyncio.get_event_loop().time()
        }

        await self.pubsub.publish(channel, data)

    async def publish_market_update(
        self,
        sport: str,
        update_data: Dict[str, Any]
    ) -> None:
        """Publish market update for a sport.

        Args:
            sport: Sport identifier
            update_data: Market update data
        """
        channel = f"market:{sport}"

        message = {
            "type": "market_update",
            "sport": sport,
            "data": update_data,
            "timestamp": asyncio.get_event_loop().time()
        }

        await self.pubsub.publish(channel, message)