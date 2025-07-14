"""Analysis API endpoints."""
import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta

from src.api.dependencies import (
    get_db,
    get_current_active_user,
    get_value_calculator,
    get_odds_aggregator,
    OddsFilterParams
)
from src.models.schemas import (
    User, SportType, ValueBet, BacktestResult,
    ArbitrageOpportunity
)
from src.analysis.value_calculator import ValueCalculator
from src.analysis.arbitrage_finder import ArbitrageFinder
from src.data_collection.odds_aggregator import OddsAggregator

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/value-bets", response_model=List[ValueBet])
async def find_value_bets(
    sport: SportType,
    min_edge: Optional[float] = Query(None, ge=0.0, le=1.0),
    min_confidence: Optional[float] = Query(None, ge=0.0, le=1.0),
    value_calculator: ValueCalculator = Depends(get_value_calculator),
    odds_aggregator: OddsAggregator = Depends(get_odds_aggregator),
    current_user: User = Depends(get_current_active_user)
):
    """Find current value betting opportunities.
    
    Args:
        sport: Sport to analyze
        min_edge: Minimum edge filter
        min_confidence: Minimum confidence filter
        value_calculator: Value calculator instance
        odds_aggregator: Odds aggregator instance
        current_user: Authenticated user
        
    Returns:
        List of value bets
    """
    try:
        # Fetch current odds
        odds_list = await odds_aggregator.fetch_odds(sport)
        
        # Find value bets
        value_bets = await value_calculator.find_value_bets(odds_list)
        
        # Apply filters
        if min_edge is not None:
            value_bets = [vb for vb in value_bets if vb.edge >= min_edge]
        
        if min_confidence is not None:
            value_bets = [vb for vb in value_bets if vb.confidence_score >= min_confidence]
        
        # Sort by edge descending
        value_bets.sort(key=lambda x: x.edge, reverse=True)
        
        return value_bets
        
    except Exception as e:
        logger.error(f"Error finding value bets: {e}")
        raise HTTPException(status_code=500, detail="Failed to find value bets")


@router.post("/arbitrage", response_model=List[ArbitrageOpportunity])
async def find_arbitrage(
    sports: Optional[str] = Query(None, description="Comma-separated sports"),
    min_profit: float = Query(1.0, ge=0.0, description="Minimum profit %"),
    odds_aggregator: OddsAggregator = Depends(get_odds_aggregator),
    current_user: User = Depends(get_current_active_user)
):
    """Find arbitrage opportunities across sportsbooks.
    
    Args:
        sports: Sports to check (defaults to user preferences)
        min_profit: Minimum profit percentage
        odds_aggregator: Odds aggregator instance
        current_user: Authenticated user
        
    Returns:
        List of arbitrage opportunities
    """
    try:
        # Parse sports
        if sports:
            sport_list = [SportType(s) for s in sports.split(",")]
        else:
            sport_list = current_user.sports or list(SportType)[:3]
        
        # Fetch odds for all sports
        all_odds = await odds_aggregator.fetch_all_sports_odds(sport_list)
        
        # Group by game
        odds_by_game = {}
        for sport, odds_list in all_odds.items():
            for market in odds_list:
                if market.game_id not in odds_by_game:
                    odds_by_game[market.game_id] = []
                odds_by_game[market.game_id].append(market)
        
        # Find arbitrage
        arbitrage_finder = ArbitrageFinder(min_profit_percentage=min_profit)
        opportunities = arbitrage_finder.find_arbitrage_opportunities(odds_by_game)
        
        return opportunities
        
    except Exception as e:
        logger.error(f"Error finding arbitrage: {e}")
        raise HTTPException(status_code=500, detail="Failed to find arbitrage")


