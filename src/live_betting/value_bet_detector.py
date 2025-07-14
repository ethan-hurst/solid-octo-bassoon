"""Live value bet detection system for real-time betting opportunities."""
import asyncio
import logging
from typing import Dict, List, Optional, Set, Any, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, deque
import numpy as np

from src.models.live_schemas import (
    LiveOdds, LiveValueBet, LivePrediction, LiveGameState, 
    LiveEvent, LiveBetType, LiveAlertSubscription
)
from src.data_collection.cache_manager import CacheManager
from src.live_betting.probability_engine import LivePredictionEngine
from src.live_betting.odds_engine import LiveOddsEngine
from src.live_betting.websocket_manager import LiveBettingWebSocketManager

logger = logging.getLogger(__name__)


class ValueBetCriteria:
    """Criteria for value bet detection."""
    
    def __init__(
        self,
        min_edge: float = 0.02,
        min_confidence: float = 0.65,
        min_odds: float = 1.5,
        max_odds: float = 10.0,
        min_kelly_fraction: float = 0.01,
        max_kelly_fraction: float = 0.15,
        max_bet_lifetime_minutes: int = 30
    ):
        """Initialize value bet criteria.
        
        Args:
            min_edge: Minimum edge percentage (2% default)
            min_confidence: Minimum prediction confidence (65% default)
            min_odds: Minimum acceptable odds
            max_odds: Maximum acceptable odds
            min_kelly_fraction: Minimum Kelly fraction
            max_kelly_fraction: Maximum Kelly fraction
            max_bet_lifetime_minutes: Maximum time a value bet stays active
        """
        self.min_edge = min_edge
        self.min_confidence = min_confidence
        self.min_odds = min_odds
        self.max_odds = max_odds
        self.min_kelly_fraction = min_kelly_fraction
        self.max_kelly_fraction = max_kelly_fraction
        self.max_bet_lifetime_minutes = max_bet_lifetime_minutes


class ValueBetCalculator:
    """Calculate value betting metrics."""
    
    def __init__(self):
        self.kelly_multiplier = 0.25  # Conservative Kelly (25% of full Kelly)
        
    def calculate_edge(self, true_probability: float, odds: float) -> float:
        """Calculate betting edge.
        
        Args:
            true_probability: Model predicted probability
            odds: Bookmaker odds
            
        Returns:
            Edge percentage (positive = value bet)
        """
        try:
            implied_probability = 1.0 / odds
            edge = true_probability - implied_probability
            return edge
        except (ZeroDivisionError, ValueError):
            return -1.0  # Invalid edge
    
    def calculate_kelly_fraction(
        self, 
        true_probability: float, 
        odds: float,
        conservative: bool = True
    ) -> float:
        """Calculate Kelly fraction for bet sizing.
        
        Args:
            true_probability: Model predicted probability
            odds: Bookmaker odds
            conservative: Use conservative Kelly multiplier
            
        Returns:
            Kelly fraction (0-1)
        """
        try:
            if true_probability <= 0 or odds <= 1:
                return 0.0
            
            # Kelly formula: f = (bp - q) / b
            # where b = odds - 1, p = true prob, q = 1 - p
            b = odds - 1.0
            p = true_probability
            q = 1.0 - p
            
            kelly_fraction = (b * p - q) / b
            
            # Apply conservative multiplier
            if conservative:
                kelly_fraction *= self.kelly_multiplier
            
            # Cap at reasonable limits
            return max(0.0, min(kelly_fraction, 0.25))
            
        except (ZeroDivisionError, ValueError):
            return 0.0
    
    def calculate_expected_value(
        self, 
        true_probability: float, 
        odds: float, 
        stake: float = 1.0
    ) -> float:
        """Calculate expected value of a bet.
        
        Args:
            true_probability: Model predicted probability
            odds: Bookmaker odds
            stake: Bet stake amount
            
        Returns:
            Expected value
        """
        try:
            # EV = (probability * (odds * stake - stake)) - ((1 - probability) * stake)
            win_amount = odds * stake - stake  # Profit if win
            lose_amount = stake  # Loss if lose
            
            ev = (true_probability * win_amount) - ((1 - true_probability) * lose_amount)
            return ev
            
        except (ZeroDivisionError, ValueError):
            return -stake  # Worst case
    
    def calculate_confidence_score(
        self,
        prediction_confidence: float,
        edge: float,
        odds_stability: float = 1.0,
        market_depth: float = 1.0
    ) -> float:
        """Calculate overall confidence score for value bet.
        
        Args:
            prediction_confidence: ML model confidence
            edge: Betting edge
            odds_stability: How stable the odds are
            market_depth: Market liquidity indicator
            
        Returns:
            Overall confidence score (0-1)
        """
        try:
            # Weight different factors
            weights = {
                'prediction': 0.4,
                'edge': 0.3,
                'stability': 0.2,
                'depth': 0.1
            }
            
            # Edge factor (larger edges get higher confidence)
            edge_factor = min(edge * 10, 1.0)  # Scale edge to 0-1
            
            # Combine factors
            confidence = (
                weights['prediction'] * prediction_confidence +
                weights['edge'] * edge_factor +
                weights['stability'] * odds_stability +
                weights['depth'] * market_depth
            )
            
            return max(0.0, min(confidence, 1.0))
            
        except (ZeroDivisionError, ValueError):
            return 0.0


