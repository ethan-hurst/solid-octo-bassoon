"""Unit tests for live event detection service."""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
import numpy as np

from src.live_betting.event_detector import (
    EventDetector, GameEventAnalyzer, MomentumDetector,
    PlayerPerformanceTracker, EventImpactCalculator,
    PatternRecognitionEngine
)
from src.models.live_schemas import (
    LiveGameState, LiveEvent, LiveEventType, ScoreUpdate
)


class TestEventDetector:
    """Test main EventDetector class."""
    
    @pytest.fixture
    def detector(self):
        """Create event detector instance."""
        return EventDetector()
    
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
    async def test_detect_scoring_run(self, detector):
        """Test detection of scoring runs."""
        # Simulate a scoring run
        events = []
        for i in range(5):
            events.append(LiveEvent(
                event_id=f"evt_{i}",
                game_id="game_1",
                event_type=LiveEventType.SCORE,
                team="Lakers",
                player="LeBron James",
                description="Made 3-pointer",
                timestamp=datetime.utcnow() - timedelta(seconds=30-i*5),
                impact_score=3.0
            ))
        
        detector.event_history["game_1"] = events
        detected = await detector.detect_events(Mock(game_id="game_1"))
        
        scoring_runs = [e for e in detected if "scoring run" in e.description.lower()]
        assert len(scoring_runs) > 0
    
    @pytest.mark.asyncio
    async def test_detect_momentum_shift(self, detector, sample_game_state):
        """Test momentum shift detection."""
        # Mock momentum detector to return high momentum
        with patch.object(detector.momentum_detector, 'calculate_momentum', 
                         return_value=0.85):
            events = await detector.detect_events(sample_game_state)
            momentum_events = [e for e in events 
                             if e.event_type == LiveEventType.MOMENTUM_SHIFT]
            assert len(momentum_events) > 0
    
    @pytest.mark.asyncio
    async def test_detect_key_player_performance(self, detector):
        """Test detection of key player performances."""
        # Add player events
        events = []
        for i in range(8):  # Player scores 24 points
            events.append(LiveEvent(
                event_id=f"evt_{i}",
                game_id="game_1",
                event_type=LiveEventType.SCORE,
                team="Lakers",
                player="Anthony Davis",
                description="Made shot",
                timestamp=datetime.utcnow() - timedelta(minutes=20-i),
                impact_score=2.5
            ))
        
        detector.event_history["game_1"] = events
        detected = await detector.detect_events(Mock(game_id="game_1"))
        
        player_events = [e for e in detected 
                        if "Anthony Davis" in e.description]
        assert len(player_events) > 0
    
    def test_analyze_event_impact(self, detector):
        """Test event impact analysis."""
        event = LiveEvent(
            event_id="evt_1",
            game_id="game_1",
            event_type=LiveEventType.SCORE,
            team="Lakers",
            player="LeBron James",
            description="Made 3-pointer",
            timestamp=datetime.utcnow(),
            impact_score=0.0
        )
        
        game_state = Mock(
            home_team="Lakers",
            away_team="Celtics",
            home_score=85,
            away_score=82,
            period=4,
            time_remaining="2:00"
        )
        
        impact = detector.analyze_event_impact(event, game_state)
        assert impact > 0  # Late game 3-pointer should have high impact


class TestMomentumDetector:
    """Test momentum detection functionality."""
    
    @pytest.fixture
    def momentum_detector(self):
        """Create momentum detector instance."""
        return MomentumDetector()
    
    def test_calculate_momentum_neutral(self, momentum_detector):
        """Test momentum calculation with neutral events."""
        events = [
            Mock(team="Lakers", event_type=LiveEventType.SCORE, 
                 timestamp=datetime.utcnow() - timedelta(seconds=i*30),
                 impact_score=2.0)
            for i in range(5)
        ] + [
            Mock(team="Celtics", event_type=LiveEventType.SCORE,
                 timestamp=datetime.utcnow() - timedelta(seconds=i*30),
                 impact_score=2.0)
            for i in range(5)
        ]
        
        momentum = momentum_detector.calculate_momentum(events, "Lakers")
        assert -0.1 < momentum < 0.1  # Should be near neutral
    
    def test_calculate_momentum_positive(self, momentum_detector):
        """Test momentum with positive team events."""
        events = [
            Mock(team="Lakers", event_type=LiveEventType.SCORE,
                 timestamp=datetime.utcnow() - timedelta(seconds=i*10),
                 impact_score=3.0)
            for i in range(8)
        ]
        
        momentum = momentum_detector.calculate_momentum(events, "Lakers")
        assert momentum > 0.5  # Strong positive momentum
    
    def test_detect_momentum_shift(self, momentum_detector):
        """Test momentum shift detection."""
        # Simulate momentum history
        history = [0.1, 0.2, 0.3, 0.5, 0.7, -0.2, -0.4, -0.6]
        
        shift = momentum_detector.detect_momentum_shift(history)
        assert shift is not None
        assert shift["from_team"] is not None
        assert shift["to_team"] is not None
        assert shift["magnitude"] > 0


