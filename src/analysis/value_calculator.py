"""Calculate value bets and expected value."""
import logging
from typing import List, Optional, Dict, Any
import numpy as np

from src.models.schemas import MarketOdds, ValueBet, SportType
from src.analysis.ml_models import MLPredictor, SportsBettingModel
from src.models.ml_features import FeatureEngineer
from src.config.settings import settings

logger = logging.getLogger(__name__)


class ValueCalculator:
    """Calculates value bets by comparing true probabilities to market odds."""
    
    def __init__(
        self,
        ml_predictor: MLPredictor,
        feature_engineer: Optional[FeatureEngineer] = None,
        min_edge: float = None,
        max_kelly_fraction: float = None
    ):
        """Initialize value calculator.
        
        Args:
            ml_predictor: ML model for probability predictions
            feature_engineer: Feature engineering instance
            min_edge: Minimum edge to consider value bet
            max_kelly_fraction: Maximum Kelly fraction to use
        """
        self.ml_predictor = ml_predictor
        self.feature_engineer = feature_engineer or FeatureEngineer()
        self.min_edge = min_edge or settings.alert_threshold_edge
        self.max_kelly_fraction = max_kelly_fraction or settings.max_kelly_fraction
    
    async def find_value_bets(
        self,
        odds_list: List[MarketOdds],
        historical_data: Optional[Dict[str, Any]] = None
    ) -> List[ValueBet]:
        """Find value betting opportunities from odds.
        
        Args:
            odds_list: List of market odds to analyze
            historical_data: Optional historical performance data
            
        Returns:
            List of detected value bets
        """
        value_bets = []
        
        for market_odds in odds_list:
            # Skip if no odds available
            if not market_odds.bookmaker_odds:
                continue
            
            # Extract features
            features = self._extract_features(market_odds, historical_data)
            
            if features is None:
                continue
            
            # Get ML prediction
            true_prob = await self.ml_predictor.predict_probability(features)
            
            # Get best available odds
            best_odds = market_odds.best_odds
            if not best_odds:
                continue
            
            implied_prob = market_odds.implied_probability
            if not implied_prob:
                continue
            
            # Calculate edge
            edge = true_prob - implied_prob
            
            # Check if this is a value bet
            if edge >= self.min_edge:
                # Calculate expected value
                ev = self._calculate_expected_value(
                    true_prob, best_odds.odds
                )
                
                # Calculate Kelly fraction
                kelly = self._calculate_kelly_fraction(
                    true_prob, best_odds.odds
                )
                
                # Calculate confidence score
                confidence = self._calculate_confidence(
                    edge, true_prob, market_odds
                )
                
                value_bet = ValueBet(
                    game_id=market_odds.game_id,
                    market=market_odds,
                    true_probability=true_prob,
                    implied_probability=implied_prob,
                    edge=edge,
                    expected_value=ev,
                    confidence_score=confidence,
                    kelly_fraction=min(kelly, self.max_kelly_fraction)
                )
                
                value_bets.append(value_bet)
                
                logger.info(
                    f"Value bet found: {market_odds.home_team} vs {market_odds.away_team}, "
                    f"Edge: {edge:.2%}, EV: {ev:.2%}, Kelly: {kelly:.2%}"
                )
        
        return value_bets
    
    def _extract_features(
        self,
        market_odds: MarketOdds,
        historical_data: Optional[Dict[str, Any]] = None
    ) -> Optional[np.ndarray]:
        """Extract features for ML prediction.
        
        Args:
            market_odds: Market odds data
            historical_data: Optional historical data
            
        Returns:
            Feature vector or None if extraction fails
        """
        try:
            # Get additional data if available
            weather_data = None
            injury_data = None
            
            if historical_data:
                weather_data = historical_data.get("weather")
                injury_data = historical_data.get("injuries")
            
            features = self.feature_engineer.extract_features(
                market_odds,
                historical_data=historical_data.get("performance") if historical_data else None,
                weather_data=weather_data,
                injury_data=injury_data
            )
            
            return features
            
        except Exception as e:
            logger.error(f"Feature extraction failed: {e}")
            return None
    
    def _calculate_expected_value(
        self,
        true_probability: float,
        decimal_odds: float
    ) -> float:
        """Calculate expected value of a bet.
        
        Args:
            true_probability: True probability of winning
            decimal_odds: Decimal odds offered
            
        Returns:
            Expected value as a percentage of stake
        """
        # EV = (true_prob * profit) - (lose_prob * loss)
        # For $1 bet: profit = (odds - 1), loss = 1
        ev = (true_probability * (decimal_odds - 1)) - ((1 - true_probability) * 1)
        
        return ev
    
    def _calculate_kelly_fraction(
        self,
        true_probability: float,
        decimal_odds: float
    ) -> float:
        """Calculate Kelly criterion bet fraction.
        
        Args:
            true_probability: True probability of winning
            decimal_odds: Decimal odds offered
            
        Returns:
            Kelly fraction (percentage of bankroll to bet)
        """
        # Kelly formula: f = (bp - q) / b
        # where b = decimal_odds - 1, p = true_prob, q = 1 - p
        b = decimal_odds - 1
        p = true_probability
        q = 1 - p
        
        # Calculate Kelly fraction
        kelly = (b * p - q) / b
        
        # Ensure non-negative
        return max(0, kelly)
    
    def _calculate_confidence(
        self,
        edge: float,
        true_probability: float,
        market_odds: MarketOdds
    ) -> float:
        """Calculate confidence score for a value bet.
        
        Args:
            edge: Betting edge
            true_probability: Model's predicted probability
            market_odds: Market odds data
            
        Returns:
            Confidence score between 0 and 1
        """
        # Base confidence from edge size
        edge_confidence = min(edge * 10, 1.0)  # Scale edge to confidence
        
        # Probability confidence (how far from 50/50)
        prob_confidence = abs(true_probability - 0.5) * 2
        
        # Market agreement (low variance = high confidence)
        if len(market_odds.bookmaker_odds) > 1:
            odds_values = [bo.odds for bo in market_odds.bookmaker_odds]
            odds_std = np.std(odds_values)
            avg_odds = np.mean(odds_values)
            market_efficiency = 1 - (odds_std / avg_odds) if avg_odds > 0 else 0
        else:
            market_efficiency = 0.5
        
        # Number of bookmakers (more = higher confidence)
        bookmaker_confidence = min(len(market_odds.bookmaker_odds) / 10, 1.0)
        
        # Weighted average
        confidence = (
            edge_confidence * 0.4 +
            prob_confidence * 0.3 +
            market_efficiency * 0.2 +
            bookmaker_confidence * 0.1
        )
        
        return min(confidence, 1.0)
    
    async def calculate_portfolio_kelly(
        self,
        value_bets: List[ValueBet],
        correlation_matrix: Optional[np.ndarray] = None
    ) -> Dict[str, float]:
        """Calculate Kelly fractions for a portfolio of bets.
        
        Args:
            value_bets: List of value bets
            correlation_matrix: Correlation between bets
            
        Returns:
            Dictionary mapping bet ID to Kelly fraction
        """
        if not value_bets:
            return {}
        
        # Simple independent Kelly if no correlation provided
        if correlation_matrix is None:
            return {
                bet.id: bet.kelly_fraction 
                for bet in value_bets
            }
        
        # Portfolio Kelly optimization
        n_bets = len(value_bets)
        
        # Extract parameters
        probs = np.array([bet.true_probability for bet in value_bets])
        odds = np.array([bet.market.best_odds.odds for bet in value_bets])
        
        # Expected returns
        returns = odds - 1
        
        # Covariance matrix (simplified - would need historical data)
        # For now, use correlation matrix with variance from win probabilities
        variances = probs * (1 - probs)
        cov_matrix = np.outer(variances, variances) * correlation_matrix
        
        # Solve portfolio optimization (simplified Kelly)
        # This is a quadratic programming problem in practice
        # For now, scale individual Kellys by diversification benefit
        
        # Diversification factor
        avg_correlation = (correlation_matrix.sum() - n_bets) / (n_bets * (n_bets - 1))
        div_factor = 1 / np.sqrt(1 + avg_correlation * (n_bets - 1))
        
        # Adjust Kelly fractions
        portfolio_kelly = {}
        for bet in value_bets:
            adjusted_kelly = bet.kelly_fraction * div_factor
            portfolio_kelly[bet.id] = min(adjusted_kelly, self.max_kelly_fraction)
        
        return portfolio_kelly
    
    def calculate_bet_size(
        self,
        value_bet: ValueBet,
        bankroll: float,
        existing_exposure: float = 0
    ) -> float:
        """Calculate recommended bet size.
        
        Args:
            value_bet: Value bet to size
            bankroll: Current bankroll
            existing_exposure: Existing exposure to this game
            
        Returns:
            Recommended bet size
        """
        # Use fractional Kelly
        kelly_fraction = value_bet.kelly_fraction
        
        # Adjust for confidence
        adjusted_kelly = kelly_fraction * value_bet.confidence_score
        
        # Calculate base bet size
        bet_size = bankroll * adjusted_kelly
        
        # Adjust for existing exposure
        if existing_exposure > 0:
            # Reduce bet size based on existing exposure
            exposure_ratio = existing_exposure / bankroll
            reduction_factor = max(0, 1 - exposure_ratio)
            bet_size *= reduction_factor
        
        # Apply minimum and maximum constraints
        min_bet = max(10, bankroll * 0.001)  # 0.1% minimum
        max_bet = bankroll * 0.05  # 5% maximum per bet
        
        bet_size = max(min_bet, min(max_bet, bet_size))
        
        # Round to reasonable amount
        if bet_size < 100:
            bet_size = round(bet_size, 0)
        else:
            bet_size = round(bet_size, -1)  # Round to nearest 10
        
        return bet_size