"""Unit tests for live value bet detection service."""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
from decimal import Decimal

from src.live_betting.value_bet_detector import (
    LiveValueBetDetector, ValueCalculator, EdgeFinder,
    BetRanker, RiskAssessor, ValueBetTracker,
    ArbitrageDetector
)
from src.models.live_schemas import (
    LiveOdds, LiveValueBet, LiveBetType, WinProbability,
    LiveGameState
)


class TestLiveValueBetDetector:
    """Test main LiveValueBetDetector class."""
    
    @pytest.fixture
    def detector(self):
        """Create value bet detector instance."""
        return LiveValueBetDetector()
    
    @pytest.fixture
    def sample_odds(self):
        """Create sample odds data."""
        return [
            LiveOdds(
                odds_id="1",
                game_id="game_1",
                bookmaker="BookA",
                bet_type=LiveBetType.MONEYLINE,
                selection="Lakers",
                odds=2.10,
                timestamp=datetime.utcnow()
            ),
            LiveOdds(
                odds_id="2",
                game_id="game_1",
                bookmaker="BookB",
                bet_type=LiveBetType.MONEYLINE,
                selection="Lakers",
                odds=2.05,
                timestamp=datetime.utcnow()
            ),
            LiveOdds(
                odds_id="3",
                game_id="game_1",
                bookmaker="BookA",
                bet_type=LiveBetType.MONEYLINE,
                selection="Celtics",
                odds=1.85,
                timestamp=datetime.utcnow()
            )
        ]
    
    @pytest.fixture
    def sample_probability(self):
        """Create sample win probability."""
        return WinProbability(
            game_id="game_1",
            home_win_probability=0.55,
            away_win_probability=0.45,
            timestamp=datetime.utcnow(),
            confidence=0.85
        )
    
    @pytest.mark.asyncio
    async def test_detect_value_bets(self, detector, sample_odds, sample_probability):
        """Test value bet detection."""
        game_state = Mock(
            game_id="game_1",
            home_team="Lakers",
            away_team="Celtics"
        )
        
        value_bets = await detector.detect_value_bets(
            sample_odds, sample_probability, game_state
        )
        
        assert len(value_bets) > 0
        assert all(isinstance(bet, LiveValueBet) for bet in value_bets)
        
        # Check for positive expected value
        positive_ev_bets = [bet for bet in value_bets if bet.expected_value > 0]
        assert len(positive_ev_bets) > 0
    
    @pytest.mark.asyncio
    async def test_edge_threshold(self, detector, sample_odds, sample_probability):
        """Test minimum edge threshold."""
        # Set high threshold
        detector.min_edge = 0.10  # 10% edge required
        
        value_bets = await detector.detect_value_bets(
            sample_odds, sample_probability, Mock(game_id="game_1")
        )
        
        # All detected bets should have significant edge
        assert all(bet.edge >= 0.10 for bet in value_bets)
    
    @pytest.mark.asyncio
    async def test_confidence_filtering(self, detector, sample_odds):
        """Test filtering by probability confidence."""
        # Low confidence probability
        low_conf_prob = WinProbability(
            game_id="game_1",
            home_win_probability=0.52,
            away_win_probability=0.48,
            timestamp=datetime.utcnow(),
            confidence=0.4  # Low confidence
        )
        
        detector.min_confidence = 0.7
        value_bets = await detector.detect_value_bets(
            sample_odds, low_conf_prob, Mock(game_id="game_1")
        )
        
        # Should not detect bets with low confidence
        assert len(value_bets) == 0


