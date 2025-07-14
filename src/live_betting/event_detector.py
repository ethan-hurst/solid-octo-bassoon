"""Live event detection system for real-time game analysis."""
import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import re

from src.models.live_schemas import (
    LiveEvent, LiveEventType, LiveGameState, ScoreUpdate,
    GameEvent, MomentumScore
)
from src.data_collection.cache_manager import CacheManager

logger = logging.getLogger(__name__)


class EventImpactCalculator:
    """Calculate the impact of game events on win probabilities."""
    
    def __init__(self):
        # Sport-specific impact weights
        self.impact_weights = {
            "NFL": {
                "touchdown": 0.15,
                "field_goal": 0.08,
                "safety": 0.05,
                "interception": 0.12,
                "fumble": 0.10,
                "sack": 0.03,
                "penalty": 0.02,
                "timeout": 0.01,
                "injury": 0.05
            },
            "NBA": {
                "three_pointer": 0.02,
                "dunk": 0.02,
                "steal": 0.03,
                "block": 0.02,
                "technical_foul": 0.03,
                "flagrant_foul": 0.05,
                "injury": 0.08,
                "timeout": 0.01
            },
            "MLB": {
                "home_run": 0.12,
                "triple": 0.08,
                "double": 0.05,
                "single": 0.03,
                "walk": 0.02,
                "strikeout": 0.02,
                "error": 0.04,
                "injury": 0.06
            },
            "NHL": {
                "goal": 0.20,
                "assist": 0.08,
                "penalty": 0.05,
                "power_play": 0.08,
                "short_handed_goal": 0.15,
                "save": 0.01,
                "injury": 0.08
            }
        }
    
    def calculate_event_impact(
        self, 
        event: LiveEvent, 
        game_state: LiveGameState
    ) -> float:
        """Calculate the impact score of an event on the game."""
        sport = game_state.sport
        event_type = event.event_type.value
        
        # Base impact from lookup table
        base_impact = self.impact_weights.get(sport, {}).get(event_type, 0.02)
        
        # Adjust impact based on game context
        context_multiplier = self._calculate_context_multiplier(event, game_state)
        
        # Adjust impact based on timing (late game events have more impact)
        timing_multiplier = self._calculate_timing_multiplier(game_state)
        
        # Calculate final impact score
        impact_score = base_impact * context_multiplier * timing_multiplier
        
        return min(impact_score, 1.0)  # Cap at 1.0
    
    def _calculate_context_multiplier(self, event: LiveEvent, game_state: LiveGameState) -> float:
        """Calculate context-based impact multiplier."""
        multiplier = 1.0
        
        # Score differential impact
        home_score = game_state.current_score.get("home", 0)
        away_score = game_state.current_score.get("away", 0)
        score_diff = abs(home_score - away_score)
        
        # Closer games have higher impact
        if score_diff <= 3:
            multiplier *= 1.5
        elif score_diff <= 7:
            multiplier *= 1.2
        elif score_diff >= 21:
            multiplier *= 0.5
        
        # Event-specific context
        if event.event_type == LiveEventType.SCORE:
            # Scoring events have higher impact when trailing
            event_data = event.event_data or {}
            scoring_team = event_data.get("team", "")
            
            if "home" in scoring_team.lower() and home_score < away_score:
                multiplier *= 1.3
            elif "away" in scoring_team.lower() and away_score < home_score:
                multiplier *= 1.3
        
        return multiplier
    
    def _calculate_timing_multiplier(self, game_state: LiveGameState) -> float:
        """Calculate timing-based impact multiplier."""
        # Default multiplier
        multiplier = 1.0
        
        if game_state.sport == "NFL":
            # NFL timing logic
            quarter = game_state.quarter_period
            if quarter >= 4:
                multiplier *= 1.5  # 4th quarter events matter more
            elif quarter == 1:
                multiplier *= 0.8  # 1st quarter events matter less
        
        elif game_state.sport == "NBA":
            # NBA timing logic
            quarter = game_state.quarter_period
            if quarter >= 4:
                multiplier *= 1.4
            elif quarter <= 2:
                multiplier *= 0.9
        
        # Could add clock-based timing for more precision
        
        return multiplier


