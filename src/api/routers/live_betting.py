"""Fixing the FastAPI error by using Pydantic models for response serialization in the live betting router."""
"""Live betting API endpoints."""
import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from datetime import datetime, timedelta

from src.api.dependencies import (
    get_db,
    get_cache,
    get_current_active_user,
    PaginationParams
)
from src.models.schemas import User
from src.models.database import LiveGame, LiveOddsUpdate, LiveEvent, LivePrediction
from src.models.live_schemas import (
    LiveGameState, LiveGameSummary, LiveOdds, LiveEvent as LiveEventSchema, LivePrediction as LivePredictionSchema,
    LiveValueBet, LiveSubscription, LiveDashboard, LiveBettingFeatures,
    EventPrediction, MomentumScore
)
from src.data_collection.cache_manager import CacheManager
from src.live_betting.probability_engine import LivePredictionEngine
from src.live_betting.odds_engine import LiveOddsEngine
from src.live_betting.event_detector import LiveEventDetector
from src.live_betting.data_ingestion import LiveDataPipeline
from src.live_betting.websocket_manager import LiveBettingWebSocketManager
from src.models.database import LiveEvent as LiveEventDB

logger = logging.getLogger(__name__)

router = APIRouter()

# Global instances (in production these would be singletons or injected)
live_prediction_engine = None
live_odds_engine = None
live_event_detector = None
live_data_pipeline = None
websocket_manager = None


async def get_live_prediction_engine(
    cache: CacheManager = Depends(get_cache)
) -> LivePredictionEngine:
    """Get live prediction engine instance."""
    global live_prediction_engine
    if live_prediction_engine is None:
        live_prediction_engine = LivePredictionEngine(cache)
        await live_prediction_engine.initialize()
    return live_prediction_engine


async def get_live_odds_engine(
    cache: CacheManager = Depends(get_cache)
) -> LiveOddsEngine:
    """Get live odds engine instance."""
    global live_odds_engine
    if live_odds_engine is None:
        live_odds_engine = LiveOddsEngine(cache)
    return live_odds_engine


async def get_live_event_detector(
    cache: CacheManager = Depends(get_cache)
) -> LiveEventDetector:
    """Get live event detector instance."""
    global live_event_detector
    if live_event_detector is None:
        live_event_detector = LiveEventDetector(cache)
    return live_event_detector


async def get_websocket_manager(
    cache: CacheManager = Depends(get_cache)
) -> LiveBettingWebSocketManager:
    """Get WebSocket manager instance."""
    global websocket_manager
    if websocket_manager is None:
        websocket_manager = LiveBettingWebSocketManager(cache)
    return websocket_manager


@router.get("/games/active", response_model=List[LiveGameSummary])
async def get_active_games(
    sport: Optional[str] = Query(None, description="Filter by sport"),
    cache: CacheManager = Depends(get_cache),
    current_user: User = Depends(get_current_active_user)
):
    """Get all currently active live games.

    Args:
        sport: Optional sport filter
        cache: Cache manager
        current_user: Authenticated user

    Returns:
        List of active live games
    """
    try:
        # Get active games from cache
        cache_pattern = f"live_game_state:*"
        if sport:
            cache_pattern = f"live_game_state:*:{sport}:*"

        cached_games = await cache.get_pattern(cache_pattern)

        active_games = []
        for game_data in cached_games or []:
            if isinstance(game_data, dict):
                game_state = LiveGameState(**game_data)

                if game_state.is_active and (not sport or game_state.sport == sport):
                    # Get value bets count for this game
                    value_bets = await cache.get(f"value_bets:{game_state.game_id}") or []

                    # Get last event
                    last_event_data = await cache.get(f"last_event:{game_state.game_id}")
                    last_event = last_event_data.get("description") if last_event_data else None

                    active_games.append(LiveGameSummary(
                        game_id=game_state.game_id,
                        sport=game_state.sport,
                        home_team=game_state.home_team,
                        away_team=game_state.away_team,
                        current_score=game_state.current_score,
                        game_clock=str(game_state.game_clock) if game_state.game_clock else None,
                        quarter_period=game_state.quarter_period,
                        is_active=game_state.is_active,
                        value_bets_count=len(value_bets),
                        last_event=last_event
                    ))

        return active_games

    except Exception as e:
        logger.error(f"Error fetching active games: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch active games")