class TestValueCalculator:
    """Test value calculation logic."""
    
    @pytest.fixture
    def calculator(self):
        """Create value calculator instance."""
        return ValueCalculator()
    
    def test_calculate_expected_value(self, calculator):
        """Test expected value calculation."""
        # Positive EV scenario
        ev = calculator.calculate_expected_value(
            probability=0.55,
            decimal_odds=2.10
        )
        assert ev > 0
        assert abs(ev - 0.155) < 0.001  # (0.55 * 2.10) - 1 = 0.155
        
        # Negative EV scenario
        ev = calculator.calculate_expected_value(
            probability=0.40,
            decimal_odds=2.00
        )
        assert ev < 0
        assert abs(ev - (-0.20)) < 0.001  # (0.40 * 2.00) - 1 = -0.20
    
    def test_calculate_edge(self, calculator):
        """Test edge calculation."""
        edge = calculator.calculate_edge(
            true_probability=0.60,
            implied_probability=0.50  # 2.00 decimal odds
        )
        assert edge == 0.10  # 60% - 50% = 10% edge
        
        # No edge scenario
        edge = calculator.calculate_edge(
            true_probability=0.50,
            implied_probability=0.52
        )
        assert edge < 0
    
    def test_kelly_criterion(self, calculator):
        """Test Kelly criterion stake calculation."""
        kelly_fraction = calculator.calculate_kelly_fraction(
            probability=0.60,
            decimal_odds=2.00,
            kelly_multiplier=0.25  # Quarter Kelly
        )
        
        # Full Kelly would be 20%, Quarter Kelly = 5%
        assert abs(kelly_fraction - 0.05) < 0.001
        
        # Negative edge should return 0
        kelly_fraction = calculator.calculate_kelly_fraction(
            probability=0.45,
            decimal_odds=2.00
        )
        assert kelly_fraction == 0


class TestEdgeFinder:
    """Test edge finding algorithms."""
    
    @pytest.fixture
    def edge_finder(self):
        """Create edge finder instance."""
        return EdgeFinder()
    
    def test_find_market_inefficiency(self, edge_finder):
        """Test finding market inefficiencies."""
        odds_list = [
            Mock(bookmaker="A", odds=1.90, selection="Team1"),
            Mock(bookmaker="B", odds=1.95, selection="Team1"),
            Mock(bookmaker="C", odds=2.20, selection="Team1"),  # Outlier
            Mock(bookmaker="D", odds=1.92, selection="Team1")
        ]
        
        inefficiencies = edge_finder.find_market_inefficiencies(odds_list)
        assert len(inefficiencies) > 0
        assert any(i["bookmaker"] == "C" for i in inefficiencies)
    
    def test_compare_to_market_consensus(self, edge_finder):
        """Test comparison against market consensus."""
        market_odds = [1.90, 1.91, 1.92, 1.93, 1.95]
        outlier_odds = 2.15
        
        deviation = edge_finder.calculate_market_deviation(outlier_odds, market_odds)
        assert deviation > 0.10  # Significant deviation
        
        # Test normal odds
        normal_odds = 1.92
        deviation = edge_finder.calculate_market_deviation(normal_odds, market_odds)
        assert deviation < 0.02
    
    def test_sharp_bookmaker_comparison(self, edge_finder):
        """Test comparison against sharp bookmakers."""
        sharp_odds = {"Pinnacle": 1.91, "Betfair": 1.92}
        soft_odds = {"RecreationalBook": 2.05}
        
        with patch.object(edge_finder, 'sharp_bookmakers', ["Pinnacle", "Betfair"]):
            edge = edge_finder.compare_to_sharps(soft_odds, sharp_odds)
            assert edge > 0.05  # Significant edge vs sharps


class TestArbitrageDetector:
    """Test arbitrage opportunity detection."""
    
    @pytest.fixture
    def arb_detector(self):
        """Create arbitrage detector instance."""
        return ArbitrageDetector()
    
    def test_detect_two_way_arbitrage(self, arb_detector):
        """Test two-way arbitrage detection."""
        odds = [
            Mock(
                bookmaker="BookA",
                bet_type=LiveBetType.MONEYLINE,
                selection="Team1",
                odds=2.15
            ),
            Mock(
                bookmaker="BookB",
                bet_type=LiveBetType.MONEYLINE,
                selection="Team2",
                odds=2.10
            )
        ]
        
        arb = arb_detector.detect_arbitrage(odds, ["Team1", "Team2"])
        assert arb is not None
        assert arb["profit_margin"] > 0
        assert "stakes" in arb
        
        # Verify stakes sum to 100%
        total_stake = sum(arb["stakes"].values())
        assert abs(total_stake - 100) < 0.01
    
    def test_no_arbitrage_scenario(self, arb_detector):
        """Test scenario with no arbitrage."""
        odds = [
            Mock(
                bookmaker="BookA",
                bet_type=LiveBetType.MONEYLINE,
                selection="Team1",
                odds=1.91
            ),
            Mock(
                bookmaker="BookB",
                bet_type=LiveBetType.MONEYLINE,
                selection="Team2",
                odds=1.91
            )
        ]
        
        arb = arb_detector.detect_arbitrage(odds, ["Team1", "Team2"])
        assert arb is None
    
    def test_three_way_arbitrage(self, arb_detector):
        """Test three-way arbitrage (e.g., soccer with draw)."""
        odds = [
            Mock(bookmaker="A", selection="Home", odds=3.20),
            Mock(bookmaker="B", selection="Draw", odds=3.40),
            Mock(bookmaker="C", selection="Away", odds=3.30)
        ]
        
        arb = arb_detector.detect_arbitrage(odds, ["Home", "Draw", "Away"])
        # This specific example should show small arbitrage
        assert arb is not None
        assert arb["profit_margin"] > 0


