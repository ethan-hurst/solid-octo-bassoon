"""Find arbitrage opportunities across sportsbooks."""
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import itertools

from src.models.schemas import MarketOdds, SportType, BetType

logger = logging.getLogger(__name__)


@dataclass
class ArbitrageOpportunity:
    """Represents an arbitrage betting opportunity."""
    game_id: str
    sport: SportType
    market_type: BetType
    home_team: str
    away_team: str
    bets: List[Dict[str, Any]]  # List of required bets
    total_stake: float
    guaranteed_profit: float
    profit_percentage: float
    bookmakers: List[str]


class ArbitrageFinder:
    """Finds arbitrage opportunities across multiple bookmakers."""
    
    def __init__(self, min_profit_percentage: float = 1.0):
        """Initialize arbitrage finder.
        
        Args:
            min_profit_percentage: Minimum profit % to consider
        """
        self.min_profit_percentage = min_profit_percentage
    
    def find_arbitrage_opportunities(
        self,
        odds_by_market: Dict[str, List[MarketOdds]]
    ) -> List[ArbitrageOpportunity]:
        """Find all arbitrage opportunities in current odds.
        
        Args:
            odds_by_market: Dictionary of market odds by game
            
        Returns:
            List of arbitrage opportunities
        """
        opportunities = []
        
        for game_id, market_list in odds_by_market.items():
            # Check each market type
            for market_type in BetType:
                market_odds = [m for m in market_list if m.bet_type == market_type]
                
                if not market_odds:
                    continue
                
                # Find arbitrage for this market
                arb = self._find_market_arbitrage(market_odds)
                
                if arb and arb.profit_percentage >= self.min_profit_percentage:
                    opportunities.append(arb)
        
        return opportunities
    
    def _find_market_arbitrage(
        self,
        market_odds_list: List[MarketOdds]
    ) -> Optional[ArbitrageOpportunity]:
        """Find arbitrage opportunity for a specific market.
        
        Args:
            market_odds_list: List of odds for same market
            
        Returns:
            ArbitrageOpportunity if found
        """
        if not market_odds_list:
            return None
        
        # Get reference market
        ref_market = market_odds_list[0]
        
        # Collect all odds by bookmaker
        bookmaker_odds = self._collect_bookmaker_odds(market_odds_list)
        
        if ref_market.bet_type == BetType.MONEYLINE:
            return self._find_two_way_arbitrage(
                ref_market, bookmaker_odds
            )
        elif ref_market.bet_type == BetType.SPREAD:
            return self._find_spread_arbitrage(
                ref_market, bookmaker_odds
            )
        elif ref_market.bet_type == BetType.TOTALS:
            return self._find_totals_arbitrage(
                ref_market, bookmaker_odds
            )
        
        return None
    
    def _collect_bookmaker_odds(
        self,
        market_odds_list: List[MarketOdds]
    ) -> Dict[str, Dict[str, float]]:
        """Collect odds by bookmaker and outcome.
        
        Args:
            market_odds_list: List of market odds
            
        Returns:
            Dict mapping bookmaker to outcome odds
        """
        bookmaker_odds = {}
        
        for market in market_odds_list:
            for bo in market.bookmaker_odds:
                if bo.bookmaker not in bookmaker_odds:
                    bookmaker_odds[bo.bookmaker] = {}
                
                # Simplified - assume home/away for now
                outcome = "home" if market.bet_type == BetType.MONEYLINE else "over"
                bookmaker_odds[bo.bookmaker][outcome] = bo.odds
        
        return bookmaker_odds
    
    def _find_two_way_arbitrage(
        self,
        market: MarketOdds,
        bookmaker_odds: Dict[str, Dict[str, float]]
    ) -> Optional[ArbitrageOpportunity]:
        """Find arbitrage for two-way markets (moneyline).
        
        Args:
            market: Reference market data
            bookmaker_odds: Odds by bookmaker
            
        Returns:
            ArbitrageOpportunity if found
        """
        best_home_odds = 0
        best_home_book = ""
        best_away_odds = 0
        best_away_book = ""
        
        # Find best odds for each outcome
        for bookmaker, odds in bookmaker_odds.items():
            home_odds = odds.get("home", 0)
            away_odds = odds.get("away", 0)
            
            if home_odds > best_home_odds:
                best_home_odds = home_odds
                best_home_book = bookmaker
            
            if away_odds > best_away_odds:
                best_away_odds = away_odds
                best_away_book = bookmaker
        
        if not (best_home_odds and best_away_odds):
            return None
        
        # Check for arbitrage
        total_implied = (1 / best_home_odds) + (1 / best_away_odds)
        
        if total_implied < 1.0:
            # Arbitrage exists!
            profit_percentage = ((1 / total_implied) - 1) * 100
            
            # Calculate stakes
            total_stake = 1000  # Standard stake
            home_stake = total_stake / (best_home_odds * total_implied)
            away_stake = total_stake / (best_away_odds * total_implied)
            
            guaranteed_profit = total_stake * (1 / total_implied - 1)
            
            return ArbitrageOpportunity(
                game_id=market.game_id,
                sport=market.sport,
                market_type=market.bet_type,
                home_team=market.home_team,
                away_team=market.away_team,
                bets=[
                    {
                        "bookmaker": best_home_book,
                        "outcome": "home",
                        "odds": best_home_odds,
                        "stake": round(home_stake, 2)
                    },
                    {
                        "bookmaker": best_away_book,
                        "outcome": "away", 
                        "odds": best_away_odds,
                        "stake": round(away_stake, 2)
                    }
                ],
                total_stake=total_stake,
                guaranteed_profit=round(guaranteed_profit, 2),
                profit_percentage=round(profit_percentage, 2),
                bookmakers=[best_home_book, best_away_book]
            )
        
        return None
    
    def _find_spread_arbitrage(
        self,
        market: MarketOdds,
        bookmaker_odds: Dict[str, Dict[str, float]]
    ) -> Optional[ArbitrageOpportunity]:
        """Find arbitrage for spread betting.
        
        Args:
            market: Reference market data
            bookmaker_odds: Odds by bookmaker
            
        Returns:
            ArbitrageOpportunity if found
        """
        # Similar to moneyline but with spreads
        # Need to ensure spreads are compatible
        # Implementation would check for middle opportunities
        
        return None  # Simplified for now
    
    def _find_totals_arbitrage(
        self,
        market: MarketOdds,
        bookmaker_odds: Dict[str, Dict[str, float]]
    ) -> Optional[ArbitrageOpportunity]:
        """Find arbitrage for totals (over/under).
        
        Args:
            market: Reference market data
            bookmaker_odds: Odds by bookmaker
            
        Returns:
            ArbitrageOpportunity if found
        """
        # Check for over/under arbitrage
        # Similar logic to two-way but with totals
        
        return None  # Simplified for now
    
    def find_synthetic_arbitrage(
        self,
        markets: List[MarketOdds],
        correlation_threshold: float = 0.8
    ) -> List[ArbitrageOpportunity]:
        """Find synthetic arbitrage using correlated events.
        
        Args:
            markets: All available markets
            correlation_threshold: Minimum correlation to consider
            
        Returns:
            List of synthetic arbitrage opportunities
        """
        synthetic_arbs = []
        
        # Find highly correlated games (e.g., same team playing)
        # This is simplified - would need correlation data
        
        return synthetic_arbs
    
    def calculate_arbitrage_profit(
        self,
        opportunity: ArbitrageOpportunity,
        actual_stake: float,
        execution_fees: float = 0
    ) -> Dict[str, float]:
        """Calculate actual profit from arbitrage.
        
        Args:
            opportunity: Arbitrage opportunity
            actual_stake: Actual total stake amount
            execution_fees: Transaction fees
            
        Returns:
            Dictionary with profit calculations
        """
        # Scale stakes proportionally
        scale_factor = actual_stake / opportunity.total_stake
        
        scaled_bets = []
        for bet in opportunity.bets:
            scaled_bets.append({
                **bet,
                "stake": bet["stake"] * scale_factor
            })
        
        # Calculate guaranteed return
        guaranteed_return = actual_stake / sum(1 / bet["odds"] for bet in opportunity.bets)
        
        # Subtract fees
        net_profit = guaranteed_return - actual_stake - execution_fees
        net_profit_percentage = (net_profit / actual_stake) * 100
        
        return {
            "total_stake": actual_stake,
            "guaranteed_return": guaranteed_return,
            "execution_fees": execution_fees,
            "net_profit": net_profit,
            "net_profit_percentage": net_profit_percentage,
            "scaled_bets": scaled_bets
        }
    
    def monitor_arbitrage_window(
        self,
        opportunity: ArbitrageOpportunity,
        current_odds: Dict[str, float],
        min_profit_threshold: float = 0.5
    ) -> bool:
        """Check if arbitrage opportunity still exists.
        
        Args:
            opportunity: Original arbitrage opportunity
            current_odds: Current odds for the bets
            min_profit_threshold: Minimum profit % to maintain
            
        Returns:
            True if opportunity still valid
        """
        # Recalculate with current odds
        total_implied = 0
        
        for bet in opportunity.bets:
            bet_key = f"{bet['bookmaker']}_{bet['outcome']}"
            current_odd = current_odds.get(bet_key)
            
            if not current_odd:
                # Odds no longer available
                return False
            
            total_implied += 1 / current_odd
        
        if total_implied >= 1.0:
            # No longer profitable
            return False
        
        current_profit = ((1 / total_implied) - 1) * 100
        
        return current_profit >= min_profit_threshold