"""Unit tests for live probability calculation engine."""
import pytest
import numpy as np
import pandas as pd
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
import joblib

from src.live_betting.probability_engine import (
    LiveProbabilityEngine, GameStatePredictor, PlayerImpactModel,
    MomentumModel, TimeDecayModel, InjuryImpactModel,
    HistoricalPerformanceModel, LiveMLPredictor
)
from src.models.live_schemas import (
    LiveGameState, LiveEvent, LiveEventType, WinProbability
)


class TestLiveProbabilityEngine:
    """Test main LiveProbabilityEngine class."""
    
    @pytest.fixture
    def probability_engine(self):
        """Create probability engine instance."""
        return LiveProbabilityEngine()
    
    @pytest.fixture
    def sample_game_state(self):
        """Create sample game state."""
        return LiveGameState(
            game_id="test_game_1",
            sport="NBA",
            home_team="Lakers",
            away_team="Celtics",
            home_score=85,
            away_score=82,
            period=3,
            time_remaining="5:30",
            status="LIVE",
            start_time=datetime.utcnow() - timedelta(hours=1)
        )
    
    @pytest.mark.asyncio
    async def test_calculate_win_probability(self, probability_engine, sample_game_state):
        """Test win probability calculation."""
        prob = await probability_engine.calculate_win_probability(sample_game_state)
        
        assert isinstance(prob, WinProbability)
        assert prob.game_id == "test_game_1"
        assert 0 <= prob.home_win_probability <= 1
        assert 0 <= prob.away_win_probability <= 1
        assert abs(prob.home_win_probability + prob.away_win_probability - 1.0) < 0.01
        
        # Home team leading should have higher probability
        assert prob.home_win_probability > 0.5
    
    @pytest.mark.asyncio
    async def test_update_after_event(self, probability_engine, sample_game_state):
        """Test probability update after game event."""
        # Initial probability
        initial_prob = await probability_engine.calculate_win_probability(sample_game_state)
        
        # Simulate away team scoring event
        event = LiveEvent(
            event_id="evt_1",
            game_id="test_game_1",
            event_type=LiveEventType.SCORE,
            team="Celtics",
            player="Jayson Tatum",
            description="Made 3-pointer",
            timestamp=datetime.utcnow(),
            impact_score=3.5
        )
        
        # Update game state
        sample_game_state.away_score = 85  # Tie game
        
        updated_prob = await probability_engine.update_probability_after_event(
            sample_game_state, event
        )
        
        # Away team probability should increase after tying
        assert updated_prob.away_win_probability > initial_prob.away_win_probability
    
    @pytest.mark.asyncio
    async def test_historical_context_impact(self, probability_engine, sample_game_state):
        """Test impact of historical performance."""
        # Mock historical data showing home team dominance
        with patch.object(
            probability_engine.historical_model,
            'get_head_to_head_factor',
            return_value=1.15  # Home team has 15% historical advantage
        ):
            prob = await probability_engine.calculate_win_probability(sample_game_state)
            assert prob.home_win_probability > 0.6
    
    def test_probability_history_tracking(self, probability_engine):
        """Test probability history tracking."""
        game_id = "test_game"
        
        # Add probability updates
        for i in range(5):
            prob = WinProbability(
                game_id=game_id,
                home_win_probability=0.5 + i * 0.05,
                away_win_probability=0.5 - i * 0.05,
                timestamp=datetime.utcnow() + timedelta(minutes=i),
                confidence=0.85
            )
            probability_engine.add_to_history(prob)
        
        history = probability_engine.get_probability_history(game_id)
        assert len(history) == 5
        assert history[-1].home_win_probability == 0.70


class TestGameStatePredictor:
    """Test game state prediction model."""
    
    @pytest.fixture
    def predictor(self):
        """Create game state predictor."""
        return GameStatePredictor()
    
    def test_extract_features(self, predictor):
        """Test feature extraction from game state."""
        game_state = Mock(
            home_score=85,
            away_score=82,
            period=3,
            time_remaining="5:30",
            sport="NBA"
        )
        
        features = predictor.extract_features(game_state)
        
        assert features["score_differential"] == 3
        assert features["time_remaining_seconds"] == 330  # 5:30
        assert features["period"] == 3
        assert 0 < features["game_progress"] < 1
    
    def test_predict_win_probability(self, predictor):
        """Test win probability prediction."""
        features = {
            "score_differential": 5,
            "time_remaining_seconds": 120,
            "period": 4,
            "game_progress": 0.95,
            "scoring_rate": 2.5
        }
        
        with patch.object(predictor, 'model') as mock_model:
            mock_model.predict_proba.return_value = np.array([[0.3, 0.7]])
            
            prob = predictor.predict_win_probability(features)
            assert prob == 0.7
    
    def test_calculate_confidence(self, predictor):
        """Test prediction confidence calculation."""
        features = {
            "score_differential": 15,  # Large lead
            "time_remaining_seconds": 60,  # Little time
            "game_progress": 0.98
        }
        
        confidence = predictor.calculate_confidence(features)
        assert confidence > 0.9  # Should be very confident
        
        features["score_differential"] = 1  # Close game
        features["time_remaining_seconds"] = 600  # More time
        
        confidence = predictor.calculate_confidence(features)
        assert confidence < 0.7  # Less confident


