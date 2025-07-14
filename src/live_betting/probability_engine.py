"""Dynamic probability engine for real-time win probability calculations."""
import asyncio
import logging
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, deque
import pickle
import joblib

from src.models.live_schemas import (
    LiveGameState, LiveEvent, LivePrediction, LiveBettingFeatures,
    EventPrediction, MomentumScore
)
from src.data_collection.cache_manager import CacheManager

logger = logging.getLogger(__name__)


class ModelManager:
    """Manage ML models for different sports and prediction types."""
    
    def __init__(self):
        self.models: Dict[str, Any] = {}
        self.model_versions: Dict[str, str] = {}
        self.feature_importances: Dict[str, Dict[str, float]] = {}
        self.last_updated: Dict[str, datetime] = {}
        
    async def load_models(self) -> None:
        """Load pre-trained models for each sport."""
        try:
            # In production, these would be loaded from model artifacts
            # For now, we'll simulate the model structure
            sports = ["NFL", "NBA", "MLB", "NHL"]
            
            for sport in sports:
                # Main win probability model (XGBoost)
                model_key = f"{sport}_win_probability"
                self.models[model_key] = self._create_dummy_xgboost_model(sport)
                self.model_versions[model_key] = "v2.1.0"
                
                # LSTM model for sequence prediction
                lstm_key = f"{sport}_lstm_sequence"
                self.models[lstm_key] = self._create_dummy_lstm_model(sport)
                self.model_versions[lstm_key] = "v1.8.0"
                
                # Event prediction model
                event_key = f"{sport}_event_prediction"
                self.models[event_key] = self._create_dummy_event_model(sport)
                self.model_versions[event_key] = "v1.5.0"
                
                self.last_updated[model_key] = datetime.utcnow()
                
                logger.info(f"Loaded models for {sport}")
                
        except Exception as e:
            logger.error(f"Error loading models: {e}")
            raise
    
    def _create_dummy_xgboost_model(self, sport: str) -> Dict[str, Any]:
        """Create a dummy XGBoost model structure."""
        # In production, this would be an actual XGBoost model
        return {
            "type": "xgboost",
            "sport": sport,
            "features": self._get_feature_names(sport),
            "n_estimators": 100,
            "max_depth": 6,
            "learning_rate": 0.1
        }
    
    def _create_dummy_lstm_model(self, sport: str) -> Dict[str, Any]:
        """Create a dummy LSTM model structure."""
        return {
            "type": "lstm",
            "sport": sport,
            "sequence_length": 10,
            "hidden_units": 64,
            "layers": 2
        }
    
    def _create_dummy_event_model(self, sport: str) -> Dict[str, Any]:
        """Create a dummy event prediction model."""
        return {
            "type": "random_forest",
            "sport": sport,
            "n_estimators": 50,
            "max_depth": 8
        }
    
    def _get_feature_names(self, sport: str) -> List[str]:
        """Get feature names for a sport."""
        base_features = [
            "score_differential", "total_points", "time_remaining_minutes",
            "quarter_period", "momentum_score", "recent_scoring_rate_home",
            "recent_scoring_rate_away", "line_movement", "h2h_performance",
            "recent_form_home", "recent_form_away"
        ]
        
        sport_specific = {
            "NFL": ["possession", "down_distance", "field_position", "timeout_remaining"],
            "NBA": ["fouls_home", "fouls_away", "free_throw_attempts"],
            "MLB": ["inning", "balls", "strikes", "baserunners"],
            "NHL": ["power_play", "shots_on_goal", "penalty_minutes"]
        }
        
        return base_features + sport_specific.get(sport, [])
    
    async def predict_win_probability(
        self, 
        sport: str, 
        features: LiveBettingFeatures
    ) -> Tuple[float, float, Optional[float]]:
        """Predict win probabilities using XGBoost model."""
        try:
            model_key = f"{sport}_win_probability"
            model = self.models.get(model_key)
            
            if not model:
                # Fallback calculation
                return self._fallback_probability(features)
            
            # Extract features for model
            feature_vector = self._extract_feature_vector(features, sport)
            
            # Simulate XGBoost prediction
            home_prob = self._simulate_xgboost_prediction(feature_vector, "home")
            away_prob = 1.0 - home_prob
            draw_prob = None
            
            # Adjust for sports that can have draws
            if sport in ["MLB"]:  # MLB rarely has draws, but possible in some situations
                draw_prob = 0.0
            
            return home_prob, away_prob, draw_prob
            
        except Exception as e:
            logger.error(f"Error in win probability prediction: {e}")
            return self._fallback_probability(features)
    
    def _simulate_xgboost_prediction(self, features: List[float], target: str) -> float:
        """Simulate XGBoost model prediction."""
        # Simplified simulation based on key features
        score_diff = features[0] if features else 0  # score_differential
        time_remaining = features[2] if len(features) > 2 else 30  # time_remaining_minutes
        momentum = features[4] if len(features) > 4 else 0  # momentum_score
        
        # Base probability from score differential
        base_prob = 0.5 + (score_diff * 0.02)  # Each point is worth ~2%
        
        # Time adjustment (closer to end = more certain)
        time_factor = max(0.1, time_remaining / 60.0)  # Normalize to 0-1
        certainty = 1.0 - time_factor
        
        # Apply momentum
        momentum_adjustment = momentum * 0.1
        
        # Combine factors
        final_prob = base_prob + momentum_adjustment
        
        # Apply certainty (less variance with less time)
        if certainty > 0.5:
            if final_prob > 0.5:
                final_prob = 0.5 + (final_prob - 0.5) * (1 + certainty)
            else:
                final_prob = 0.5 - (0.5 - final_prob) * (1 + certainty)
        
        return max(0.05, min(0.95, final_prob))
    
    def _extract_feature_vector(self, features: LiveBettingFeatures, sport: str) -> List[float]:
        """Extract feature vector for model input."""
        vector = [
            float(features.score_differential),
            float(features.total_points),
            float(features.time_remaining_minutes),
            float(features.quarter_period),
            float(features.momentum_score),
            float(features.recent_scoring_rate_home),
            float(features.recent_scoring_rate_away),
            float(features.line_movement),
            float(features.h2h_performance),
            float(features.recent_form_home),
            float(features.recent_form_away)
        ]
        
        # Add sport-specific features
        if sport == "NFL":
            vector.extend([
                1.0 if features.possession == "home" else 0.0,
                float(features.field_position or 50),
                0.0  # timeout_remaining placeholder
            ])
        elif sport == "NBA":
            vector.extend([0.0, 0.0, 0.0])  # fouls, free_throws placeholders
        elif sport == "MLB":
            vector.extend([0.0, 0.0, 0.0, 0.0])  # inning, balls, strikes, baserunners
        elif sport == "NHL":
            vector.extend([0.0, 0.0, 0.0])  # power_play, shots, penalty_minutes
        
        return vector
    
    def _fallback_probability(self, features: LiveBettingFeatures) -> Tuple[float, float, Optional[float]]:
        """Fallback probability calculation when models unavailable."""
        score_diff = features.score_differential
        time_remaining = features.time_remaining_minutes
        
        # Simple logistic function based on score differential
        # Adjust for time remaining (more certain as time decreases)
        time_factor = max(0.1, time_remaining / 60.0)
        
        # Base probability from score differential
        home_prob = 1 / (1 + np.exp(-score_diff * 0.15))
        
        # Adjust certainty based on time
        if time_factor < 0.5:
            # Less time = more extreme probabilities
            home_prob = 0.5 + (home_prob - 0.5) * (2 - time_factor)
        
        home_prob = max(0.05, min(0.95, home_prob))
        away_prob = 1.0 - home_prob
        
        return home_prob, away_prob, None