@router.get("/games/{game_id}", response_model=LiveGameState)
async def get_game_state(
    game_id: str,
    cache: CacheManager = Depends(get_cache),
    current_user: User = Depends(get_current_active_user)
):
    """Get current state of a live game.

    Args:
        game_id: Game identifier
        cache: Cache manager
        current_user: Authenticated user

    Returns:
        Current game state
    """
    try:
        # Get game state from cache
        game_data = await cache.get(f"live_game_state:{game_id}")

        if not game_data:
            raise HTTPException(status_code=404, detail="Game not found")

        return LiveGameState(**game_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching game state: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch game state")


@router.get("/games/{game_id}/odds", response_model=List[LiveOdds])
async def get_live_odds(
    game_id: str,
    bet_type: Optional[str] = Query(None, description="Filter by bet type"),
    bookmaker: Optional[str] = Query(None, description="Filter by bookmaker"),
    cache: CacheManager = Depends(get_cache),
    current_user: User = Depends(get_current_active_user)
):
    """Get live odds for a game.

    Args:
        game_id: Game identifier
        bet_type: Optional bet type filter
        bookmaker: Optional bookmaker filter
        cache: Cache manager
        current_user: Authenticated user

    Returns:
        List of live odds
    """
    try:
        # Get odds from cache
        odds_data = await cache.get(f"live_odds:{game_id}")

        if not odds_data:
            return []

        odds_list = []
        for odds_item in odds_data:
            odds = LiveOdds(**odds_item)

            # Apply filters
            if bet_type and odds.bet_type.value != bet_type:
                continue
            if bookmaker and odds.bookmaker != bookmaker:
                continue

            odds_list.append(odds)

        return sorted(odds_list, key=lambda x: x.timestamp, reverse=True)

    except Exception as e:
        logger.error(f"Error fetching live odds: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch live odds")


@router.get("/games/{game_id}/predictions", response_model=LivePredictionSchema)
async def get_live_predictions(
    game_id: str,
    prediction_engine: LivePredictionEngine = Depends(get_live_prediction_engine),
    cache: CacheManager = Depends(get_cache),
    current_user: User = Depends(get_current_active_user)
):
    """Get live win probability predictions for a game.

    Args:
        game_id: Game identifier
        prediction_engine: Prediction engine
        cache: Cache manager
        current_user: Authenticated user

    Returns:
        Live prediction data
    """
    try:
        # Get cached prediction first
        cached_prediction = await cache.get(f"live_prediction:{game_id}")

        if cached_prediction:
            return LivePredictionSchema(**cached_prediction)

        # If no cached prediction, try to generate one
        game_data = await cache.get(f"live_game_state:{game_id}")
        if not game_data:
            raise HTTPException(status_code=404, detail="Game not found")

        game_state = LiveGameState(**game_data)

        # Get recent events
        events_data = await cache.get_pattern(f"live_event:{game_id}:*")
        recent_events = [LiveEventSchema(**event) for event in events_data or []]

        # Get momentum
        momentum_data = await cache.get(f"live_momentum:{game_id}")
        momentum = MomentumScore(**momentum_data) if momentum_data else None

        # Generate prediction
        prediction = await prediction_engine.predict_live_probabilities(
            game_state, recent_events, momentum
        )

        return prediction

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching live predictions: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch predictions")


@router.get("/games/{game_id}/events", response_model=List[LiveEventSchema])
async def get_live_events(
    game_id: str,
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    hours: int = Query(2, ge=1, le=24, description="Hours of history"),
    cache: CacheManager = Depends(get_cache),
    current_user: User = Depends(get_current_active_user)
):
    """Get live events for a game.

    Args:
        game_id: Game identifier
        event_type: Optional event type filter
        hours: Hours of event history
        cache: Cache manager
        current_user: Authenticated user

    Returns:
        List of live events
    """
    try:
        # Get events from cache
        events_data = await cache.get_pattern(f"live_event:{game_id}:*")

        if not events_data:
            return []

        # Filter by time
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)

        events = []
        for event_data in events_data:
            event = LiveEventSchema(**event_data)

            if event.timestamp >= cutoff_time:
                if not event_type or event.event_type.value == event_type:
                    events.append(event)

        return sorted(events, key=lambda x: x.timestamp, reverse=True)

    except Exception as e:
        logger.error(f"Error fetching live events: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch live events")


