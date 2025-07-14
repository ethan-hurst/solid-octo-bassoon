"""Backtesting framework for sports betting strategies."""
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable, Tuple
import pandas as pd
import numpy as np
from dataclasses import dataclass, field

from src.models.schemas import ValueBet, BacktestResult, SportType
from src.analysis.value_calculator import ValueCalculator

logger = logging.getLogger(__name__)


@dataclass
class BettingStrategy:
    """Defines a betting strategy for backtesting."""
    name: str
    min_edge: float = 0.05
    max_kelly_fraction: float = 0.25
    min_odds: float = 1.5
    max_odds: float = 10.0
    sports: List[SportType] = field(default_factory=list)
    bet_filter: Optional[Callable[[ValueBet], bool]] = None


@dataclass
class BacktestConfig:
    """Configuration for backtesting run."""
    initial_bankroll: float = 10000.0
    commission_rate: float = 0.0  # Some books charge commission
    max_bet_size: float = 1000.0
    min_bet_size: float = 10.0
    fractional_kelly: float = 0.25  # Use fraction of Kelly
    track_metrics: bool = True


class Backtester:
    """Backtests betting strategies on historical data."""
    
    def __init__(self, value_calculator: ValueCalculator):
        """Initialize backtester.
        
        Args:
            value_calculator: Value calculator for finding bets
        """
        self.value_calculator = value_calculator
    
    async def run_backtest(
        self,
        strategy: BettingStrategy,
        historical_odds: pd.DataFrame,
        historical_results: pd.DataFrame,
        config: BacktestConfig,
        start_date: datetime,
        end_date: datetime
    ) -> BacktestResult:
        """Run backtest for a strategy.
        
        Args:
            strategy: Betting strategy to test
            historical_odds: Historical odds data
            historical_results: Historical game results
            config: Backtest configuration
            start_date: Start date for backtest
            end_date: End date for backtest
            
        Returns:
            BacktestResult with performance metrics
        """
        logger.info(
            f"Running backtest for {strategy.name} "
            f"from {start_date} to {end_date}"
        )
        
        # Initialize tracking
        bankroll = config.initial_bankroll
        bets_placed = []
        daily_returns = []
        peak_bankroll = bankroll
        
        # Filter data by date range
        odds_data = historical_odds[
            (historical_odds["date"] >= start_date) &
            (historical_odds["date"] <= end_date)
        ].sort_values("date")
        
        # Process each day
        for date in pd.date_range(start_date, end_date):
            daily_odds = odds_data[odds_data["date"].dt.date == date.date()]
            
            if daily_odds.empty:
                continue
            
            # Find value bets for the day
            value_bets = await self._find_daily_value_bets(
                daily_odds, strategy
            )
            
            # Place bets
            daily_bets = []
            for value_bet in value_bets:
                bet_size = self._calculate_bet_size(
                    value_bet, bankroll, config
                )
                
                if bet_size >= config.min_bet_size:
                    bet_record = {
                        "date": date,
                        "game_id": value_bet.game_id,
                        "bet_size": bet_size,
                        "odds": value_bet.market.best_odds.odds,
                        "edge": value_bet.edge,
                        "kelly_fraction": value_bet.kelly_fraction,
                        "value_bet": value_bet
                    }
                    daily_bets.append(bet_record)
                    bets_placed.append(bet_record)
            
            # Settle bets from results
            daily_profit = await self._settle_bets(
                daily_bets, historical_results, config
            )
            
            # Update bankroll
            bankroll += daily_profit
            peak_bankroll = max(peak_bankroll, bankroll)
            
            # Track daily return
            daily_returns.append({
                "date": date,
                "bankroll": bankroll,
                "profit": daily_profit,
                "bets": len(daily_bets)
            })
        
        # Calculate metrics
        result = self._calculate_backtest_metrics(
            strategy,
            bets_placed,
            daily_returns,
            config.initial_bankroll,
            bankroll,
            peak_bankroll,
            start_date,
            end_date
        )
        
        return result
    
    async def _find_daily_value_bets(
        self,
        daily_odds: pd.DataFrame,
        strategy: BettingStrategy
    ) -> List[ValueBet]:
        """Find value bets for a single day.
        
        Args:
            daily_odds: Odds data for the day
            strategy: Betting strategy
            
        Returns:
            List of value bets
        """
        # Convert DataFrame to MarketOdds objects
        market_odds_list = self._dataframe_to_market_odds(daily_odds)
        
        # Find all value bets
        all_value_bets = await self.value_calculator.find_value_bets(
            market_odds_list
        )
        
        # Apply strategy filters
        filtered_bets = []
        for bet in all_value_bets:
            # Check edge threshold
            if bet.edge < strategy.min_edge:
                continue
            
            # Check odds range
            best_odds = bet.market.best_odds.odds
            if best_odds < strategy.min_odds or best_odds > strategy.max_odds:
                continue
            
            # Check sport filter
            if strategy.sports and bet.market.sport not in strategy.sports:
                continue
            
            # Apply custom filter if provided
            if strategy.bet_filter and not strategy.bet_filter(bet):
                continue
            
            filtered_bets.append(bet)
        
        return filtered_bets
    
    def _calculate_bet_size(
        self,
        value_bet: ValueBet,
        bankroll: float,
        config: BacktestConfig
    ) -> float:
        """Calculate bet size using Kelly criterion.
        
        Args:
            value_bet: Value bet to size
            bankroll: Current bankroll
            config: Backtest configuration
            
        Returns:
            Bet size in currency units
        """
        # Use fractional Kelly
        kelly_fraction = min(
            value_bet.kelly_fraction * config.fractional_kelly,
            config.max_kelly_fraction
        )
        
        # Calculate bet size
        bet_size = bankroll * kelly_fraction
        
        # Apply constraints
        bet_size = max(config.min_bet_size, min(config.max_bet_size, bet_size))
        
        # Don't bet more than current bankroll
        bet_size = min(bet_size, bankroll * 0.95)  # Keep 5% reserve
        
        return round(bet_size, 2)
    
    async def _settle_bets(
        self,
        bets: List[Dict[str, Any]],
        results: pd.DataFrame,
        config: BacktestConfig
    ) -> float:
        """Settle bets and calculate profit/loss.
        
        Args:
            bets: List of bets to settle
            results: Historical results data
            config: Backtest configuration
            
        Returns:
            Total profit/loss
        """
        total_profit = 0.0
        
        for bet in bets:
            game_id = bet["game_id"]
            
            # Find result
            game_result = results[results["game_id"] == game_id]
            
            if game_result.empty:
                logger.warning(f"No result found for game {game_id}")
                continue
            
            # Determine if bet won
            home_won = game_result.iloc[0]["home_score"] > game_result.iloc[0]["away_score"]
            bet_won = home_won  # Assuming we bet on home team
            
            if bet_won:
                # Calculate winnings
                gross_profit = bet["bet_size"] * (bet["odds"] - 1)
                commission = gross_profit * config.commission_rate
                net_profit = gross_profit - commission
            else:
                # Lost the bet
                net_profit = -bet["bet_size"]
            
            total_profit += net_profit
            
            # Update bet record
            bet["won"] = bet_won
            bet["profit"] = net_profit
        
        return total_profit
    
    def _calculate_backtest_metrics(
        self,
        strategy: BettingStrategy,
        bets_placed: List[Dict[str, Any]],
        daily_returns: List[Dict[str, Any]],
        initial_bankroll: float,
        final_bankroll: float,
        peak_bankroll: float,
        start_date: datetime,
        end_date: datetime
    ) -> BacktestResult:
        """Calculate comprehensive backtest metrics.
        
        Args:
            strategy: Strategy that was tested
            bets_placed: All bets placed
            daily_returns: Daily return data
            initial_bankroll: Starting bankroll
            final_bankroll: Ending bankroll
            peak_bankroll: Peak bankroll reached
            start_date: Backtest start date
            end_date: Backtest end date
            
        Returns:
            BacktestResult with all metrics
        """
        # Basic metrics
        total_bets = len(bets_placed)
        winning_bets = sum(1 for bet in bets_placed if bet.get("won", False))
        win_rate = winning_bets / total_bets if total_bets > 0 else 0
        
        # Profit metrics
        total_profit = final_bankroll - initial_bankroll
        roi = total_profit / initial_bankroll if initial_bankroll > 0 else 0
        
        # Calculate Sharpe ratio
        returns_df = pd.DataFrame(daily_returns)
        if not returns_df.empty and len(returns_df) > 1:
            daily_roi = returns_df["profit"] / returns_df["bankroll"].shift(1)
            daily_roi = daily_roi.dropna()
            
            if len(daily_roi) > 0 and daily_roi.std() > 0:
                sharpe_ratio = (daily_roi.mean() / daily_roi.std()) * np.sqrt(252)
            else:
                sharpe_ratio = 0.0
        else:
            sharpe_ratio = 0.0
        
        # Maximum drawdown
        max_drawdown = (peak_bankroll - final_bankroll) / peak_bankroll
        
        # Kelly performance
        kelly_performance = {
            "avg_kelly_bet": np.mean([b["kelly_fraction"] for b in bets_placed]) if bets_placed else 0,
            "avg_edge": np.mean([b["edge"] for b in bets_placed]) if bets_placed else 0,
            "avg_odds": np.mean([b["odds"] for b in bets_placed]) if bets_placed else 0
        }
        
        return BacktestResult(
            strategy_name=strategy.name,
            start_date=start_date,
            end_date=end_date,
            total_bets=total_bets,
            winning_bets=winning_bets,
            win_rate=win_rate,
            total_profit=total_profit,
            roi=roi,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown,
            kelly_performance=kelly_performance
        )
    
    def _dataframe_to_market_odds(
        self,
        df: pd.DataFrame
    ) -> List[MarketOdds]:
        """Convert DataFrame to MarketOdds objects.
        
        Args:
            df: DataFrame with odds data
            
        Returns:
            List of MarketOdds objects
        """
        # This is a simplified conversion - adjust based on actual data structure
        market_odds_list = []
        
        # Group by game
        for game_id, game_data in df.groupby("game_id"):
            # Extract game info from first row
            first_row = game_data.iloc[0]
            
            # Create MarketOdds object
            # This would need to be adapted to your actual data structure
            # market_odds = MarketOdds(...)
            # market_odds_list.append(market_odds)
        
        return market_odds_list
    
    def analyze_results(
        self,
        results: List[BacktestResult]
    ) -> pd.DataFrame:
        """Analyze multiple backtest results.
        
        Args:
            results: List of backtest results
            
        Returns:
            DataFrame with comparative analysis
        """
        data = []
        
        for result in results:
            data.append({
                "Strategy": result.strategy_name,
                "Total Bets": result.total_bets,
                "Win Rate": f"{result.win_rate:.2%}",
                "ROI": f"{result.roi:.2%}",
                "Sharpe Ratio": f"{result.sharpe_ratio:.2f}",
                "Max Drawdown": f"{result.max_drawdown:.2%}",
                "Avg Edge": f"{result.kelly_performance.get('avg_edge', 0):.2%}",
                "Profit": f"${result.total_profit:.2f}"
            })
        
        return pd.DataFrame(data)