@router.post("/backtest")
async def run_backtest(
    strategy_config: Dict[str, Any],
    start_date: datetime,
    end_date: datetime,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Run backtest on historical data.
    
    Args:
        strategy_config: Strategy configuration
        start_date: Backtest start date
        end_date: Backtest end date
        db: Database session
        current_user: Authenticated user
        
    Returns:
        Backtest results
    """
    try:
        # This would run the backtester with historical data
        # Simplified response for now
        
        return {
            "status": "completed",
            "strategy_name": strategy_config.get("name", "Custom"),
            "start_date": start_date,
            "end_date": end_date,
            "results": {
                "total_bets": 0,
                "winning_bets": 0,
                "win_rate": 0.0,
                "total_profit": 0.0,
                "roi": 0.0,
                "sharpe_ratio": 0.0,
                "max_drawdown": 0.0
            }
        }
        
    except Exception as e:
        logger.error(f"Error running backtest: {e}")
        raise HTTPException(status_code=500, detail="Failed to run backtest")


@router.get("/performance/summary")
async def get_performance_summary(
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get betting performance summary.
    
    Args:
        days: Number of days for analysis
        db: Database session
        current_user: Authenticated user
        
    Returns:
        Performance summary
    """
    try:
        # Query user's betting history
        from src.models.database import Bet
        from sqlalchemy import select, func
        import uuid
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Get betting statistics
        query = select(
            func.count(Bet.id).label("total_bets"),
            func.sum(Bet.profit).label("total_profit"),
            func.avg(Bet.profit).label("avg_profit"),
            func.sum(func.case((Bet.status == "won", 1), else_=0)).label("wins")
        ).where(
            Bet.user_id == uuid.UUID(current_user.id),
            Bet.placed_at >= cutoff_date,
            Bet.status.in_(["won", "lost"])
        )
        
        result = await db.execute(query)
        stats = result.one()
        
        # Calculate metrics
        total_bets = stats.total_bets or 0
        wins = stats.wins or 0
        total_profit = float(stats.total_profit or 0)
        
        win_rate = wins / total_bets if total_bets > 0 else 0
        
        # Get sport breakdown
        sport_query = select(
            Bet.sport,
            func.count(Bet.id).label("count"),
            func.sum(Bet.profit).label("profit")
        ).where(
            Bet.user_id == uuid.UUID(current_user.id),
            Bet.placed_at >= cutoff_date
        ).group_by(Bet.sport)
        
        sport_result = await db.execute(sport_query)
        sport_breakdown = [
            {
                "sport": row.sport,
                "bets": row.count,
                "profit": float(row.profit or 0)
            }
            for row in sport_result
        ]
        
        return {
            "period_days": days,
            "total_bets": total_bets,
            "winning_bets": wins,
            "win_rate": win_rate,
            "total_profit": total_profit,
            "average_profit_per_bet": total_profit / total_bets if total_bets > 0 else 0,
            "sport_breakdown": sport_breakdown
        }
        
    except Exception as e:
        logger.error(f"Error calculating performance: {e}")
        raise HTTPException(status_code=500, detail="Failed to calculate performance")


@router.post("/simulate-bet")
async def simulate_bet(
    value_bet: ValueBet,
    bankroll: float = Query(10000, gt=0),
    existing_exposure: float = Query(0, ge=0),
    value_calculator: ValueCalculator = Depends(get_value_calculator),
    current_user: User = Depends(get_current_active_user)
):
    """Simulate a bet with Kelly sizing.
    
    Args:
        value_bet: Value bet to simulate
        bankroll: Current bankroll
        existing_exposure: Existing exposure to this game
        value_calculator: Value calculator instance
        current_user: Authenticated user
        
    Returns:
        Bet simulation results
    """
    try:
        # Calculate recommended bet size
        bet_size = value_calculator.calculate_bet_size(
            value_bet,
            bankroll,
            existing_exposure
        )
        
        # Calculate potential outcomes
        potential_profit = bet_size * (value_bet.market.best_odds.odds - 1)
        potential_loss = bet_size
        
        # Expected value
        expected_profit = (
            value_bet.true_probability * potential_profit -
            (1 - value_bet.true_probability) * potential_loss
        )
        
        return {
            "recommended_bet_size": bet_size,
            "bet_percentage": bet_size / bankroll,
            "potential_profit": potential_profit,
            "potential_loss": potential_loss,
            "expected_profit": expected_profit,
            "expected_roi": expected_profit / bet_size if bet_size > 0 else 0,
            "break_even_probability": 1 / value_bet.market.best_odds.odds,
            "true_probability": value_bet.true_probability,
            "edge": value_bet.edge
        }
        
    except Exception as e:
        logger.error(f"Error simulating bet: {e}")
        raise HTTPException(status_code=500, detail="Failed to simulate bet")


@router.get("/models/performance")
async def get_model_performance(
    sport: Optional[SportType] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get ML model performance metrics.
    
    Args:
        sport: Filter by sport
        db: Database session
        current_user: Authenticated user
        
    Returns:
        Model performance data
    """
    try:
        # Query model performance
        from src.models.database import MLModel
        from sqlalchemy import select
        
        query = select(MLModel).where(MLModel.is_active == True)
        
        if sport:
            query = query.where(MLModel.sport == sport.value)
        
        result = await db.execute(query)
        models = result.scalars().all()
        
        # Format response
        performance_data = []
        for model in models:
            performance_data.append({
                "sport": model.sport,
                "model_type": model.model_type,
                "version": model.version,
                "accuracy": model.accuracy,
                "precision": model.precision,
                "recall": model.recall,
                "f1_score": model.f1_score,
                "trained_at": model.trained_at,
                "training_samples": model.training_samples
            })
        
        return {
            "models": performance_data,
            "last_updated": max(m.trained_at for m in models) if models else None
        }
        
    except Exception as e:
        logger.error(f"Error fetching model performance: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch model performance")