@router.get("/games/{game_id}/value-bets", response_model=List[LiveValueBet])
async def get_live_value_bets(
    game_id: str,
    min_edge: float = Query(0.02, ge=0.0, le=1.0, description="Minimum edge"),
    min_confidence: float = Query(0.6, ge=0.0, le=1.0, description="Minimum confidence"),
    cache: CacheManager = Depends(get_cache),
    current_user: User = Depends(get_current_active_user)
):
    """Get live value betting opportunities for a game.

    Args:
        game_id: Game identifier
        min_edge: Minimum edge threshold
        min_confidence: Minimum confidence threshold
        cache: Cache manager
        current_user: Authenticated user

    Returns:
        List of value betting opportunities
    """
    try:
        # Get value bets from cache
        value_bets_data = await cache.get(f"value_bets:{game_id}")

        if not value_bets_data:
            return []

        value_bets = []
        for bet_data in value_bets_data:
            bet = LiveValueBet(**bet_data)

            # Apply filters
            if bet.edge >= min_edge and bet.confidence >= min_confidence:
                # Check if bet is still active and not expired
                if bet.is_active and (not bet.expires_at or bet.expires_at > datetime.utcnow()):
                    value_bets.append(bet)

        return sorted(value_bets, key=lambda x: x.edge, reverse=True)

    except Exception as e:
        logger.error(f"Error fetching value bets: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch value bets")


@router.get("/games/{game_id}/next-events", response_model=List[EventPrediction])
async def predict_next_events(
    game_id: str,
    time_window: int = Query(5, ge=1, le=30, description="Prediction window in minutes"),
    prediction_engine: LivePredictionEngine = Depends(get_live_prediction_engine),
    cache: CacheManager = Depends(get_cache),
    current_user: User = Depends(get_current_active_user)
):
    """Predict likely next events in the game.

    Args:
        game_id: Game identifier
        time_window: Prediction time window
        prediction_engine: Prediction engine
        cache: Cache manager
        current_user: Authenticated user

    Returns:
        List of event predictions
    """
    try:
        # Get game state
        game_data = await cache.get(f"live_game_state:{game_id}")
        if not game_data:
            raise HTTPException(status_code=404, detail="Game not found")

        game_state = LiveGameState(**game_data)

        # Predict next events
        predictions = await prediction_engine.predict_next_event(game_state, time_window)

        return predictions

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error predicting next events: {e}")
        raise HTTPException(status_code=500, detail="Failed to predict events")


