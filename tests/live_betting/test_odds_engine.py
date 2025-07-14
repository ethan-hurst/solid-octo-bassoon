"""Unit tests for live odds processing engine."""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
from decimal import Decimal
import numpy as np

from src.live_betting.odds_engine import (
    LiveOddsEngine, OddsCalculator, OddsAdjuster,
    MarketMaker, OddsCompiler, LiveOddsTracker
)
from src.models.live_schemas import (
    LiveOdds, LiveGameState, LiveBetType, LiveEvent,
    LiveEventType
)


class TestLiveOddsEngine:
    """Test main LiveOddsEngine class."""
    
    @pytest.fixture
    def odds_engine(self):
        """Create odds engine instance."""
        return LiveOddsEngine()
    
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
            start_time=datetime.utcnow() - timedelta(hours=1),
            home_win_probability=0.65
        )
    
    @pytest.mark.asyncio
    async def test_calculate_live_odds(self, odds_engine, sample_game_state):
        """Test live odds calculation."""
        odds = await odds_engine.calculate_live_odds(sample_game_state)
        
        assert len(odds) > 0
        moneyline_odds = [o for o in odds if o.bet_type == LiveBetType.MONEYLINE]
        assert len(moneyline_odds) == 2  # Home and away
        
        # Check odds are reasonable
        home_odds = next(o for o in moneyline_odds if o.selection == "Lakers")
        away_odds = next(o for o in moneyline_odds if o.selection == "Celtics")
        assert 1.0 < home_odds.odds < 3.0
        assert 1.0 < away_odds.odds < 5.0
    
    @pytest.mark.asyncio
    async def test_update_odds_after_event(self, odds_engine, sample_game_state):
        """Test odds update after game event."""
        # Initial odds
        initial_odds = await odds_engine.calculate_live_odds(sample_game_state)
        initial_home_odds = next(
            o.odds for o in initial_odds 
            if o.bet_type == LiveBetType.MONEYLINE and o.selection == "Lakers"
        )
        
        # Simulate scoring event for away team
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
        sample_game_state.home_win_probability = 0.50
        
        updated_odds = await odds_engine.update_odds_after_event(
            sample_game_state, event
        )
        
        updated_home_odds = next(
            o.odds for o in updated_odds
            if o.bet_type == LiveBetType.MONEYLINE and o.selection == "Lakers"
        )
        
        # Home odds should increase (become less favorable) after away team scores
        assert updated_home_odds > initial_home_odds
    
    @pytest.mark.asyncio
    async def test_calculate_prop_bet_odds(self, odds_engine, sample_game_state):
        """Test prop bet odds calculation."""
        player_stats = {
            "LeBron James": {"points": 22, "rebounds": 7, "assists": 8},
            "Anthony Davis": {"points": 28, "rebounds": 12, "assists": 3}
        }
        
        with patch.object(odds_engine.odds_calculator, 'get_player_stats',
                         return_value=player_stats):
            odds = await odds_engine.calculate_live_odds(sample_game_state)
            
            prop_odds = [o for o in odds if o.bet_type == LiveBetType.PLAYER_PROP]
            assert len(prop_odds) > 0
            
            # Check for specific prop bets
            lebron_points_odds = [
                o for o in prop_odds 
                if "LeBron James" in o.selection and "points" in o.selection.lower()
            ]
            assert len(lebron_points_odds) > 0


class TestOddsCalculator:
    """Test odds calculation logic."""
    
    @pytest.fixture
    def calculator(self):
        """Create odds calculator instance."""
        return OddsCalculator()
    
    def test_probability_to_decimal_odds(self, calculator):
        """Test probability to decimal odds conversion."""
        # 50% probability should give 2.0 odds
        assert calculator.probability_to_decimal_odds(0.5) == 2.0
        
        # 75% probability should give ~1.33 odds
        assert abs(calculator.probability_to_decimal_odds(0.75) - 1.33) < 0.01
        
        # Edge cases
        assert calculator.probability_to_decimal_odds(0.99) > 1.0
        assert calculator.probability_to_decimal_odds(0.01) < 100.0
    
    def test_calculate_moneyline_odds(self, calculator):
        """Test moneyline odds calculation."""
        odds = calculator.calculate_moneyline_odds(0.65, 0.35)
        
        assert "home" in odds
        assert "away" in odds
        assert odds["home"] < odds["away"]  # Favorite has lower odds
        
        # Check implied probabilities sum to ~100% (with vig)
        home_prob = 1 / odds["home"]
        away_prob = 1 / odds["away"]
        assert 1.0 < (home_prob + away_prob) < 1.10  # 0-10% vig
    
    def test_calculate_total_odds(self, calculator):
        """Test totals (over/under) odds calculation."""
        current_total = 167
        expected_final_total = 220
        time_remaining_factor = 0.4  # 40% of game remaining
        
        odds = calculator.calculate_total_odds(
            current_total, expected_final_total, time_remaining_factor
        )
        
        assert "over" in odds
        assert "under" in odds
        assert "line" in odds
        assert odds["line"] > current_total
        assert abs(odds["over"] - odds["under"]) < 0.2  # Should be close
    
    def test_calculate_spread_odds(self, calculator):
        """Test spread betting odds calculation."""
        odds = calculator.calculate_spread_odds(
            win_probability=0.7,
            current_margin=5,
            expected_margin=8
        )
        
        assert "spread" in odds
        assert "home_odds" in odds
        assert "away_odds" in odds
        assert odds["spread"] < 0  # Negative spread for favorite
        assert abs(odds["home_odds"] - 1.91) < 0.1  # Standard -110 odds