class FeatureExtractor:
    """Extract features from live game state for ML models."""
    
    def __init__(self, cache_manager: CacheManager):
        self.cache_manager = cache_manager
        self.game_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=50))
        
    async def extract_features(
        self, 
        game_state: LiveGameState, 
        recent_events: List[LiveEvent],
        momentum: Optional[MomentumScore] = None
    ) -> LiveBettingFeatures:
        """Extract comprehensive features for ML prediction."""
        try:
            # Basic game state features
            home_score = game_state.current_score.get("home", 0)
            away_score = game_state.current_score.get("away", 0)
            score_differential = home_score - away_score
            total_points = home_score + away_score
            
            # Time features
            time_remaining = await self._calculate_time_remaining(game_state)
            
            # Momentum features
            momentum_score = momentum.momentum_strength if momentum else 0.0
            scoring_rates = await self._calculate_scoring_rates(game_state, recent_events)
            
            # Historical features
            historical_features = await self._get_historical_features(game_state)
            
            # Market features
            market_features = await self._get_market_features(game_state.game_id)
            
            # Sport-specific features
            sport_features = await self._extract_sport_specific_features(game_state)
            
            return LiveBettingFeatures(
                game_id=game_state.game_id,
                score_differential=score_differential,
                total_points=total_points,
                time_remaining_minutes=time_remaining,
                quarter_period=game_state.quarter_period,
                recent_scoring_rate_home=scoring_rates["home"],
                recent_scoring_rate_away=scoring_rates["away"],
                momentum_score=momentum_score,
                possession=game_state.possession,
                down_distance=game_state.down_distance,
                field_position=self._parse_field_position(game_state.field_position),
                line_movement=market_features.get("line_movement", 0.0),
                volume_indicator=market_features.get("volume_indicator", 0.0),
                h2h_performance=historical_features.get("h2h_performance", 0.0),
                recent_form_home=historical_features.get("recent_form_home", 0.0),
                recent_form_away=historical_features.get("recent_form_away", 0.0)
            )
            
        except Exception as e:
            logger.error(f"Error extracting features: {e}")
            return self._default_features(game_state)
    
    async def _calculate_time_remaining(self, game_state: LiveGameState) -> float:
        """Calculate time remaining in minutes."""
        try:
            if not game_state.is_active:
                return 0.0
            
            sport = game_state.sport
            quarter = game_state.quarter_period
            
            # Sport-specific time calculation
            if sport == "NFL":
                total_time = 60.0  # 4 quarters × 15 minutes
                elapsed_quarters = (quarter - 1) * 15.0
                
                # Parse game clock if available
                if game_state.game_clock:
                    clock_parts = str(game_state.game_clock).split(":")
                    if len(clock_parts) == 2:
                        minutes = int(clock_parts[0])
                        seconds = int(clock_parts[1])
                        quarter_time_remaining = minutes + (seconds / 60.0)
                        return total_time - elapsed_quarters - (15.0 - quarter_time_remaining)
                
                # Default calculation
                return total_time - (quarter * 15.0)
                
            elif sport == "NBA":
                total_time = 48.0  # 4 quarters × 12 minutes
                elapsed_quarters = (quarter - 1) * 12.0
                return max(0.0, total_time - elapsed_quarters - 6.0)  # Estimate mid-quarter
                
            elif sport == "NHL":
                total_time = 60.0  # 3 periods × 20 minutes
                elapsed_periods = (quarter - 1) * 20.0
                return max(0.0, total_time - elapsed_periods - 10.0)  # Estimate mid-period
                
            elif sport == "MLB":
                # Baseball is different - estimate based on inning
                if quarter <= 9:
                    return (9 - quarter) * 20.0  # Rough estimate: 20 min per inning
                else:
                    return 10.0  # Extra innings
            
            return 30.0  # Default fallback
            
        except Exception as e:
            logger.error(f"Error calculating time remaining: {e}")
            return 30.0
    
    async def _calculate_scoring_rates(
        self, 
        game_state: LiveGameState, 
        recent_events: List[LiveEvent]
    ) -> Dict[str, float]:
        """Calculate recent scoring rates for both teams."""
        try:
            # Look at last 15 minutes of events
            cutoff_time = datetime.utcnow() - timedelta(minutes=15)
            recent_scoring_events = [
                event for event in recent_events
                if event.timestamp >= cutoff_time and event.event_type.value == "score"
            ]
            
            home_points = sum(
                event.event_data.get("points", 0) 
                for event in recent_scoring_events
                if event.event_data.get("team") == "home"
            )
            
            away_points = sum(
                event.event_data.get("points", 0)
                for event in recent_scoring_events  
                if event.event_data.get("team") == "away"
            )
            
            # Convert to points per hour
            time_window_hours = 15.0 / 60.0
            
            return {
                "home": home_points / time_window_hours,
                "away": away_points / time_window_hours
            }
            
        except Exception as e:
            logger.error(f"Error calculating scoring rates: {e}")
            return {"home": 0.0, "away": 0.0}
    
    async def _get_historical_features(self, game_state: LiveGameState) -> Dict[str, float]:
        """Get historical performance features."""
        try:
            # In production, this would query historical database
            # For now, simulate based on cached data
            
            cached_h2h = await self.cache_manager.get(
                f"h2h_performance:{game_state.home_team}:{game_state.away_team}"
            )
            
            cached_form = await self.cache_manager.get(
                f"recent_form:{game_state.home_team}:{game_state.away_team}"
            )
            
            return {
                "h2h_performance": cached_h2h or 0.0,
                "recent_form_home": cached_form.get("home", 0.0) if cached_form else 0.0,
                "recent_form_away": cached_form.get("away", 0.0) if cached_form else 0.0
            }
            
        except Exception as e:
            logger.error(f"Error getting historical features: {e}")
            return {"h2h_performance": 0.0, "recent_form_home": 0.0, "recent_form_away": 0.0}
    
    async def _get_market_features(self, game_id: str) -> Dict[str, float]:
        """Get betting market features."""
        try:
            # Get line movement data
            line_movements = await self.cache_manager.get_pattern(f"line_movement:{game_id}:*")
            
            if line_movements:
                recent_movement = sum(
                    abs(movement.get("movement_size", 0))
                    for movement in line_movements[-5:]  # Last 5 movements
                )
                line_movement = recent_movement / 5.0
            else:
                line_movement = 0.0
            
            # Volume indicator (simplified)
            volume_indicator = min(len(line_movements) / 10.0, 1.0) if line_movements else 0.0
            
            return {
                "line_movement": line_movement,
                "volume_indicator": volume_indicator
            }
            
        except Exception as e:
            logger.error(f"Error getting market features: {e}")
            return {"line_movement": 0.0, "volume_indicator": 0.0}
    
    async def _extract_sport_specific_features(self, game_state: LiveGameState) -> Dict[str, Any]:
        """Extract sport-specific features."""
        features = {}
        
        if game_state.sport == "NFL":
            features.update({
                "possession": game_state.possession,
                "down_distance": game_state.down_distance,
                "field_position": game_state.field_position
            })
        
        return features
    
    def _parse_field_position(self, field_position: Optional[str]) -> Optional[int]:
        """Parse field position string to numeric value."""
        if not field_position:
            return None
        
        try:
            # Parse formats like "OWN 25", "OPP 35", etc.
            parts = field_position.split()
            if len(parts) >= 2:
                yard_line = int(parts[1])
                if "OPP" in parts[0]:
                    return 100 - yard_line  # Convert to distance from endzone
                else:
                    return yard_line
            return 50  # Midfield default
        except:
            return 50
    
    def _default_features(self, game_state: LiveGameState) -> LiveBettingFeatures:
        """Create default features when extraction fails."""
        home_score = game_state.current_score.get("home", 0)
        away_score = game_state.current_score.get("away", 0)
        
        return LiveBettingFeatures(
            game_id=game_state.game_id,
            score_differential=home_score - away_score,
            total_points=home_score + away_score,
            time_remaining_minutes=30.0,
            quarter_period=game_state.quarter_period
        )