@router.post("/subscriptions")
async def create_subscription(
    subscription_type: str,
    target: str,
    min_edge_threshold: float = Query(0.02, ge=0.0, le=1.0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a live betting subscription.

    Args:
        subscription_type: Type of subscription (game, sport, team)
        target: Subscription target
        min_edge_threshold: Minimum edge threshold for alerts
        db: Database session
        current_user: Authenticated user

    Returns:
        Created subscription
    """
    try:
        from src.models.database import LiveSubscription as DBLiveSubscription

        # Create subscription
        db_subscription = DBLiveSubscription(
            user_id=current_user.id,
            subscription_type=subscription_type,
            subscription_target=target,
            min_edge_threshold=min_edge_threshold,
            is_active=True
        )

        db.add(db_subscription)
        await db.commit()
        await db.refresh(db_subscription)

        # Return response model
        subscription = LiveSubscription(
            id=str(db_subscription.id),
            user_id=current_user.id,
            subscription_type=subscription_type,
            subscription_target=target,
            min_edge_threshold=min_edge_threshold,
            is_active=True,
            created_at=db_subscription.created_at
        )

        logger.info(f"Created subscription {subscription.id} for user {current_user.id}")

        return subscription

    except Exception as e:
        logger.error(f"Error creating subscription: {e}")
        raise HTTPException(status_code=500, detail="Failed to create subscription")


@router.get("/subscriptions", response_model=List[LiveSubscription])
async def get_user_subscriptions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get user's live betting subscriptions.

    Args:
        db: Database session
        current_user: Authenticated user

    Returns:
        List of user subscriptions
    """
    try:
        from src.models.database import LiveSubscription as DBLiveSubscription

        # Query user subscriptions
        query = select(DBLiveSubscription).where(
            and_(
                DBLiveSubscription.user_id == current_user.id,
                DBLiveSubscription.is_active == True
            )
        )

        result = await db.execute(query)
        db_subscriptions = result.scalars().all()

        # Convert to response models
        subscriptions = []
        for db_sub in db_subscriptions:
            subscriptions.append(LiveSubscription(
                id=str(db_sub.id),
                user_id=current_user.id,
                subscription_type=db_sub.subscription_type,
                subscription_target=db_sub.subscription_target,
                min_edge_threshold=db_sub.min_edge_threshold,
                is_active=db_sub.is_active,
                created_at=db_sub.created_at
            ))

        return subscriptions

    except Exception as e:
        logger.error(f"Error fetching subscriptions: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch subscriptions")


@router.delete("/subscriptions/{subscription_id}")
async def delete_subscription(
    subscription_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete a live betting subscription.

    Args:
        subscription_id: Subscription ID
        db: Database session
        current_user: Authenticated user

    Returns:
        Success message
    """
    try:
        from src.models.database import LiveSubscription as DBLiveSubscription

        # Find subscription
        query = select(DBLiveSubscription).where(
            and_(
                DBLiveSubscription.id == subscription_id,
                DBLiveSubscription.user_id == current_user.id
            )
        )

        result = await db.execute(query)
        subscription = result.scalar_one_or_none()

        if not subscription:
            raise HTTPException(status_code=404, detail="Subscription not found")

        # Mark as inactive instead of deleting
        subscription.is_active = False
        await db.commit()

        logger.info(f"Deleted subscription {subscription_id} for user {current_user.id}")

        return {"status": "success", "message": "Subscription deleted"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting subscription: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete subscription")


@router.get("/dashboard", response_model=LiveDashboard)
async def get_live_dashboard(
    cache: CacheManager = Depends(get_cache),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get live betting dashboard data.

    Args:
        cache: Cache manager
        db: Database session
        current_user: Authenticated user

    Returns:
        Live betting dashboard data
    """
    try:
        # Get active games
        active_games_data = await cache.get_pattern("live_game_state:*")
        active_games = []

        for game_data in active_games_data or []:
            if isinstance(game_data, dict):
                game_state = LiveGameState(**game_data)
                if game_state.is_active:
                    value_bets = await cache.get(f"value_bets:{game_state.game_id}") or []
                    last_event_data = await cache.get(f"last_event:{game_state.game_id}")

                    active_games.append(LiveGameSummary(
                        game_id=game_state.game_id,
                        sport=game_state.sport,
                        home_team=game_state.home_team,
                        away_team=game_state.away_team,
                        current_score=game_state.current_score,
                        game_clock=str(game_state.game_clock) if game_state.game_clock else None,
                        quarter_period=game_state.quarter_period,
                        is_active=game_state.is_active,
                        value_bets_count=len(value_bets),
                        last_event=last_event_data.get("description") if last_event_data else None
                    ))

        # Get user subscriptions
        from src.models.database import LiveSubscription as DBLiveSubscription

        query = select(DBLiveSubscription).where(
            and_(
                DBLiveSubscription.user_id == current_user.id,
                DBLiveSubscription.is_active == True
            )
        )
        result = await db.execute(query)
        db_subscriptions = result.scalars().all()

        user_subscriptions = []
        for db_sub in db_subscriptions:
            user_subscriptions.append(LiveSubscription(
                id=str(db_sub.id),
                user_id=current_user.id,
                subscription_type=db_sub.subscription_type,
                subscription_target=db_sub.subscription_target,
                min_edge_threshold=db_sub.min_edge_threshold,
                is_active=db_sub.is_active,
                created_at=db_sub.created_at
            ))

        # Get recent value bets
        recent_value_bets = []
        for game in active_games:
            game_value_bets = await cache.get(f"value_bets:{game.game_id}") or []
            for bet_data in game_value_bets[:5]:  # Top 5 per game
                recent_value_bets.append(LiveValueBet(**bet_data))

        # Sort by edge and take top 10
        recent_value_bets = sorted(recent_value_bets, key=lambda x: x.edge, reverse=True)[:10]

        # Count live alerts (simplified)
        live_alerts_count = len(recent_value_bets)

        dashboard = LiveDashboard(
            active_games=active_games,
            user_subscriptions=user_subscriptions,
            recent_value_bets=recent_value_bets,
            live_alerts_count=live_alerts_count
        )

        return dashboard

    except Exception as e:
        logger.error(f"Error fetching dashboard: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch dashboard")


@router.get("/odds/best/{game_id}")
async def get_best_odds(
    game_id: str,
    bet_type: str,
    selection: str,
    odds_engine: LiveOddsEngine = Depends(get_live_odds_engine),
    current_user: User = Depends(get_current_active_user)
):
    """Get the best available odds for a specific bet.

    Args:
        game_id: Game identifier
        bet_type: Bet type
        selection: Bet selection
        odds_engine: Odds engine
        current_user: Authenticated user

    Returns:
        Best available odds
    """
    try:
        best_odds = await odds_engine.get_best_odds(game_id, bet_type, selection)

        if not best_odds:
            raise HTTPException(status_code=404, detail="No odds found for this selection")

        return best_odds

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting best odds: {e}")
        raise HTTPException(status_code=500, detail="Failed to get best odds")


@router.get("/odds/summary/{game_id}")
async def get_odds_summary(
    game_id: str,
    odds_engine: LiveOddsEngine = Depends(get_live_odds_engine),
    current_user: User = Depends(get_current_active_user)
):
    """Get comprehensive odds summary for a game.

    Args:
        game_id: Game identifier
        odds_engine: Odds engine
        current_user: Authenticated user

    Returns:
        Comprehensive odds summary
    """
    try:
        summary = await odds_engine.get_odds_summary(game_id)
        return summary

    except Exception as e:
        logger.error(f"Error getting odds summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to get odds summary")


@router.post("/refresh/{game_id}")
async def refresh_game_data(
    game_id: str,
    background_tasks: BackgroundTasks,
    cache: CacheManager = Depends(get_cache),
    current_user: User = Depends(get_current_active_user)
):
    """Manually refresh live data for a game.

    Args:
        game_id: Game identifier
        background_tasks: Background tasks
        cache: Cache manager
        current_user: Authenticated user

    Returns:
        Refresh status
    """
    try:
        # Clear cached data for this game
        patterns_to_clear = [
            f"live_game_state:{game_id}",
            f"live_odds:{game_id}:*",
            f"live_prediction:{game_id}",
            f"live_momentum:{game_id}",
            f"value_bets:{game_id}"
        ]

        cleared_count = 0
        for pattern in patterns_to_clear:
            if "*" in pattern:
                cleared = await cache.clear_pattern(pattern)
            else:
                cleared = await cache.delete(pattern)
            cleared_count += cleared

        # Schedule background refresh
        background_tasks.add_task(_refresh_game_data_background, game_id)

        return {
            "status": "success",
            "message": f"Refresh initiated for game {game_id}",
            "cache_cleared": cleared_count
        }

    except Exception as e:
        logger.error(f"Error refreshing game data: {e}")
        raise HTTPException(status_code=500, detail="Failed to refresh game data")


async def _refresh_game_data_background(game_id: str):
    """Background task to refresh game data."""
    try:
        # This would trigger data pipeline refresh
        logger.info(f"Background refresh started for game {game_id}")
        # Implementation would depend on specific data sources

    except Exception as e:
        logger.error(f"Error in background refresh: {e}")


@router.get("/health")
async def live_betting_health():
    """Health check for live betting services."""
    try:
        health_status = {
            "status": "healthy",
            "services": {
                "prediction_engine": "unknown",
                "odds_engine": "unknown", 
                "event_detector": "unknown",
                "websocket_manager": "unknown"
            },
            "timestamp": datetime.utcnow()
        }

        # Check each service
        global live_prediction_engine, live_odds_engine, live_event_detector, websocket_manager

        health_status["services"]["prediction_engine"] = "up" if live_prediction_engine else "down"
        health_status["services"]["odds_engine"] = "up" if live_odds_engine else "down"
        health_status["services"]["event_detector"] = "up" if live_event_detector else "down"
        health_status["services"]["websocket_manager"] = "up" if websocket_manager else "down"

        # Check if any services are down
        if "down" in health_status["services"].values():
            health_status["status"] = "degraded"

        return health_status

    except Exception as e:
        logger.error(f"Error checking live betting health: {e}")
        return {
            "status": "error", 
            "message": str(e),
            "timestamp": datetime.utcnow()
        }

@router.get("/games/{game_id}/game_events", response_model=List[LiveEventSchema])
async def get_game_events(
    game_id: str,
    limit: int = Query(50, le=100),
    db: AsyncSession = Depends(get_db)
) -> List[LiveEventSchema]:
    """Get live events for a specific game from the database."""
    # Get live events for the game
    result = await db.execute(
        select(LiveEventDB)
        .where(LiveEventDB.game_id == game_id)
        .order_by(LiveEventDB.timestamp.desc())
        .limit(limit)
    )
    events = result.scalars().all()

    # Convert database models to Pydantic schemas
    return [
        LiveEventSchema(
            id=event.id,
            game_id=event.game_id,
            event_type=event.event_type,
            description=event.description,
            timestamp=event.timestamp,
            impact_score=event.impact_score,
            event_data=event.event_data
        )
        for event in events
    ]