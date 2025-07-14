"""Real-time odds engine for live betting analysis."""
import asyncio
import logging
from typing import Dict, List, Optional, AsyncIterator, Any, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, deque
import numpy as np

from src.models.live_schemas import (
    LiveOdds, LineMovement, OddsUpdate, LiveValueBet,
    LivePrediction, LiveBetType
)
from src.analysis.value_calculator import ValueCalculator
from src.data_collection.cache_manager import CacheManager

logger = logging.getLogger(__name__)


class OddsTracker:
    """Track odds changes and detect movements."""
    
    def __init__(self, window_size: int = 100):
        self.window_size = window_size
        self.odds_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=window_size))
        self.last_odds: Dict[str, LiveOdds] = {}
        
    def add_odds_update(self, odds: LiveOdds) -> Optional[LineMovement]:
        """Add odds update and detect line movement."""
        odds_key = f"{odds.game_id}:{odds.bookmaker}:{odds.bet_type}:{odds.selection}"
        
        # Get previous odds for comparison
        previous_odds = self.last_odds.get(odds_key)
        
        # Store current odds
        self.odds_history[odds_key].append(odds)
        self.last_odds[odds_key] = odds
        
        # Detect movement if we have previous odds
        if previous_odds:
            return self._detect_line_movement(previous_odds, odds)
        
        return None
    
    def _detect_line_movement(self, old_odds: LiveOdds, new_odds: LiveOdds) -> Optional[LineMovement]:
        """Detect and classify line movement."""
        odds_change = new_odds.odds - old_odds.odds
        line_change = 0.0
        
        if new_odds.line is not None and old_odds.line is not None:
            line_change = new_odds.line - old_odds.line
        
        # Calculate movement significance
        odds_change_pct = abs(odds_change) / old_odds.odds
        significance = min(odds_change_pct * 10, 1.0)  # Scale to 0-1
        
        # Determine direction
        if odds_change > 0:
            direction = "up"
        elif odds_change < 0:
            direction = "down"
        else:
            direction = "stable"
        
        # Only report significant movements
        if significance > 0.02:  # 2% threshold
            return LineMovement(
                game_id=new_odds.game_id,
                bookmaker=new_odds.bookmaker,
                bet_type=new_odds.bet_type,
                old_line=old_odds.line,
                new_line=new_odds.line,
                old_odds=old_odds.odds,
                new_odds=new_odds.odds,
                movement_size=abs(odds_change),
                direction=direction,
                significance=significance,
                timestamp=new_odds.timestamp
            )
        
        return None
    
    def get_odds_trend(self, game_id: str, bookmaker: str, bet_type: str, selection: str) -> Dict[str, Any]:
        """Get odds trend analysis."""
        odds_key = f"{game_id}:{bookmaker}:{bet_type}:{selection}"
        history = self.odds_history.get(odds_key, deque())
        
        if len(history) < 2:
            return {"trend": "insufficient_data", "volatility": 0.0}
        
        # Calculate trend
        odds_values = [odds.odds for odds in history]
        
        # Simple linear trend
        x = np.arange(len(odds_values))
        slope = np.polyfit(x, odds_values, 1)[0]
        
        # Volatility (standard deviation)
        volatility = np.std(odds_values)
        
        trend = "increasing" if slope > 0.01 else "decreasing" if slope < -0.01 else "stable"
        
        return {
            "trend": trend,
            "slope": slope,
            "volatility": volatility,
            "current_odds": odds_values[-1],
            "min_odds": min(odds_values),
            "max_odds": max(odds_values),
            "data_points": len(odds_values)
        }