class TestOddsAdjuster:
    """Test odds adjustment logic."""
    
    @pytest.fixture
    def adjuster(self):
        """Create odds adjuster instance."""
        return OddsAdjuster()
    
    def test_apply_market_movement(self, adjuster):
        """Test market movement adjustments."""
        initial_odds = 1.85
        betting_volume = {"selection": 75, "opposite": 25}  # 75% on this selection
        
        adjusted = adjuster.apply_market_movement(initial_odds, betting_volume)
        assert adjusted < initial_odds  # Should shorten odds due to heavy action
    
    def test_apply_injury_adjustment(self, adjuster):
        """Test injury impact on odds."""
        initial_odds = 2.0
        
        # Star player injury
        adjusted = adjuster.apply_injury_adjustment(
            initial_odds, "LeBron James", "star", "home"
        )
        assert adjusted > initial_odds  # Home team odds should lengthen
        
        # Role player injury - less impact
        adjusted_role = adjuster.apply_injury_adjustment(
            initial_odds, "Bench Player", "role", "home"
        )
        assert adjusted_role > initial_odds
        assert adjusted_role < adjusted  # Less impact than star
    
    def test_apply_momentum_adjustment(self, adjuster):
        """Test momentum-based odds adjustment."""
        initial_odds = 2.0
        
        # Positive momentum
        adjusted = adjuster.apply_momentum_adjustment(initial_odds, 0.7)
        assert adjusted < initial_odds
        
        # Negative momentum
        adjusted = adjuster.apply_momentum_adjustment(initial_odds, -0.7)
        assert adjusted > initial_odds
        
        # Neutral momentum
        adjusted = adjuster.apply_momentum_adjustment(initial_odds, 0.1)
        assert abs(adjusted - initial_odds) < 0.05


class TestMarketMaker:
    """Test market making functionality."""
    
    @pytest.fixture
    def market_maker(self):
        """Create market maker instance."""
        return MarketMaker()
    
    def test_create_market(self, market_maker):
        """Test market creation."""
        market = market_maker.create_market(
            bet_type=LiveBetType.MONEYLINE,
            selections=["Lakers", "Celtics"],
            probabilities=[0.6, 0.4]
        )
        
        assert len(market) == 2
        assert all(isinstance(odds, LiveOdds) for odds in market)
        assert market[0].selection == "Lakers"
        assert market[1].selection == "Celtics"
    
    def test_balance_market(self, market_maker):
        """Test market balancing."""
        # Unbalanced market
        market = [
            Mock(odds=1.5, selection="Team A"),
            Mock(odds=3.0, selection="Team B")
        ]
        
        exposure = {"Team A": 10000, "Team B": 2000}  # Heavy on Team A
        
        balanced = market_maker.balance_market(market, exposure)
        assert balanced[0].odds < 1.5  # Team A odds should shorten
        assert balanced[1].odds > 3.0  # Team B odds should lengthen
    
    def test_calculate_market_margin(self, market_maker):
        """Test market margin calculation."""
        market = [
            Mock(odds=1.91),  # ~52.4% implied
            Mock(odds=1.91)   # ~52.4% implied
        ]
        
        margin = market_maker.calculate_market_margin(market)
        assert abs(margin - 0.048) < 0.001  # ~4.8% margin


class TestLiveOddsTracker:
    """Test odds tracking and history."""
    
    @pytest.fixture
    def tracker(self):
        """Create odds tracker instance."""
        return LiveOddsTracker()
    
    def test_track_odds_movement(self, tracker):
        """Test tracking odds movements."""
        # Add initial odds
        odds1 = LiveOdds(
            odds_id="1",
            game_id="game1",
            bookmaker="test",
            bet_type=LiveBetType.MONEYLINE,
            selection="Lakers",
            odds=1.85,
            timestamp=datetime.utcnow()
        )
        tracker.add_odds(odds1)
        
        # Add updated odds
        odds2 = LiveOdds(
            odds_id="2",
            game_id="game1",
            bookmaker="test",
            bet_type=LiveBetType.MONEYLINE,
            selection="Lakers",
            odds=1.75,
            timestamp=datetime.utcnow() + timedelta(minutes=5)
        )
        tracker.add_odds(odds2)
        
        history = tracker.get_odds_history("game1", LiveBetType.MONEYLINE, "Lakers")
        assert len(history) == 2
        assert history[0].odds == 1.85
        assert history[1].odds == 1.75
    
    def test_detect_significant_movement(self, tracker):
        """Test detection of significant odds movements."""
        # Add series of odds
        base_time = datetime.utcnow()
        for i, odds_value in enumerate([2.0, 1.95, 1.90, 1.70, 1.65]):
            odds = LiveOdds(
                odds_id=str(i),
                game_id="game1",
                bookmaker="test",
                bet_type=LiveBetType.MONEYLINE,
                selection="Team A",
                odds=odds_value,
                timestamp=base_time + timedelta(minutes=i)
            )
            tracker.add_odds(odds)
        
        movements = tracker.get_significant_movements("game1", threshold=0.1)
        assert len(movements) > 0
        assert any(m["change_percent"] > 10 for m in movements)
    
    def test_get_best_odds(self, tracker):
        """Test finding best odds across bookmakers."""
        # Add odds from multiple bookmakers
        for book, odds_value in [("BookA", 1.85), ("BookB", 1.90), ("BookC", 1.87)]:
            odds = LiveOdds(
                odds_id=f"{book}_1",
                game_id="game1",
                bookmaker=book,
                bet_type=LiveBetType.MONEYLINE,
                selection="Lakers",
                odds=odds_value,
                timestamp=datetime.utcnow()
            )
            tracker.add_odds(odds)
        
        best = tracker.get_best_odds("game1", LiveBetType.MONEYLINE, "Lakers")
        assert best.bookmaker == "BookB"
        assert best.odds == 1.90