class LiveValueBetDetector:
    """Real-time value bet detection system."""
    
    def __init__(
        self,
        cache_manager: CacheManager,
        prediction_engine: LivePredictionEngine,
        odds_engine: LiveOddsEngine,
        websocket_manager: Optional[LiveBettingWebSocketManager] = None
    ):
        """Initialize value bet detector.
        
        Args:
            cache_manager: Cache manager
            prediction_engine: Live prediction engine
            odds_engine: Live odds engine
            websocket_manager: WebSocket manager for notifications
        """
        self.cache_manager = cache_manager
        self.prediction_engine = prediction_engine
        self.odds_engine = odds_engine
        self.websocket_manager = websocket_manager
        
        self.calculator = ValueBetCalculator()
        self.criteria = ValueBetCriteria()
        
        # Active value bets tracking
        self.active_value_bets: Dict[str, LiveValueBet] = {}
        self.bet_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        
        # Subscription tracking
        self.user_subscriptions: Dict[str, List[LiveAlertSubscription]] = defaultdict(list)
        
        # Performance tracking
        self.detection_stats = {
            "total_processed": 0,
            "value_bets_found": 0,
            "alerts_sent": 0,
            "last_reset": datetime.utcnow()
        }
        
    async def process_odds_update(self, odds: LiveOdds) -> Optional[LiveValueBet]:
        """Process odds update and check for value betting opportunities.
        
        Args:
            odds: Live odds update
            
        Returns:
            Value bet if found, None otherwise
        """
        try:
            self.detection_stats["total_processed"] += 1
            
            # Get current prediction for the game
            prediction = await self._get_current_prediction(odds.game_id)
            if not prediction:
                logger.debug(f"No prediction available for game {odds.game_id}")
                return None
            
            # Calculate value bet metrics
            value_bet = await self._calculate_value_bet(odds, prediction)
            
            if value_bet and self._meets_criteria(value_bet):
                # Store value bet
                await self._store_value_bet(value_bet)
                
                # Send alerts
                await self._send_value_bet_alerts(value_bet)
                
                self.detection_stats["value_bets_found"] += 1
                
                logger.info(
                    f"Value bet detected: {value_bet.game_id} - "
                    f"{value_bet.bet_type} - {value_bet.edge:.3f} edge"
                )
                
                return value_bet
            
            return None
            
        except Exception as e:
            logger.error(f"Error processing odds update: {e}")
            return None
    
    async def _get_current_prediction(self, game_id: str) -> Optional[LivePrediction]:
        """Get current prediction for a game.
        
        Args:
            game_id: Game identifier
            
        Returns:
            Live prediction if available
        """
        try:
            # Try cache first
            cached_prediction = await self.cache_manager.get(f"live_prediction:{game_id}")
            
            if cached_prediction:
                return LivePrediction(**cached_prediction)
            
            # If no cached prediction, try to generate one
            game_data = await self.cache_manager.get(f"live_game_state:{game_id}")
            if not game_data:
                return None
            
            game_state = LiveGameState(**game_data)
            
            # Get recent events for context
            events_data = await self.cache_manager.get_pattern(f"live_event:{game_id}:*")
            recent_events = [LiveEvent(**event) for event in events_data or []]
            
            # Generate prediction
            prediction = await self.prediction_engine.predict_live_probabilities(
                game_state, recent_events
            )
            
            return prediction
            
        except Exception as e:
            logger.error(f"Error getting prediction for {game_id}: {e}")
            return None
    
    async def _calculate_value_bet(
        self, 
        odds: LiveOdds, 
        prediction: LivePrediction
    ) -> Optional[LiveValueBet]:
        """Calculate value bet metrics.
        
        Args:
            odds: Live odds
            prediction: Live prediction
            
        Returns:
            Value bet object if calculations successful
        """
        try:
            # Get true probability based on bet type
            true_probability = self._get_true_probability(odds, prediction)
            
            if true_probability <= 0:
                return None
            
            # Calculate edge
            edge = self.calculator.calculate_edge(true_probability, odds.odds)
            
            if edge <= 0:
                return None
            
            # Calculate Kelly fraction
            kelly_fraction = self.calculator.calculate_kelly_fraction(
                true_probability, odds.odds
            )
            
            # Calculate fair odds
            fair_odds = 1.0 / true_probability if true_probability > 0 else 0.0
            
            # Calculate confidence
            confidence = self.calculator.calculate_confidence_score(
                prediction.confidence_score,
                edge
            )
            
            # Create value bet
            value_bet = LiveValueBet(
                game_id=odds.game_id,
                bookmaker=odds.bookmaker,
                bet_type=odds.bet_type.value,
                selection=odds.selection,
                odds=odds.odds,
                fair_odds=fair_odds,
                edge=edge,
                confidence=confidence,
                kelly_fraction=kelly_fraction,
                detected_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(
                    minutes=self.criteria.max_bet_lifetime_minutes
                )
            )
            
            return value_bet
            
        except Exception as e:
            logger.error(f"Error calculating value bet: {e}")
            return None
    
    def _get_true_probability(self, odds: LiveOdds, prediction: LivePrediction) -> float:
        """Get true probability for the bet type.
        
        Args:
            odds: Live odds
            prediction: Live prediction
            
        Returns:
            True probability for this bet
        """
        try:
            if odds.bet_type == LiveBetType.MONEYLINE:
                # Moneyline bets
                if "home" in odds.selection.lower():
                    return prediction.home_win_probability
                elif "away" in odds.selection.lower():
                    return prediction.away_win_probability
                elif "draw" in odds.selection.lower() or "tie" in odds.selection.lower():
                    return prediction.draw_probability or 0.0
                else:
                    return 0.0
                    
            elif odds.bet_type == LiveBetType.SPREAD:
                # Point spread bets - simplified calculation
                base_prob = (
                    prediction.home_win_probability 
                    if "home" in odds.selection.lower() 
                    else prediction.away_win_probability
                )
                
                # Adjust for spread (simplified)
                if odds.line:
                    # Each point of spread roughly worth 3% probability
                    spread_adjustment = odds.line * 0.03
                    return max(0.05, min(0.95, base_prob + spread_adjustment))
                
                return base_prob
                
            elif odds.bet_type == LiveBetType.TOTAL:
                # Over/under total points - simplified
                # Would need more sophisticated modeling in production
                return 0.5  # Baseline 50/50 for totals
                
            else:
                # Other bet types - use conservative estimate
                return 0.4
                
        except Exception as e:
            logger.error(f"Error getting true probability: {e}")
            return 0.0
    
    def _meets_criteria(self, value_bet: LiveValueBet) -> bool:
        """Check if value bet meets detection criteria.
        
        Args:
            value_bet: Value bet to check
            
        Returns:
            True if meets criteria
        """
        try:
            # Check all criteria
            checks = [
                value_bet.edge >= self.criteria.min_edge,
                value_bet.confidence >= self.criteria.min_confidence,
                value_bet.odds >= self.criteria.min_odds,
                value_bet.odds <= self.criteria.max_odds,
                value_bet.kelly_fraction >= self.criteria.min_kelly_fraction,
                value_bet.kelly_fraction <= self.criteria.max_kelly_fraction
            ]
            
            return all(checks)
            
        except Exception as e:
            logger.error(f"Error checking criteria: {e}")
            return False
    
    async def _store_value_bet(self, value_bet: LiveValueBet) -> None:
        """Store value bet in cache and active tracking.
        
        Args:
            value_bet: Value bet to store
        """
        try:
            # Store in active bets
            bet_key = f"{value_bet.game_id}:{value_bet.bookmaker}:{value_bet.bet_type}:{value_bet.selection}"
            self.active_value_bets[bet_key] = value_bet
            
            # Cache value bet
            await self.cache_manager.set(
                f"value_bet:{value_bet.id}",
                value_bet.model_dump(),
                ttl=self.criteria.max_bet_lifetime_minutes * 60
            )
            
            # Add to game's value bets list
            game_value_bets = await self.cache_manager.get(f"value_bets:{value_bet.game_id}") or []
            game_value_bets.append(value_bet.model_dump())
            
            # Keep only recent bets (last 20)
            game_value_bets = game_value_bets[-20:]
            
            await self.cache_manager.set(
                f"value_bets:{value_bet.game_id}",
                game_value_bets,
                ttl=3600  # 1 hour
            )
            
            # Add to history
            self.bet_history[value_bet.game_id].append(value_bet)
            
        except Exception as e:
            logger.error(f"Error storing value bet: {e}")
    
    async def _send_value_bet_alerts(self, value_bet: LiveValueBet) -> None:
        """Send alerts for value bet discovery.
        
        Args:
            value_bet: Value bet to alert about
        """
        try:
            # WebSocket broadcast
            if self.websocket_manager:
                await self.websocket_manager.broadcast_value_bet(value_bet)
            
            # User-specific alerts
            await self._send_user_alerts(value_bet)
            
            self.detection_stats["alerts_sent"] += 1
            
        except Exception as e:
            logger.error(f"Error sending value bet alerts: {e}")
    
    async def _send_user_alerts(self, value_bet: LiveValueBet) -> None:
        """Send targeted user alerts based on subscriptions.
        
        Args:
            value_bet: Value bet to alert about
        """
        try:
            # Get relevant subscriptions
            relevant_subscriptions = []
            
            for user_id, subscriptions in self.user_subscriptions.items():
                for subscription in subscriptions:
                    if self._subscription_matches(subscription, value_bet):
                        relevant_subscriptions.append((user_id, subscription))
            
            # Send alerts to matching users
            for user_id, subscription in relevant_subscriptions:
                if self.websocket_manager:
                    alert_data = {
                        "type": "value_bet_alert",
                        "value_bet": value_bet.model_dump(),
                        "subscription": subscription.model_dump()
                    }
                    
                    await self.websocket_manager.send_user_alert(user_id, alert_data)
            
        except Exception as e:
            logger.error(f"Error sending user alerts: {e}")
    
    def _subscription_matches(
        self, 
        subscription: LiveAlertSubscription, 
        value_bet: LiveValueBet
    ) -> bool:
        """Check if subscription matches value bet.
        
        Args:
            subscription: User subscription
            value_bet: Value bet
            
        Returns:
            True if subscription matches
        """
        try:
            # Check edge threshold
            if value_bet.edge < subscription.min_edge_threshold:
                return False
            
            # Check subscription type
            if subscription.subscription_type == "game":
                return subscription.subscription_target == value_bet.game_id
            elif subscription.subscription_type == "sport":
                # Would need sport info from game
                return True  # Simplified for now
            elif subscription.subscription_type == "team":
                # Would need team info from game
                return True  # Simplified for now
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking subscription match: {e}")
            return False
    
    async def cleanup_expired_bets(self) -> int:
        """Clean up expired value bets.
        
        Returns:
            Number of bets cleaned up
        """
        try:
            current_time = datetime.utcnow()
            expired_count = 0
            
            # Check active bets for expiration
            expired_keys = []
            for bet_key, value_bet in self.active_value_bets.items():
                if value_bet.expires_at and current_time > value_bet.expires_at:
                    expired_keys.append(bet_key)
                    expired_count += 1
            
            # Remove expired bets
            for key in expired_keys:
                del self.active_value_bets[key]
            
            if expired_count > 0:
                logger.info(f"Cleaned up {expired_count} expired value bets")
            
            return expired_count
            
        except Exception as e:
            logger.error(f"Error cleaning up expired bets: {e}")
            return 0
    
    async def add_user_subscription(self, subscription: LiveAlertSubscription) -> None:
        """Add user subscription for value bet alerts.
        
        Args:
            subscription: User subscription
        """
        try:
            self.user_subscriptions[subscription.user_id].append(subscription)
            logger.info(f"Added subscription for user {subscription.user_id}")
            
        except Exception as e:
            logger.error(f"Error adding subscription: {e}")
    
    async def remove_user_subscription(
        self, 
        user_id: str, 
        subscription_target: str
    ) -> bool:
        """Remove user subscription.
        
        Args:
            user_id: User identifier
            subscription_target: Subscription target to remove
            
        Returns:
            True if removed successfully
        """
        try:
            user_subs = self.user_subscriptions.get(user_id, [])
            original_count = len(user_subs)
            
            # Filter out matching subscriptions
            self.user_subscriptions[user_id] = [
                sub for sub in user_subs
                if sub.subscription_target != subscription_target
            ]
            
            removed_count = original_count - len(self.user_subscriptions[user_id])
            
            if removed_count > 0:
                logger.info(f"Removed {removed_count} subscriptions for user {user_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error removing subscription: {e}")
            return False
    
    def get_active_value_bets(self, game_id: Optional[str] = None) -> List[LiveValueBet]:
        """Get currently active value bets.
        
        Args:
            game_id: Optional game filter
            
        Returns:
            List of active value bets
        """
        try:
            current_time = datetime.utcnow()
            active_bets = []
            
            for value_bet in self.active_value_bets.values():
                # Check if still active and not expired
                if (value_bet.is_active and 
                    (not value_bet.expires_at or current_time <= value_bet.expires_at)):
                    
                    if not game_id or value_bet.game_id == game_id:
                        active_bets.append(value_bet)
            
            return sorted(active_bets, key=lambda x: x.edge, reverse=True)
            
        except Exception as e:
            logger.error(f"Error getting active value bets: {e}")
            return []
    
    def get_detection_stats(self) -> Dict[str, Any]:
        """Get value bet detection statistics.
        
        Returns:
            Detection statistics
        """
        return {
            **self.detection_stats,
            "active_bets": len(self.active_value_bets),
            "user_subscriptions": sum(len(subs) for subs in self.user_subscriptions.values()),
            "uptime_minutes": (datetime.utcnow() - self.detection_stats["last_reset"]).total_seconds() / 60
        }
    
    def update_criteria(self, **kwargs) -> None:
        """Update detection criteria.
        
        Args:
            **kwargs: Criteria parameters to update
        """
        try:
            for key, value in kwargs.items():
                if hasattr(self.criteria, key):
                    setattr(self.criteria, key, value)
                    logger.info(f"Updated criteria {key} to {value}")
                    
        except Exception as e:
            logger.error(f"Error updating criteria: {e}")
    
    async def start_monitoring(self) -> None:
        """Start background monitoring tasks."""
        try:
            # Start cleanup task
            asyncio.create_task(self._cleanup_task())
            logger.info("Value bet detector monitoring started")
            
        except Exception as e:
            logger.error(f"Error starting monitoring: {e}")
    
    async def _cleanup_task(self) -> None:
        """Background cleanup task."""
        while True:
            try:
                await asyncio.sleep(300)  # Run every 5 minutes
                await self.cleanup_expired_bets()
                
            except Exception as e:
                logger.error(f"Error in cleanup task: {e}")
                await asyncio.sleep(300)  # Continue after error