class TestMomentumModel:
    """Test momentum impact model."""
    
    @pytest.fixture
    def momentum_model(self):
        """Create momentum model."""
        return MomentumModel()
    
    def test_calculate_momentum_factor(self, momentum_model):
        """Test momentum factor calculation."""
        recent_events = []
        
        # Add positive events for home team
        for i in range(5):
            recent_events.append(Mock(
                team="Lakers",
                event_type=LiveEventType.SCORE,
                impact_score=2.5,
                timestamp=datetime.utcnow() - timedelta(seconds=30*i)
            ))
        
        factor = momentum_model.calculate_momentum_factor(recent_events, "Lakers")
        assert factor > 1.0  # Positive momentum should increase probability
        
        # Add negative events
        for i in range(3):
            recent_events.append(Mock(
                team="Lakers",
                event_type=LiveEventType.TURNOVER,
                impact_score=-2.0,
                timestamp=datetime.utcnow() - timedelta(seconds=10*i)
            ))
        
        factor = momentum_model.calculate_momentum_factor(recent_events, "Lakers")
        assert factor < 1.0  # Momentum shifted negative
    
    def test_scoring_run_detection(self, momentum_model):
        """Test detection of scoring runs."""
        events = []
        
        # Create a 10-0 run
        for i in range(5):
            events.append(Mock(
                team="Celtics",
                event_type=LiveEventType.SCORE,
                impact_score=2.0,
                timestamp=datetime.utcnow() - timedelta(seconds=20*i)
            ))
        
        run_factor = momentum_model.detect_scoring_run(events, "Celtics")
        assert run_factor > 1.1  # Significant boost for scoring run


class TestTimeDecayModel:
    """Test time decay impact on probabilities."""
    
    @pytest.fixture
    def time_model(self):
        """Create time decay model."""
        return TimeDecayModel()
    
    def test_calculate_time_impact(self, time_model):
        """Test time impact calculation."""
        # Large lead with lots of time - less certain
        impact = time_model.calculate_time_impact(
            score_diff=15,
            time_remaining=600,  # 10 minutes
            period=3,
            sport="NBA"
        )
        assert 0.7 < impact < 0.9
        
        # Large lead with little time - more certain
        impact = time_model.calculate_time_impact(
            score_diff=15,
            time_remaining=30,  # 30 seconds
            period=4,
            sport="NBA"
        )
        assert impact > 0.95
        
        # Close game - time matters less
        impact = time_model.calculate_time_impact(
            score_diff=2,
            time_remaining=120,
            period=4,
            sport="NBA"
        )
        assert 0.5 < impact < 0.7
    
    def test_possession_calculation(self, time_model):
        """Test remaining possessions calculation."""
        possessions = time_model.calculate_remaining_possessions(
            time_remaining=240,  # 4 minutes
            sport="NBA"
        )
        assert 15 < possessions < 25  # Reasonable range for NBA
        
        possessions = time_model.calculate_remaining_possessions(
            time_remaining=180,  # 3 minutes
            sport="NFL"
        )
        assert 2 < possessions < 8  # Fewer possessions in NFL


class TestPlayerImpactModel:
    """Test player performance impact model."""
    
    @pytest.fixture
    def player_model(self):
        """Create player impact model."""
        return PlayerImpactModel()
    
    def test_calculate_player_impact(self, player_model):
        """Test player impact calculation."""
        player_stats = {
            "LeBron James": {
                "points": 28,
                "rebounds": 8,
                "assists": 10,
                "plus_minus": 12
            },
            "Anthony Davis": {
                "points": 22,
                "rebounds": 14,
                "assists": 3,
                "plus_minus": 8
            }
        }
        
        impact = player_model.calculate_team_impact(player_stats, "Lakers")
        assert impact > 1.0  # Strong performance should boost probability
    
    def test_injury_adjustment(self, player_model):
        """Test injury impact on team strength."""
        injuries = [
            {"player": "Star Player", "severity": "OUT", "impact_rating": 0.9}
        ]
        
        adjustment = player_model.adjust_for_injuries(injuries, "home")
        assert adjustment < 0.9  # Significant reduction for star player out
        
        injuries = [
            {"player": "Role Player", "severity": "QUESTIONABLE", "impact_rating": 0.3}
        ]
        
        adjustment = player_model.adjust_for_injuries(injuries, "home")
        assert 0.95 < adjustment < 1.0  # Minor impact


class TestLiveMLPredictor:
    """Test machine learning prediction integration."""
    
    @pytest.fixture
    def ml_predictor(self):
        """Create ML predictor."""
        return LiveMLPredictor()
    
    @pytest.mark.asyncio
    async def test_ensemble_prediction(self, ml_predictor):
        """Test ensemble model prediction."""
        game_state = Mock(
            home_score=90,
            away_score=85,
            period=4,
            time_remaining="3:00",
            sport="NBA"
        )
        
        with patch.object(ml_predictor, 'models') as mock_models:
            # Mock individual model predictions
            mock_models['gradient_boost'].predict_proba.return_value = [[0.3, 0.7]]
            mock_models['neural_net'].predict_proba.return_value = [[0.25, 0.75]]
            mock_models['random_forest'].predict_proba.return_value = [[0.35, 0.65]]
            
            prediction = await ml_predictor.predict_ensemble(game_state, {})
            
            # Should be weighted average
            assert 0.65 < prediction < 0.75
    
    def test_feature_engineering(self, ml_predictor):
        """Test feature engineering for ML models."""
        game_state = Mock(
            home_score=100,
            away_score=95,
            period=4,
            time_remaining="1:30",
            sport="NBA",
            home_team="Lakers",
            away_team="Celtics"
        )
        
        features = ml_predictor.engineer_features(game_state, {})
        
        assert "score_differential" in features
        assert "time_pressure" in features
        assert "scoring_pace" in features
        assert features["score_differential"] == 5
        assert features["time_pressure"] > 0.8  # High pressure late in game