class LiveEventDetector:
    """Detect and process live sporting events."""
    
    def __init__(self, cache_manager: CacheManager):
        self.cache_manager = cache_manager
        self.impact_calculator = EventImpactCalculator()
        self.event_history: Dict[str, List[LiveEvent]] = defaultdict(list)
        self.momentum_tracker: Dict[str, MomentumScore] = {}
        
    async def process_score_update(self, game_id: str, score_data: ScoreUpdate) -> Optional[LiveEvent]:
        """Process score changes and update probabilities."""
        try:
            # Get current game state
            current_state = await self._get_game_state(game_id)
            
            if not current_state:
                logger.warning(f"No game state found for {game_id}")
                return None
            
            # Check if this is actually a score change
            current_home_score = current_state.current_score.get("home", 0)
            current_away_score = current_state.current_score.get("away", 0)
            
            if (score_data.home_score == current_home_score and 
                score_data.away_score == current_away_score):
                # No score change
                return None
            
            # Determine which team scored
            home_scored = score_data.home_score > current_home_score
            away_scored = score_data.away_score > current_away_score
            
            if home_scored:
                scoring_team = "home"
                points_scored = score_data.home_score - current_home_score
            elif away_scored:
                scoring_team = "away"
                points_scored = score_data.away_score - current_away_score
            else:
                # Shouldn't happen, but handle gracefully
                return None
            
            # Create score event
            event = LiveEvent(
                game_id=game_id,
                event_type=LiveEventType.SCORE,
                description=f"{scoring_team.title()} team scored {points_scored} points",
                event_data={
                    "team": scoring_team,
                    "points": points_scored,
                    "new_score": {"home": score_data.home_score, "away": score_data.away_score},
                    "scoring_play": score_data.scoring_play
                },
                game_clock=score_data.game_clock,
                timestamp=datetime.utcnow()
            )
            
            # Calculate impact
            event.impact_score = self.impact_calculator.calculate_event_impact(event, current_state)
            
            # Calculate probability change (simplified)
            prob_change = await self._calculate_probability_change(event, current_state)
            event.probability_change = prob_change
            
            # Store event
            await self._store_event(event)
            
            # Update momentum
            await self._update_momentum(game_id, event)
            
            logger.info(f"Score event detected: {game_id} - {event.description}")
            
            return event
            
        except Exception as e:
            logger.error(f"Error processing score update: {e}")
            return None
    
    async def detect_key_events(self, game_data: Dict[str, Any]) -> List[LiveEvent]:
        """Detect penalties, injuries, momentum shifts, etc."""
        events = []
        game_id = game_data.get("game_id", "")
        
        if not game_id:
            return events
        
        try:
            # Extract play-by-play data if available
            plays = game_data.get("plays", [])
            
            for play in plays:
                event = await self._parse_play_event(game_id, play)
                if event:
                    events.append(event)
            
            # Detect momentum shifts
            momentum_events = await self._detect_momentum_shifts(game_id, events)
            events.extend(momentum_events)
            
            # Detect injury events
            injury_events = await self._detect_injury_events(game_id, game_data)
            events.extend(injury_events)
            
            return events
            
        except Exception as e:
            logger.error(f"Error detecting key events: {e}")
            return []
    
    async def _parse_play_event(self, game_id: str, play: Dict[str, Any]) -> Optional[LiveEvent]:
        """Parse individual play into event."""
        try:
            play_text = play.get("text", "").lower()
            play_type = play.get("type", {}).get("text", "").lower()
            
            # Detect event type from play description
            event_type = self._classify_play_type(play_text, play_type)
            
            if event_type == LiveEventType.PENALTY:
                # Parse penalty details
                penalty_info = self._parse_penalty(play_text)
                
                return LiveEvent(
                    game_id=game_id,
                    event_type=event_type,
                    description=play.get("text", ""),
                    event_data={
                        "penalty_type": penalty_info.get("type", "unknown"),
                        "yards": penalty_info.get("yards", 0),
                        "team": penalty_info.get("team", "unknown")
                    },
                    game_clock=play.get("clock", {}).get("displayValue"),
                    timestamp=datetime.utcnow()
                )
            
            elif event_type == LiveEventType.TURNOVER:
                # Parse turnover details
                turnover_info = self._parse_turnover(play_text)
                
                return LiveEvent(
                    game_id=game_id,
                    event_type=event_type,
                    description=play.get("text", ""),
                    event_data={
                        "turnover_type": turnover_info.get("type", "unknown"),
                        "recovering_team": turnover_info.get("team", "unknown")
                    },
                    game_clock=play.get("clock", {}).get("displayValue"),
                    timestamp=datetime.utcnow()
                )
            
            # Add more event type parsing as needed
            
            return None
            
        except Exception as e:
            logger.error(f"Error parsing play event: {e}")
            return None
    
    def _classify_play_type(self, play_text: str, play_type: str) -> Optional[LiveEventType]:
        """Classify play type based on description."""
        # Penalty detection
        penalty_keywords = ["penalty", "flag", "foul", "holding", "interference", "offside"]
        if any(keyword in play_text for keyword in penalty_keywords):
            return LiveEventType.PENALTY
        
        # Turnover detection
        turnover_keywords = ["interception", "fumble", "turnover", "recovered by"]
        if any(keyword in play_text for keyword in turnover_keywords):
            return LiveEventType.TURNOVER
        
        # Timeout detection
        if "timeout" in play_text:
            return LiveEventType.TIMEOUT
        
        # Injury detection
        injury_keywords = ["injury", "injured", "hurt", "down on the field"]
        if any(keyword in play_text for keyword in injury_keywords):
            return LiveEventType.INJURY
        
        return None
    
    def _parse_penalty(self, play_text: str) -> Dict[str, Any]:
        """Parse penalty information from play text."""
        penalty_info = {"type": "unknown", "yards": 0, "team": "unknown"}
        
        # Extract penalty type
        penalty_types = {
            "holding": "holding",
            "false start": "false_start",
            "offsides": "offsides",
            "pass interference": "pass_interference",
            "roughing": "roughing",
            "delay of game": "delay_of_game"
        }
        
        for penalty, penalty_type in penalty_types.items():
            if penalty in play_text:
                penalty_info["type"] = penalty_type
                break
        
        # Extract yardage using regex
        yard_match = re.search(r"(\d+)[- ]yard", play_text)
        if yard_match:
            penalty_info["yards"] = int(yard_match.group(1))
        
        return penalty_info
    
    def _parse_turnover(self, play_text: str) -> Dict[str, Any]:
        """Parse turnover information from play text."""
        turnover_info = {"type": "unknown", "team": "unknown"}
        
        if "interception" in play_text:
            turnover_info["type"] = "interception"
        elif "fumble" in play_text:
            turnover_info["type"] = "fumble"
        
        # Extract recovering team (simplified)
        if "recovered by" in play_text:
            # This would need more sophisticated parsing in production
            turnover_info["team"] = "unknown"
        
        return turnover_info
    
    async def _detect_momentum_shifts(self, game_id: str, recent_events: List[LiveEvent]) -> List[LiveEvent]:
        """Detect momentum shifts based on recent events."""
        momentum_events = []
        
        try:
            # Get recent event history
            all_events = self.event_history.get(game_id, [])
            all_events.extend(recent_events)
            
            # Look at last 5 minutes of events
            cutoff_time = datetime.utcnow() - timedelta(minutes=5)
            recent_events_filtered = [
                event for event in all_events 
                if event.timestamp >= cutoff_time
            ]
            
            if len(recent_events_filtered) < 3:
                return momentum_events
            
            # Calculate momentum score
            momentum = await self._calculate_momentum(game_id, recent_events_filtered)
            
            # Check for significant momentum shift
            previous_momentum = self.momentum_tracker.get(game_id)
            
            if previous_momentum:
                momentum_change = abs(momentum.momentum_strength - previous_momentum.momentum_strength)
                
                if momentum_change > 0.3:  # 30% momentum shift threshold
                    momentum_event = LiveEvent(
                        game_id=game_id,
                        event_type=LiveEventType.TURNOVER,  # Using turnover as momentum shift
                        description=f"Momentum shift detected: {momentum.momentum_direction} gaining momentum",
                        event_data={
                            "momentum_direction": momentum.momentum_direction,
                            "momentum_strength": momentum.momentum_strength,
                            "momentum_change": momentum_change
                        },
                        impact_score=momentum_change,
                        timestamp=datetime.utcnow()
                    )
                    
                    momentum_events.append(momentum_event)
            
            # Update momentum tracker
            self.momentum_tracker[game_id] = momentum
            
        except Exception as e:
            logger.error(f"Error detecting momentum shifts: {e}")
        
        return momentum_events
    
    async def _detect_injury_events(self, game_id: str, game_data: Dict[str, Any]) -> List[LiveEvent]:
        """Detect injury events from various data sources."""
        injury_events = []
        
        try:
            # Check for injury reports in game data
            injuries = game_data.get("injuries", [])
            
            for injury in injuries:
                injury_event = LiveEvent(
                    game_id=game_id,
                    event_type=LiveEventType.INJURY,
                    description=f"Injury reported: {injury.get('player', 'Unknown player')}",
                    event_data={
                        "player": injury.get("player", "unknown"),
                        "team": injury.get("team", "unknown"),
                        "injury_type": injury.get("type", "unknown"),
                        "severity": injury.get("severity", "unknown")
                    },
                    impact_score=0.05,  # Base injury impact
                    timestamp=datetime.utcnow()
                )
                
                injury_events.append(injury_event)
        
        except Exception as e:
            logger.error(f"Error detecting injury events: {e}")
        
        return injury_events
    
    async def update_game_state(self, game_id: str, events: List[LiveEvent]) -> None:
        """Update ML model inputs based on live events."""
        try:
            # Get current game state
            current_state = await self._get_game_state(game_id)
            
            if not current_state:
                return
            
            # Update game state based on events
            for event in events:
                await self._apply_event_to_game_state(current_state, event)
            
            # Store updated game state
            await self.cache_manager.set(
                f"live_game_state:{game_id}",
                current_state.model_dump(),
                ttl=3600
            )
            
            # Store events
            for event in events:
                await self._store_event(event)
            
        except Exception as e:
            logger.error(f"Error updating game state: {e}")
    
    async def _apply_event_to_game_state(self, game_state: LiveGameState, event: LiveEvent) -> None:
        """Apply event effects to game state."""
        try:
            # Update score if it's a scoring event
            if event.event_type == LiveEventType.SCORE:
                event_data = event.event_data or {}
                new_score = event_data.get("new_score", {})
                
                if new_score:
                    game_state.current_score = new_score
            
            # Update last updated timestamp
            game_state.last_updated = datetime.utcnow()
            
        except Exception as e:
            logger.error(f"Error applying event to game state: {e}")
    
    async def _calculate_probability_change(
        self, 
        event: LiveEvent, 
        game_state: LiveGameState
    ) -> Dict[str, float]:
        """Calculate how an event changes win probabilities."""
        # Simplified probability change calculation
        # In production, this would use more sophisticated models
        
        change = {"home": 0.0, "away": 0.0}
        
        if event.event_type == LiveEventType.SCORE:
            event_data = event.event_data or {}
            scoring_team = event_data.get("team", "")
            impact = event.impact_score
            
            if scoring_team == "home":
                change["home"] = impact
                change["away"] = -impact
            elif scoring_team == "away":
                change["away"] = impact
                change["home"] = -impact
        
        elif event.event_type == LiveEventType.TURNOVER:
            # Turnovers typically shift probability by 8-12%
            impact = event.impact_score
            event_data = event.event_data or {}
            recovering_team = event_data.get("recovering_team", "")
            
            if recovering_team == "home":
                change["home"] = impact
                change["away"] = -impact
            elif recovering_team == "away":
                change["away"] = impact
                change["home"] = -impact
        
        return change
    
    async def _calculate_momentum(self, game_id: str, events: List[LiveEvent]) -> MomentumScore:
        """Calculate game momentum based on recent events."""
        try:
            # Score events by team
            home_events = []
            away_events = []
            
            for event in events:
                event_data = event.event_data or {}
                team = event_data.get("team", "")
                
                if team == "home":
                    home_events.append(event)
                elif team == "away":
                    away_events.append(event)
            
            # Calculate momentum factors
            home_momentum = sum(event.impact_score for event in home_events)
            away_momentum = sum(event.impact_score for event in away_events)
            
            # Determine momentum direction and strength
            if home_momentum > away_momentum:
                direction = "home"
                strength = min(home_momentum / (home_momentum + away_momentum + 0.01), 1.0)
            elif away_momentum > home_momentum:
                direction = "away"
                strength = min(away_momentum / (home_momentum + away_momentum + 0.01), 1.0)
            else:
                direction = "neutral"
                strength = 0.5
            
            return MomentumScore(
                game_id=game_id,
                momentum_direction=direction,
                momentum_strength=strength,
                recent_events_factor=len(events) / 10.0,  # More events = higher factor
                scoring_rate_factor=min((home_momentum + away_momentum) / 0.5, 1.0)
            )
            
        except Exception as e:
            logger.error(f"Error calculating momentum: {e}")
            return MomentumScore(
                game_id=game_id,
                momentum_direction="neutral",
                momentum_strength=0.5,
                recent_events_factor=0.0,
                scoring_rate_factor=0.0
            )
    
    async def _update_momentum(self, game_id: str, event: LiveEvent) -> None:
        """Update momentum tracking based on new event."""
        try:
            # Get current momentum
            current_momentum = self.momentum_tracker.get(game_id)
            
            # Get recent events including this one
            recent_events = self.event_history.get(game_id, [])[-4:]  # Last 5 events
            recent_events.append(event)
            
            # Recalculate momentum
            new_momentum = await self._calculate_momentum(game_id, recent_events)
            self.momentum_tracker[game_id] = new_momentum
            
            # Cache momentum
            await self.cache_manager.set(
                f"live_momentum:{game_id}",
                new_momentum.model_dump(),
                ttl=600  # 10 minutes
            )
            
        except Exception as e:
            logger.error(f"Error updating momentum: {e}")
    
    async def _store_event(self, event: LiveEvent) -> None:
        """Store event in cache and history."""
        try:
            # Add to history
            self.event_history[event.game_id].append(event)
            
            # Keep only last 50 events per game
            if len(self.event_history[event.game_id]) > 50:
                self.event_history[event.game_id] = self.event_history[event.game_id][-50:]
            
            # Cache event
            await self.cache_manager.set(
                f"live_event:{event.game_id}:{event.timestamp.isoformat()}",
                event.model_dump(),
                ttl=3600  # 1 hour
            )
            
        except Exception as e:
            logger.error(f"Error storing event: {e}")
    
    async def _get_game_state(self, game_id: str) -> Optional[LiveGameState]:
        """Get current game state from cache."""
        try:
            cached_state = await self.cache_manager.get(f"live_game_state:{game_id}")
            
            if cached_state:
                return LiveGameState(**cached_state)
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting game state: {e}")
            return None