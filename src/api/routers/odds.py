"""Odds API endpoints."""
import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta

from src.api.dependencies import (
    get_db,
    get_odds_aggregator,
    get_current_active_user,
    PaginationParams,
    OddsFilterParams
)
from src.models.schemas import (
    User, SportType, MarketOdds, OddsResponse
)
from src.models.database import OddsSnapshot
from src.data_collection.odds_aggregator import OddsAggregator

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/sports", response_model=List[Dict[str, Any]])
async def get_available_sports(
    active_only: bool = Query(True, description="Only show active sports"),
    odds_aggregator: OddsAggregator = Depends(get_odds_aggregator),
    current_user: User = Depends(get_current_active_user)
):
    """Get list of available sports.
    
    Args:
        active_only: Filter for active sports only
        odds_aggregator: Odds aggregator instance
        current_user: Authenticated user
        
    Returns:
        List of available sports
    """
    try:
        sports = await odds_aggregator.get_sports(active_only)
        return sports
    except Exception as e:
        logger.error(f"Error fetching sports: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch sports")


@router.get("/{sport}", response_model=List[MarketOdds])
async def get_odds(
    sport: SportType,
    markets: Optional[str] = Query(None, description="Comma-separated market types"),
    regions: Optional[str] = Query(None, description="Comma-separated regions"),
    odds_aggregator: OddsAggregator = Depends(get_odds_aggregator),
    current_user: User = Depends(get_current_active_user)
):
    """Get current odds for a sport.
    
    Args:
        sport: Sport to get odds for
        markets: Market types (h2h, spreads, totals)
        regions: Bookmaker regions (us, uk, au, eu)
        odds_aggregator: Odds aggregator instance
        current_user: Authenticated user
        
    Returns:
        List of market odds
    """
    try:
        # Parse markets and regions
        market_list = markets.split(",") if markets else None
        region_list = regions.split(",") if regions else None
        
        # Fetch odds
        odds = await odds_aggregator.fetch_odds(
            sport=sport,
            markets=market_list,
            regions=region_list
        )
        
        return odds
        
    except Exception as e:
        logger.error(f"Error fetching odds for {sport}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch odds: {str(e)}"
        )


@router.get("/all/current", response_model=Dict[str, List[MarketOdds]])
async def get_all_current_odds(
    sports: Optional[str] = Query(None, description="Comma-separated sports"),
    markets: Optional[str] = Query(None, description="Comma-separated markets"),
    odds_aggregator: OddsAggregator = Depends(get_odds_aggregator),
    current_user: User = Depends(get_current_active_user)
):
    """Get current odds for multiple sports.
    
    Args:
        sports: Sports to fetch (defaults to user preferences)
        markets: Market types
        odds_aggregator: Odds aggregator instance
        current_user: Authenticated user
        
    Returns:
        Dictionary of sport -> odds
    """
    try:
        # Parse sports or use user preferences
        if sports:
            sport_list = [SportType(s) for s in sports.split(",")]
        else:
            sport_list = current_user.sports or list(SportType)[:3]  # Default to first 3
        
        market_list = markets.split(",") if markets else None
        
        # Fetch odds for all sports
        odds_by_sport = await odds_aggregator.fetch_all_sports_odds(
            sports=sport_list,
            markets=market_list
        )
        
        # Convert to response format
        response = {}
        for sport, odds in odds_by_sport.items():
            response[sport.value] = odds
        
        return response
        
    except Exception as e:
        logger.error(f"Error fetching all odds: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch odds")


@router.get("/history/{game_id}")
async def get_odds_history(
    game_id: str,
    hours: int = Query(24, ge=1, le=168, description="Hours of history"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get historical odds for a game.
    
    Args:
        game_id: Game identifier
        hours: Number of hours of history
        db: Database session
        current_user: Authenticated user
        
    Returns:
        Historical odds data
    """
    try:
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        # Query historical odds
        query = select(OddsSnapshot).where(
            OddsSnapshot.game_id == game_id,
            OddsSnapshot.timestamp >= cutoff_time
        ).order_by(OddsSnapshot.timestamp)
        
        result = await db.execute(query)
        snapshots = result.scalars().all()
        
        # Group by bookmaker
        history_by_bookmaker = {}
        for snapshot in snapshots:
            if snapshot.bookmaker not in history_by_bookmaker:
                history_by_bookmaker[snapshot.bookmaker] = []
            
            history_by_bookmaker[snapshot.bookmaker].append({
                "timestamp": snapshot.timestamp,
                "odds": snapshot.decimal_odds,
                "market_type": snapshot.market_type
            })
        
        return {
            "game_id": game_id,
            "period_hours": hours,
            "history": history_by_bookmaker
        }
        
    except Exception as e:
        logger.error(f"Error fetching odds history: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch history")


@router.get("/movements/significant")
async def get_significant_movements(
    sport: Optional[SportType] = None,
    min_movement: float = Query(3.0, description="Minimum % movement"),
    hours: int = Query(2, ge=1, le=24),
    db: AsyncSession = Depends(get_db),
    pagination: PaginationParams = Depends(),
    current_user: User = Depends(get_current_active_user)
):
    """Get significant line movements.
    
    Args:
        sport: Filter by sport
        min_movement: Minimum movement percentage
        hours: Time window
        db: Database session
        pagination: Pagination parameters
        current_user: Authenticated user
        
    Returns:
        List of significant movements
    """
    try:
        # This would use the LineTracker to find movements
        # Simplified for now
        
        return {
            "movements": [],
            "total": 0,
            "skip": pagination.skip,
            "limit": pagination.limit
        }
        
    except Exception as e:
        logger.error(f"Error fetching movements: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch movements")


@router.post("/refresh/{sport}")
async def refresh_odds(
    sport: SportType,
    odds_aggregator: OddsAggregator = Depends(get_odds_aggregator),
    current_user: User = Depends(get_current_active_user)
):
    """Manually refresh odds for a sport.
    
    Args:
        sport: Sport to refresh
        odds_aggregator: Odds aggregator instance
        current_user: Authenticated user
        
    Returns:
        Refresh status
    """
    try:
        # Clear cache for this sport
        from src.data_collection.cache_manager import cache_manager
        pattern = f"odds:{sport.value}:*"
        cleared = await cache_manager.clear_pattern(pattern)
        
        # Fetch fresh odds
        odds = await odds_aggregator.fetch_odds(sport)
        
        return {
            "status": "success",
            "sport": sport.value,
            "cache_cleared": cleared,
            "odds_fetched": len(odds)
        }
        
    except Exception as e:
        logger.error(f"Error refreshing odds: {e}")
        raise HTTPException(status_code=500, detail="Failed to refresh odds")