class TestPlayerPerformanceTracker:
    """Test player performance tracking."""
    
    @pytest.fixture
    def tracker(self):
        """Create performance tracker instance."""
        return PlayerPerformanceTracker()
    
    def test_update_player_stats(self, tracker):
        """Test updating player statistics."""
        event = Mock(
            player="LeBron James",
            event_type=LiveEventType.SCORE,
            description="Made 3-pointer"
        )
        
        tracker.update_player_stats(event)
        
        stats = tracker.player_stats["LeBron James"]
        assert stats["points"] == 3
        assert stats["field_goals_made"] == 1
        assert stats["three_pointers_made"] == 1
    
    def test_detect_hot_player(self, tracker):
        """Test hot player detection."""
        # Simulate player making multiple shots
        for i in range(5):
            event = Mock(
                player="Stephen Curry",
                event_type=LiveEventType.SCORE,
                description="Made 3-pointer",
                timestamp=datetime.utcnow() - timedelta(seconds=i*30)
            )
            tracker.update_player_stats(event)
        
        hot_players = tracker.get_hot_players(min_points=10)
        assert "Stephen Curry" in [p["player"] for p in hot_players]
    
    def test_calculate_player_impact(self, tracker):
        """Test player impact calculation."""
        # Add various stats for a player
        events = [
            Mock(player="Giannis", event_type=LiveEventType.SCORE, 
                 description="Made 2-pointer"),
            Mock(player="Giannis", event_type=LiveEventType.REBOUND,
                 description="Defensive rebound"),
            Mock(player="Giannis", event_type=LiveEventType.ASSIST,
                 description="Assist"),
            Mock(player="Giannis", event_type=LiveEventType.BLOCK,
                 description="Block")
        ]
        
        for event in events:
            tracker.update_player_stats(event)
        
        impact = tracker.calculate_player_impact("Giannis")
        assert impact > 0  # Should have positive impact


class TestEventImpactCalculator:
    """Test event impact calculation."""
    
    @pytest.fixture
    def calculator(self):
        """Create impact calculator instance."""
        return EventImpactCalculator()
    
    def test_calculate_score_impact(self, calculator):
        """Test score event impact calculation."""
        event = Mock(
            event_type=LiveEventType.SCORE,
            description="Made 3-pointer"
        )
        
        game_context = {
            "score_differential": 2,
            "time_factor": 0.9,  # Late game
            "period": 4
        }
        
        impact = calculator.calculate_impact(event, game_context)
        assert impact > 3.0  # Close game, late 3-pointer = high impact
    
    def test_calculate_turnover_impact(self, calculator):
        """Test turnover impact calculation."""
        event = Mock(
            event_type=LiveEventType.TURNOVER,
            description="Turnover"
        )
        
        game_context = {
            "score_differential": 1,
            "time_factor": 0.95,  # Very late game
            "period": 4
        }
        
        impact = calculator.calculate_impact(event, game_context)
        assert impact > 4.0  # Late game turnover in close game = very high impact
    
    def test_time_factor_calculation(self, calculator):
        """Test time factor calculation for different game stages."""
        # Early game
        factor = calculator._calculate_time_factor(1, "10:00")
        assert factor < 0.3
        
        # Late game
        factor = calculator._calculate_time_factor(4, "2:00")
        assert factor > 0.8
        
        # Overtime
        factor = calculator._calculate_time_factor(5, "3:00")
        assert factor > 0.9


class TestPatternRecognitionEngine:
    """Test pattern recognition in game events."""
    
    @pytest.fixture
    def engine(self):
        """Create pattern recognition engine."""
        return PatternRecognitionEngine()
    
    def test_detect_comeback_pattern(self, engine):
        """Test comeback pattern detection."""
        # Simulate comeback scenario
        score_history = [
            {"home": 70, "away": 85, "time": "8:00"},
            {"home": 75, "away": 87, "time": "6:00"},
            {"home": 82, "away": 89, "time": "4:00"},
            {"home": 90, "away": 91, "time": "2:00"},
            {"home": 95, "away": 91, "time": "0:30"}
        ]
        
        patterns = engine.detect_patterns(score_history, [])
        comeback_patterns = [p for p in patterns if p["type"] == "comeback"]
        assert len(comeback_patterns) > 0
    
    def test_detect_defensive_battle(self, engine):
        """Test defensive battle pattern detection."""
        # Low scoring game
        score_history = [
            {"home": 15, "away": 12, "time": "8:00", "period": 1},
            {"home": 28, "away": 25, "time": "0:00", "period": 1},
            {"home": 40, "away": 38, "time": "6:00", "period": 2},
            {"home": 48, "away": 45, "time": "0:00", "period": 2}
        ]
        
        patterns = engine.detect_patterns(score_history, [])
        defensive_patterns = [p for p in patterns if p["type"] == "defensive_battle"]
        assert len(defensive_patterns) > 0
    
    def test_detect_blowout_pattern(self, engine):
        """Test blowout pattern detection."""
        # Large score differential
        score_history = [
            {"home": 35, "away": 18, "time": "0:00", "period": 1},
            {"home": 72, "away": 35, "time": "0:00", "period": 2},
            {"home": 105, "away": 52, "time": "0:00", "period": 3}
        ]
        
        patterns = engine.detect_patterns(score_history, [])
        blowout_patterns = [p for p in patterns if p["type"] == "blowout"]
        assert len(blowout_patterns) > 0