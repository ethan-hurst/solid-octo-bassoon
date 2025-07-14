"""Tests for value calculator."""
import pytest
from datetime import datetime, timedelta
import numpy as np

from src.analysis.value_calculator import ValueCalculator
from src.models.schemas import (
    MarketOdds, BookmakerOdds, SportType, BetType, ValueBet
)


@pytest.mark.asyncio
async def test_find_value_bets(mock_ml_predictor):
    """Test finding value bets from odds."""
    # Create test market odds
    market_odds = MarketOdds(
        game_id="test_game_1",
        sport=SportType.NFL,
        home_team="Team A",
        away_team="Team B",
        commence_time=datetime.utcnow() + timedelta(hours=24),
        bet_type=BetType.MONEYLINE,
        bookmaker_odds=[
            BookmakerOdds(
                bookmaker="DraftKings",
                odds=2.20,  # Implied prob: 0.4545
                last_update=datetime.utcnow()
            )
        ]
    )
    
    # ML predictor returns 0.55 probability (10% edge)
    mock_ml_predictor.predict_probability.return_value = 0.55
    
    calculator = ValueCalculator(mock_ml_predictor, min_edge=0.05)
    value_bets = await calculator.find_value_bets([market_odds])
    
    assert len(value_bets) == 1
    assert value_bets[0].edge > 0.09  # ~10% edge
    assert value_bets[0].expected_value > 0
    assert value_bets[0].kelly_fraction > 0


@pytest.mark.asyncio
async def test_no_value_bets_below_edge(mock_ml_predictor):
    """Test no value bets returned when edge below threshold."""
    market_odds = MarketOdds(
        game_id="test_game_2",
        sport=SportType.NBA,
        home_team="Team C",
        away_team="Team D",
        commence_time=datetime.utcnow() + timedelta(hours=12),
        bet_type=BetType.MONEYLINE,
        bookmaker_odds=[
            BookmakerOdds(
                bookmaker="FanDuel",
                odds=2.00,  # Implied prob: 0.50
                last_update=datetime.utcnow()
            )
        ]
    )
    
    # ML predictor returns 0.52 probability (2% edge)
    mock_ml_predictor.predict_probability.return_value = 0.52
    
    calculator = ValueCalculator(mock_ml_predictor, min_edge=0.05)
    value_bets = await calculator.find_value_bets([market_odds])
    
    assert len(value_bets) == 0


@pytest.mark.asyncio
async def test_expected_value_calculation():
    """Test expected value calculation."""
    from src.analysis.value_calculator import ValueCalculator
    
    calculator = ValueCalculator(None)  # Don't need ML for this test
    
    # Test cases
    test_cases = [
        (0.60, 2.00, 0.20),  # 60% prob, 2.00 odds = 20% EV
        (0.55, 1.91, 0.0005),  # 55% prob, 1.91 odds = ~0% EV
        (0.40, 3.00, 0.20),  # 40% prob, 3.00 odds = 20% EV
    ]
    
    for true_prob, odds, expected_ev in test_cases:
        ev = calculator._calculate_expected_value(true_prob, odds)
        assert abs(ev - expected_ev) < 0.01


@pytest.mark.asyncio
async def test_kelly_fraction_calculation():
    """Test Kelly criterion calculation."""
    from src.analysis.value_calculator import ValueCalculator
    
    calculator = ValueCalculator(None)
    
    # Test cases
    test_cases = [
        (0.60, 2.00, 0.20),  # 60% prob, 2.00 odds = 20% Kelly
        (0.55, 2.00, 0.10),  # 55% prob, 2.00 odds = 10% Kelly
        (0.45, 2.00, 0.00),  # 45% prob, 2.00 odds = 0% Kelly (no edge)
    ]
    
    for true_prob, odds, expected_kelly in test_cases:
        kelly = calculator._calculate_kelly_fraction(true_prob, odds)
        assert abs(kelly - expected_kelly) < 0.01