class TestRiskAssessor:
    """Test risk assessment functionality."""
    
    @pytest.fixture
    def risk_assessor(self):
        """Create risk assessor instance."""
        return RiskAssessor()
    
    def test_assess_bet_risk(self, risk_assessor):
        """Test bet risk assessment."""
        value_bet = Mock(
            edge=0.05,  # 5% edge
            confidence=0.85,
            expected_value=0.10,
            odds=2.00,
            game_time_remaining=120  # 2 minutes
        )
        
        risk_score = risk_assessor.assess_bet_risk(value_bet)
        assert 0 <= risk_score <= 1
        assert risk_score < 0.5  # Should be relatively low risk
    
    def test_high_risk_scenarios(self, risk_assessor):
        """Test high risk bet identification."""
        # Low confidence, high odds bet
        risky_bet = Mock(
            edge=0.02,  # Small edge
            confidence=0.55,  # Low confidence
            expected_value=0.05,
            odds=5.00,  # High odds
            game_time_remaining=600  # Lots of time left
        )
        
        risk_score = risk_assessor.assess_bet_risk(risky_bet)
        assert risk_score > 0.7  # High risk
    
    def test_calculate_max_exposure(self, risk_assessor):
        """Test maximum exposure calculation."""
        bankroll = 10000
        risk_score = 0.3  # Low risk
        
        max_exposure = risk_assessor.calculate_max_exposure(
            bankroll, risk_score
        )
        assert max_exposure > 100  # Can risk more on low risk
        assert max_exposure < 1000  # But still conservative
        
        # High risk
        max_exposure = risk_assessor.calculate_max_exposure(
            bankroll, 0.8
        )
        assert max_exposure < 200  # Much lower for high risk


class TestBetRanker:
    """Test value bet ranking functionality."""
    
    @pytest.fixture
    def ranker(self):
        """Create bet ranker instance."""
        return BetRanker()
    
    def test_rank_value_bets(self, ranker):
        """Test ranking multiple value bets."""
        bets = [
            Mock(
                bet_id="1",
                edge=0.08,
                expected_value=0.15,
                confidence=0.90,
                kelly_fraction=0.04
            ),
            Mock(
                bet_id="2",
                edge=0.12,
                expected_value=0.20,
                confidence=0.85,
                kelly_fraction=0.06
            ),
            Mock(
                bet_id="3",
                edge=0.05,
                expected_value=0.08,
                confidence=0.95,
                kelly_fraction=0.02
            )
        ]
        
        ranked = ranker.rank_bets(bets)
        assert ranked[0].bet_id == "2"  # Highest EV and edge
        assert ranked[-1].bet_id == "3"  # Lowest EV and edge
    
    def test_filter_by_criteria(self, ranker):
        """Test filtering bets by criteria."""
        bets = [
            Mock(edge=0.03, expected_value=0.05, sport="NBA"),
            Mock(edge=0.08, expected_value=0.12, sport="NFL"),
            Mock(edge=0.06, expected_value=0.10, sport="NBA")
        ]
        
        # Filter by minimum edge
        filtered = ranker.filter_bets(bets, min_edge=0.05)
        assert len(filtered) == 2
        
        # Filter by sport
        filtered = ranker.filter_bets(bets, sport="NBA")
        assert len(filtered) == 2
        assert all(bet.sport == "NBA" for bet in filtered)