class LiveOddsEngine:
    """Real-time odds processing with millisecond precision."""
    
    def __init__(self, cache_manager: CacheManager):
        self.cache_manager = cache_manager
        self.odds_tracker = OddsTracker()
        self.value_calculator = ValueCalculator()
        self.active_streams: Dict[str, bool] = {}
        self.odds_subscribers: Dict[str, List[callable]] = defaultdict(list)
        
    async def stream_odds(self, game_id: str) -> AsyncIterator[LiveOdds]:
        """Stream live odds updates with timestamp precision."""
        stream_key = f"odds_stream:{game_id}"
        self.active_streams[stream_key] = True
        
        try:
            while self.active_streams.get(stream_key, False):
                # Get latest odds from cache
                cached_odds = await self.cache_manager.get(f"live_odds:{game_id}")
                
                if cached_odds:
                    for odds_data in cached_odds:
                        odds = LiveOdds(**odds_data)
                        yield odds
                
                # Check for updates every 100ms for sub-second precision
                await asyncio.sleep(0.1)
                
        except Exception as e:
            logger.error(f"Error streaming odds for {game_id}: {e}")
        finally:
            self.active_streams[stream_key] = False
    
    async def detect_line_movement(self, odds_update: LiveOdds) -> Optional[LineMovement]:
        """Detect significant line movements and betting opportunities."""
        try:
            # Add to tracker and detect movement
            movement = self.odds_tracker.add_odds_update(odds_update)
            
            if movement:
                # Cache significant movements
                await self.cache_manager.set(
                    f"line_movement:{movement.game_id}:{movement.timestamp.isoformat()}",
                    movement.model_dump(),
                    ttl=3600  # 1 hour
                )
                
                # Notify subscribers
                await self._notify_movement_subscribers(movement)
                
                logger.info(
                    f"Line movement detected: {movement.game_id} {movement.bookmaker} "
                    f"{movement.bet_type} {movement.direction} by {movement.movement_size:.3f}"
                )
            
            return movement
            
        except Exception as e:
            logger.error(f"Error detecting line movement: {e}")
            return None
    
    async def calculate_live_value(self, odds: LiveOdds, prediction: LivePrediction) -> Optional[LiveValueBet]:
        """Calculate real-time value betting opportunities."""
        try:
            # Get the relevant prediction probability
            if odds.bet_type == LiveBetType.MONEYLINE:
                if "home" in odds.selection.lower():
                    true_probability = prediction.home_win_probability
                elif "away" in odds.selection.lower():
                    true_probability = prediction.away_win_probability
                else:
                    true_probability = prediction.draw_probability or 0.0
            else:
                # For spread/total bets, use a more complex calculation
                true_probability = await self._calculate_spread_total_probability(odds, prediction)
            
            if true_probability <= 0:
                return None
            
            # Calculate implied probability from odds
            implied_probability = 1.0 / odds.odds
            
            # Calculate edge
            edge = true_probability - implied_probability
            
            # Only consider positive edge bets
            if edge <= 0:
                return None
            
            # Calculate fair odds
            fair_odds = 1.0 / true_probability
            
            # Calculate Kelly fraction
            kelly_fraction = edge / (odds.odds - 1.0)
            kelly_fraction = min(kelly_fraction, 0.25)  # Cap at 25%
            
            # Determine confidence based on prediction confidence and edge size
            confidence = min(prediction.confidence_score * (edge * 10), 1.0)
            
            # Only return high-confidence bets
            if confidence < 0.6:
                return None
            
            return LiveValueBet(
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
                expires_at=datetime.utcnow() + timedelta(minutes=15)  # 15 minute expiry
            )
            
        except Exception as e:
            logger.error(f"Error calculating live value: {e}")
            return None
    
    async def _calculate_spread_total_probability(self, odds: LiveOdds, prediction: LivePrediction) -> float:
        """Calculate probability for spread/total bets."""
        # This is a simplified implementation
        # In production, you'd want more sophisticated models
        
        if odds.bet_type == LiveBetType.SPREAD:
            # For spread bets, use the win probability and adjust for the spread
            base_prob = prediction.home_win_probability if "home" in odds.selection.lower() else prediction.away_win_probability
            
            # Adjust probability based on spread (simplified)
            if odds.line:
                # Rough adjustment: each point of spread is worth ~3% probability
                spread_adjustment = odds.line * 0.03
                return max(0.05, min(0.95, base_prob + spread_adjustment))
            
            return base_prob
            
        elif odds.bet_type == LiveBetType.TOTAL:
            # For totals, use a baseline of 50% and adjust based on game flow
            # This would typically involve more sophisticated modeling
            return 0.5
        
        return 0.5
    
    async def process_odds_batch(self, odds_batch: List[LiveOdds]) -> Dict[str, Any]:
        """Process a batch of odds updates efficiently."""
        results = {
            "movements": [],
            "value_bets": [],
            "processed_count": 0,
            "errors": []
        }
        
        for odds in odds_batch:
            try:
                # Detect movement
                movement = await self.detect_line_movement(odds)
                if movement:
                    results["movements"].append(movement)
                
                # Cache the odds update
                await self.cache_manager.set(
                    f"live_odds:{odds.game_id}:{odds.bookmaker}:{odds.bet_type.value}",
                    odds.model_dump(),
                    ttl=600  # 10 minutes
                )
                
                results["processed_count"] += 1
                
            except Exception as e:
                error_msg = f"Error processing odds for {odds.game_id}: {e}"
                logger.error(error_msg)
                results["errors"].append(error_msg)
        
        return results
    
    async def get_best_odds(self, game_id: str, bet_type: str, selection: str) -> Optional[LiveOdds]:
        """Get the best available odds for a specific bet."""
        try:
            # Get all odds for the game
            all_odds = await self.cache_manager.get(f"live_odds:{game_id}")
            
            if not all_odds:
                return None
            
            # Filter for specific bet type and selection
            matching_odds = []
            for odds_data in all_odds:
                odds = LiveOdds(**odds_data)
                if odds.bet_type.value == bet_type and odds.selection == selection:
                    matching_odds.append(odds)
            
            if not matching_odds:
                return None
            
            # Return highest odds (best for bettor)
            return max(matching_odds, key=lambda x: x.odds)
            
        except Exception as e:
            logger.error(f"Error getting best odds: {e}")
            return None
    
    async def get_market_depth(self, game_id: str, bet_type: str) -> Dict[str, Any]:
        """Get market depth analysis for a betting market."""
        try:
            # Get all odds for the game and bet type
            all_odds = await self.cache_manager.get(f"live_odds:{game_id}")
            
            if not all_odds:
                return {"depth": 0, "spread": 0.0, "bookmakers": []}
            
            # Filter for specific bet type
            market_odds = []
            for odds_data in all_odds:
                odds = LiveOdds(**odds_data)
                if odds.bet_type.value == bet_type:
                    market_odds.append(odds)
            
            if not market_odds:
                return {"depth": 0, "spread": 0.0, "bookmakers": []}
            
            # Group by selection
            by_selection = defaultdict(list)
            for odds in market_odds:
                by_selection[odds.selection].append(odds)
            
            # Calculate market metrics
            depth = len(set(odds.bookmaker for odds in market_odds))
            
            # Calculate bid-ask spread for each selection
            spreads = []
            for selection, odds_list in by_selection.items():
                if len(odds_list) > 1:
                    best_odds = max(odds_list, key=lambda x: x.odds).odds
                    worst_odds = min(odds_list, key=lambda x: x.odds).odds
                    spread = (best_odds - worst_odds) / worst_odds
                    spreads.append(spread)
            
            avg_spread = np.mean(spreads) if spreads else 0.0
            
            bookmakers = list(set(odds.bookmaker for odds in market_odds))
            
            return {
                "depth": depth,
                "spread": avg_spread,
                "bookmakers": bookmakers,
                "total_odds": len(market_odds),
                "selections": list(by_selection.keys())
            }
            
        except Exception as e:
            logger.error(f"Error getting market depth: {e}")
            return {"depth": 0, "spread": 0.0, "bookmakers": []}
    
    async def subscribe_to_odds_updates(self, game_id: str, callback: callable) -> None:
        """Subscribe to odds updates for a specific game."""
        key = f"odds:{game_id}"
        self.odds_subscribers[key].append(callback)
        logger.info(f"Added odds subscriber for {game_id}")
    
    async def unsubscribe_from_odds_updates(self, game_id: str, callback: callable) -> None:
        """Unsubscribe from odds updates."""
        key = f"odds:{game_id}"
        if callback in self.odds_subscribers[key]:
            self.odds_subscribers[key].remove(callback)
            logger.info(f"Removed odds subscriber for {game_id}")
    
    async def _notify_odds_subscribers(self, odds: LiveOdds) -> None:
        """Notify all subscribers of odds updates."""
        key = f"odds:{odds.game_id}"
        
        for callback in self.odds_subscribers[key]:
            try:
                await callback(odds)
            except Exception as e:
                logger.error(f"Error notifying odds subscriber: {e}")
    
    async def _notify_movement_subscribers(self, movement: LineMovement) -> None:
        """Notify subscribers of significant line movements."""
        # This would integrate with the notification system
        logger.debug(f"Line movement notification: {movement.game_id} - {movement.significance:.3f}")
    
    async def stop_odds_stream(self, game_id: str) -> None:
        """Stop odds streaming for a specific game."""
        stream_key = f"odds_stream:{game_id}"
        self.active_streams[stream_key] = False
        logger.info(f"Stopped odds stream for {game_id}")
    
    async def get_odds_summary(self, game_id: str) -> Dict[str, Any]:
        """Get comprehensive odds summary for a game."""
        try:
            summary = {
                "game_id": game_id,
                "timestamp": datetime.utcnow(),
                "markets": {},
                "movements": [],
                "best_odds": {}
            }
            
            # Get all odds for the game
            all_odds = await self.cache_manager.get(f"live_odds:{game_id}")
            
            if not all_odds:
                return summary
            
            # Process each market
            by_market = defaultdict(list)
            for odds_data in all_odds:
                odds = LiveOdds(**odds_data)
                market_key = f"{odds.bet_type.value}:{odds.selection}"
                by_market[market_key].append(odds)
            
            # Calculate market summaries
            for market_key, odds_list in by_market.items():
                bet_type, selection = market_key.split(":", 1)
                
                best_odds = max(odds_list, key=lambda x: x.odds)
                worst_odds = min(odds_list, key=lambda x: x.odds)
                
                summary["markets"][market_key] = {
                    "bet_type": bet_type,
                    "selection": selection,
                    "bookmaker_count": len(odds_list),
                    "best_odds": best_odds.odds,
                    "best_bookmaker": best_odds.bookmaker,
                    "worst_odds": worst_odds.odds,
                    "odds_spread": best_odds.odds - worst_odds.odds
                }
                
                # Track best odds by selection
                if selection not in summary["best_odds"]:
                    summary["best_odds"][selection] = {}
                summary["best_odds"][selection][bet_type] = {
                    "odds": best_odds.odds,
                    "bookmaker": best_odds.bookmaker
                }
            
            # Get recent movements
            movements_key = f"line_movement:{game_id}:*"
            recent_movements = await self.cache_manager.get_pattern(movements_key)
            summary["movements"] = recent_movements[-10:] if recent_movements else []
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting odds summary: {e}")
            return {"game_id": game_id, "error": str(e)}