class LivePredictionEngine:
    """Real-time prediction engine with sub-100ms response time."""
    
    def __init__(self, cache_manager: CacheManager):
        self.cache_manager = cache_manager
        self.model_manager = ModelManager()
        self.feature_extractor = FeatureExtractor(cache_manager)
        self.prediction_cache: Dict[str, LivePrediction] = {}
        self.last_predictions: Dict[str, datetime] = {}
        self.prediction_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        
    async def initialize(self) -> None:
        """Initialize the prediction engine."""
        try:
            await self.model_manager.load_models()
            logger.info("Live prediction engine initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing prediction engine: {e}")
            raise
    
    async def predict_live_probabilities(
        self,
        game_state: LiveGameState,
        recent_events: List[LiveEvent],
        momentum: Optional[MomentumScore] = None
    ) -> LivePrediction:
        """Generate real-time win probability predictions."""
        try:
            start_time = datetime.utcnow()
            
            # Check cache for recent prediction (within 10 seconds)
            cached_prediction = await self._get_cached_prediction(game_state.game_id)
            if cached_prediction:
                return cached_prediction
            
            # Extract features
            features = await self.feature_extractor.extract_features(
                game_state, recent_events, momentum
            )
            
            # Get model predictions
            home_prob, away_prob, draw_prob = await self.model_manager.predict_win_probability(
                game_state.sport, features
            )
            
            # Calculate confidence score
            confidence = await self._calculate_confidence(game_state, features, recent_events)
            
            # Create prediction
            prediction = LivePrediction(
                game_id=game_state.game_id,
                model_version=self.model_manager.model_versions.get(
                    f"{game_state.sport}_win_probability", "v1.0.0"
                ),
                home_win_probability=home_prob,
                away_win_probability=away_prob,
                draw_probability=draw_prob,
                confidence_score=confidence,
                features_used=features.model_dump(),
                prediction_timestamp=datetime.utcnow()
            )
            
            # Cache prediction
            await self._cache_prediction(prediction)
            
            # Store in history
            self.prediction_history[game_state.game_id].append(prediction)
            
            # Log latency
            latency = (datetime.utcnow() - start_time).total_seconds() * 1000
            if latency > 100:
                logger.warning(f"Prediction latency {latency:.1f}ms exceeds target of 100ms")
            else:
                logger.debug(f"Prediction completed in {latency:.1f}ms")
            
            return prediction
            
        except Exception as e:
            logger.error(f"Error generating live predictions: {e}")
            return self._fallback_prediction(game_state)
    
    async def predict_next_event(
        self,
        game_state: LiveGameState,
        time_window_minutes: int = 5
    ) -> List[EventPrediction]:
        """Predict likely next events in the game."""
        try:
            sport = game_state.sport
            model_key = f"{sport}_event_prediction"
            
            if model_key not in self.model_manager.models:
                return []
            
            # Extract features for event prediction
            features = await self.feature_extractor.extract_features(
                game_state, [], None
            )
            
            # Simulate event predictions based on sport and game state
            predictions = []
            
            if sport == "NFL":
                # NFL event predictions
                event_probs = {
                    "touchdown": 0.15,
                    "field_goal": 0.08,
                    "turnover": 0.05,
                    "punt": 0.25
                }
            elif sport == "NBA":
                # NBA event predictions
                event_probs = {
                    "three_pointer": 0.30,
                    "free_throws": 0.20,
                    "steal": 0.10,
                    "foul": 0.25
                }
            elif sport == "MLB":
                # MLB event predictions
                event_probs = {
                    "hit": 0.25,
                    "strikeout": 0.20,
                    "walk": 0.10,
                    "home_run": 0.05
                }
            elif sport == "NHL":
                # NHL event predictions
                event_probs = {
                    "goal": 0.10,
                    "penalty": 0.15,
                    "save": 0.40,
                    "shot": 0.35
                }
            else:
                event_probs = {}
            
            # Adjust probabilities based on game context
            adjusted_probs = self._adjust_event_probabilities(
                event_probs, game_state, features
            )
            
            for event_type, probability in adjusted_probs.items():
                confidence = min(0.8, probability * 2)  # Simple confidence calculation
                
                predictions.append(EventPrediction(
                    game_id=game_state.game_id,
                    event_type=event_type,
                    probability=probability,
                    time_window_minutes=time_window_minutes,
                    confidence=confidence
                ))
            
            return sorted(predictions, key=lambda x: x.probability, reverse=True)[:5]
            
        except Exception as e:
            logger.error(f"Error predicting next events: {e}")
            return []
    
    def _adjust_event_probabilities(
        self,
        base_probs: Dict[str, float],
        game_state: LiveGameState,
        features: LiveBettingFeatures
    ) -> Dict[str, float]:
        """Adjust event probabilities based on game context."""
        adjusted = base_probs.copy()
        
        # Time-based adjustments
        time_factor = features.time_remaining_minutes / 60.0
        
        # Score-based adjustments
        score_diff = abs(features.score_differential)
        
        # Late game adjustments
        if time_factor < 0.25:  # Last quarter/period
            if game_state.sport == "NFL":
                if score_diff <= 7:  # Close game
                    adjusted["field_goal"] = adjusted.get("field_goal", 0) * 1.5
                    adjusted["timeout"] = 0.3
            elif game_state.sport == "NBA":
                if score_diff <= 10:  # Close game
                    adjusted["foul"] = adjusted.get("foul", 0) * 2.0
                    adjusted["free_throws"] = adjusted.get("free_throws", 0) * 1.8
        
        # Normalize probabilities
        total = sum(adjusted.values())
        if total > 0:
            adjusted = {k: v / total for k, v in adjusted.items()}
        
        return adjusted
    
    async def _calculate_confidence(
        self,
        game_state: LiveGameState,
        features: LiveBettingFeatures,
        recent_events: List[LiveEvent]
    ) -> float:
        """Calculate prediction confidence score."""
        try:
            confidence_factors = []
            
            # Time factor (more confident with less time remaining)
            time_confidence = 1.0 - (features.time_remaining_minutes / 60.0)
            confidence_factors.append(time_confidence)
            
            # Score differential factor (more confident with larger leads)
            score_confidence = min(1.0, abs(features.score_differential) / 20.0)
            confidence_factors.append(score_confidence)
            
            # Data quality factor (more events = higher confidence)
            data_confidence = min(1.0, len(recent_events) / 10.0)
            confidence_factors.append(data_confidence)
            
            # Model stability (if we have prediction history)
            history = self.prediction_history.get(game_state.game_id, deque())
            if len(history) >= 3:
                recent_probs = [p.home_win_probability for p in list(history)[-3:]]
                variance = np.var(recent_probs)
                stability_confidence = max(0.3, 1.0 - variance * 10)  # Lower variance = higher confidence
                confidence_factors.append(stability_confidence)
            
            # Average confidence factors
            final_confidence = np.mean(confidence_factors)
            return max(0.1, min(1.0, final_confidence))
            
        except Exception as e:
            logger.error(f"Error calculating confidence: {e}")
            return 0.5
    
    async def _get_cached_prediction(self, game_id: str) -> Optional[LivePrediction]:
        """Get cached prediction if recent enough."""
        try:
            last_prediction_time = self.last_predictions.get(game_id)
            
            if last_prediction_time:
                age = datetime.utcnow() - last_prediction_time
                if age.total_seconds() < 10:  # Cache for 10 seconds
                    cached = self.prediction_cache.get(game_id)
                    if cached:
                        return cached
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting cached prediction: {e}")
            return None
    
    async def _cache_prediction(self, prediction: LivePrediction) -> None:
        """Cache prediction for quick retrieval."""
        try:
            self.prediction_cache[prediction.game_id] = prediction
            self.last_predictions[prediction.game_id] = prediction.prediction_timestamp
            
            # Also cache in Redis for cross-service access
            await self.cache_manager.set(
                f"live_prediction:{prediction.game_id}",
                prediction.model_dump(),
                ttl=30  # 30 seconds TTL
            )
            
        except Exception as e:
            logger.error(f"Error caching prediction: {e}")
    
    def _fallback_prediction(self, game_state: LiveGameState) -> LivePrediction:
        """Create fallback prediction when main prediction fails."""
        home_score = game_state.current_score.get("home", 0)
        away_score = game_state.current_score.get("away", 0)
        score_diff = home_score - away_score
        
        # Simple fallback based on score
        if score_diff > 0:
            home_prob = 0.5 + min(0.4, score_diff * 0.03)
        elif score_diff < 0:
            home_prob = 0.5 - min(0.4, abs(score_diff) * 0.03)
        else:
            home_prob = 0.5
        
        return LivePrediction(
            game_id=game_state.game_id,
            model_version="fallback_v1.0.0",
            home_win_probability=home_prob,
            away_win_probability=1.0 - home_prob,
            draw_probability=None,
            confidence_score=0.3,  # Low confidence for fallback
            features_used={},
            prediction_timestamp=datetime.utcnow()
        )
    
    async def get_prediction_trend(self, game_id: str, window_minutes: int = 30) -> Dict[str, Any]:
        """Get prediction trend analysis for a game."""
        try:
            history = self.prediction_history.get(game_id, deque())
            
            if len(history) < 2:
                return {"trend": "insufficient_data", "predictions": 0}
            
            # Filter by time window
            cutoff_time = datetime.utcnow() - timedelta(minutes=window_minutes)
            recent_predictions = [
                p for p in history
                if p.prediction_timestamp >= cutoff_time
            ]
            
            if len(recent_predictions) < 2:
                return {"trend": "insufficient_recent_data", "predictions": len(recent_predictions)}
            
            # Calculate trend
            home_probs = [p.home_win_probability for p in recent_predictions]
            times = [(p.prediction_timestamp - recent_predictions[0].prediction_timestamp).total_seconds() 
                    for p in recent_predictions]
            
            # Simple linear trend
            slope = np.polyfit(times, home_probs, 1)[0] if len(times) > 1 else 0
            
            trend_direction = "increasing" if slope > 0.001 else "decreasing" if slope < -0.001 else "stable"
            volatility = np.std(home_probs)
            
            return {
                "trend": trend_direction,
                "slope": slope,
                "volatility": volatility,
                "predictions": len(recent_predictions),
                "latest_home_probability": home_probs[-1],
                "change_since_start": home_probs[-1] - home_probs[0]
            }
            
        except Exception as e:
            logger.error(f"Error getting prediction trend: {e}")
            return {"trend": "error", "predictions": 0}
    
    async def update_model_features(self, game_id: str, new_events: List[LiveEvent]) -> None:
        """Update model features based on new game events."""
        try:
            # This would trigger feature recalculation and potentially model updates
            # For now, we'll just log the update
            logger.debug(f"Updating model features for {game_id} with {len(new_events)} new events")
            
            # Invalidate cached predictions to force recalculation
            if game_id in self.prediction_cache:
                del self.prediction_cache[game_id]
            
            if game_id in self.last_predictions:
                del self.last_predictions[game_id]
                
        except Exception as e:
            logger.error(f"Error updating model features: {e}")