@pytest.mark.asyncio
async def test_confidence_score_calculation(mock_ml_predictor):
    """Test confidence score calculation."""
    # High confidence scenario - large edge, many bookmakers
    market_odds_high = MarketOdds(
        game_id="test_game_3",
        sport=SportType.NFL,
        home_team="Team E",
        away_team="Team F",
        commence_time=datetime.utcnow() + timedelta(hours=24),
        bet_type=BetType.MONEYLINE,
        bookmaker_odds=[
            BookmakerOdds(bookmaker=f"Book{i}", odds=2.20, last_update=datetime.utcnow())
            for i in range(10)  # 10 bookmakers
        ]
    )
    
    mock_ml_predictor.predict_probability.return_value = 0.60  # High edge
    
    calculator = ValueCalculator(mock_ml_predictor)
    value_bets = await calculator.find_value_bets([market_odds_high])
    
    assert len(value_bets) == 1
    assert value_bets[0].confidence_score > 0.7  # High confidence


@pytest.mark.asyncio
async def test_calculate_bet_size():
    """Test bet size calculation."""
    from src.analysis.value_calculator import ValueCalculator
    
    calculator = ValueCalculator(None, max_kelly_fraction=0.25)
    
    # Create test value bet
    value_bet = ValueBet(
        game_id="test_game",
        market=None,  # Not needed for this test
        true_probability=0.60,
        implied_probability=0.45,
        edge=0.15,
        expected_value=0.20,
        confidence_score=0.80,
        kelly_fraction=0.20
    )
    
    # Test bet sizing
    bankroll = 10000
    bet_size = calculator.calculate_bet_size(value_bet, bankroll)
    
    # Should be kelly * confidence * bankroll
    expected_size = 10000 * 0.20 * 0.80  # 1600
    assert 1500 <= bet_size <= 1700  # Allow for rounding
    
    # Test with existing exposure
    bet_size_with_exposure = calculator.calculate_bet_size(
        value_bet, bankroll, existing_exposure=5000
    )
    assert bet_size_with_exposure < bet_size  # Should be reduced


@pytest.mark.asyncio
async def test_portfolio_kelly_independent(test_value_bet):
    """Test portfolio Kelly calculation with independent bets."""
    from src.analysis.value_calculator import ValueCalculator
    
    calculator = ValueCalculator(None)
    
    # Create multiple value bets
    value_bets = [test_value_bet for _ in range(3)]
    
    # Calculate portfolio Kelly
    kelly_fractions = await calculator.calculate_portfolio_kelly(value_bets)
    
    assert len(kelly_fractions) == 3
    for bet_id, fraction in kelly_fractions.items():
        assert fraction > 0
        assert fraction <= calculator.max_kelly_fraction


@pytest.mark.asyncio
async def test_portfolio_kelly_correlated(test_value_bet):
    """Test portfolio Kelly with correlated bets."""
    from src.analysis.value_calculator import ValueCalculator
    
    calculator = ValueCalculator(None)
    
    # Create multiple value bets
    value_bets = [test_value_bet for _ in range(3)]
    
    # Create correlation matrix (high correlation)
    correlation_matrix = np.array([
        [1.0, 0.8, 0.8],
        [0.8, 1.0, 0.8],
        [0.8, 0.8, 1.0]
    ])
    
    # Calculate portfolio Kelly
    kelly_fractions = await calculator.calculate_portfolio_kelly(
        value_bets, correlation_matrix
    )
    
    # With high correlation, Kelly fractions should be reduced
    for bet_id, fraction in kelly_fractions.items():
        assert fraction < test_value_bet.kelly_fraction


@pytest.mark.asyncio
async def test_no_odds_available(mock_ml_predictor):
    """Test handling when no odds are available."""
    market_odds = MarketOdds(
        game_id="test_game_no_odds",
        sport=SportType.NFL,
        home_team="Team X",
        away_team="Team Y",
        commence_time=datetime.utcnow() + timedelta(hours=24),
        bet_type=BetType.MONEYLINE,
        bookmaker_odds=[]  # No odds
    )
    
    calculator = ValueCalculator(mock_ml_predictor)
    value_bets = await calculator.find_value_bets([market_odds])
    
    assert len(value_bets) == 0
    mock_ml_predictor.predict_probability.assert_not_called()