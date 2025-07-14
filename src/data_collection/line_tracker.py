"""Track line movements and detect steam moves."""
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func

from src.models.database import OddsSnapshot
from src.models.schemas import MarketOdds, SportType
from src.data_collection.odds_aggregator import OddsAggregator

logger = logging.getLogger(__name__)


class LineMovement:
    """Represents a line movement for analysis."""
    
    def __init__(
        self,
        game_id: str,
        bookmaker: str,
        market_type: str,
        old_odds: float,
        new_odds: float,
        timestamp: datetime,
        movement_percent: float
    ):
        self.game_id = game_id
        self.bookmaker = bookmaker
        self.market_type = market_type
        self.old_odds = old_odds
        self.new_odds = new_odds
        self.timestamp = timestamp
        self.movement_percent = movement_percent
    
    @property
    def is_steam(self) -> bool:
        """Check if this is a steam move (>3% movement)."""
        return abs(self.movement_percent) > 3.0
    
    @property
    def direction(self) -> str:
        """Get movement direction."""
        if self.movement_percent > 0:
            return "up"
        elif self.movement_percent < 0:
            return "down"
        return "unchanged"


class LineTracker:
    """Tracks line movements and detects significant changes."""
    
    def __init__(
        self,
        odds_aggregator: OddsAggregator,
        steam_threshold: float = 3.0,
        time_window_minutes: int = 15
    ):
        """Initialize line tracker.
        
        Args:
            odds_aggregator: Odds aggregator instance
            steam_threshold: Percentage movement to consider steam
            time_window_minutes: Time window for movement analysis
        """
        self.odds_aggregator = odds_aggregator
        self.steam_threshold = steam_threshold
        self.time_window = timedelta(minutes=time_window_minutes)
    
    async def track_odds(
        self,
        session: AsyncSession,
        odds_list: List[MarketOdds]
    ) -> List[LineMovement]:
        """Track odds and detect line movements.
        
        Args:
            session: Database session
            odds_list: Current odds to track
            
        Returns:
            List of detected line movements
        """
        movements = []
        
        for market_odds in odds_list:
            # Store current snapshot
            await self._store_snapshot(session, market_odds)
            
            # Check for movements
            movement = await self._detect_movement(session, market_odds)
            if movement:
                movements.append(movement)
        
        await session.commit()
        
        # Log significant movements
        steam_moves = [m for m in movements if m.is_steam]
        if steam_moves:
            logger.info(f"Detected {len(steam_moves)} steam moves")
        
        return movements
    
    async def _store_snapshot(
        self,
        session: AsyncSession,
        market_odds: MarketOdds
    ) -> None:
        """Store odds snapshot in database.
        
        Args:
            session: Database session
            market_odds: Market odds to store
        """
        for bookmaker_odds in market_odds.bookmaker_odds:
            snapshot = OddsSnapshot(
                timestamp=datetime.utcnow(),
                game_id=market_odds.game_id,
                sport=market_odds.sport.value,
                bookmaker=bookmaker_odds.bookmaker,
                market_type=market_odds.bet_type.value,
                odds_data={
                    "home_team": market_odds.home_team,
                    "away_team": market_odds.away_team,
                    "commence_time": market_odds.commence_time.isoformat(),
                    "odds": bookmaker_odds.odds
                },
                home_team=market_odds.home_team,
                away_team=market_odds.away_team,
                commence_time=market_odds.commence_time,
                decimal_odds=bookmaker_odds.odds
            )
            session.add(snapshot)
    
    async def _detect_movement(
        self,
        session: AsyncSession,
        market_odds: MarketOdds
    ) -> Optional[LineMovement]:
        """Detect line movement for a market.
        
        Args:
            session: Database session
            market_odds: Current market odds
            
        Returns:
            LineMovement if significant movement detected
        """
        # Get best current odds
        best_current = market_odds.best_odds
        if not best_current:
            return None
        
        # Query previous odds within time window
        cutoff_time = datetime.utcnow() - self.time_window
        
        query = select(OddsSnapshot).where(
            and_(
                OddsSnapshot.game_id == market_odds.game_id,
                OddsSnapshot.market_type == market_odds.bet_type.value,
                OddsSnapshot.bookmaker == best_current.bookmaker,
                OddsSnapshot.timestamp >= cutoff_time
            )
        ).order_by(OddsSnapshot.timestamp.desc()).limit(1)
        
        result = await session.execute(query)
        previous_snapshot = result.scalar_one_or_none()
        
        if not previous_snapshot:
            return None
        
        # Calculate movement
        old_odds = previous_snapshot.decimal_odds
        new_odds = best_current.odds
        
        if old_odds == new_odds:
            return None
        
        movement_percent = ((new_odds - old_odds) / old_odds) * 100
        
        # Only track significant movements
        if abs(movement_percent) < 0.5:
            return None
        
        return LineMovement(
            game_id=market_odds.game_id,
            bookmaker=best_current.bookmaker,
            market_type=market_odds.bet_type.value,
            old_odds=old_odds,
            new_odds=new_odds,
            timestamp=datetime.utcnow(),
            movement_percent=movement_percent
        )
    
    async def get_line_history(
        self,
        session: AsyncSession,
        game_id: str,
        market_type: str,
        hours: int = 24
    ) -> List[Dict[str, Any]]:
        """Get line movement history for a game.
        
        Args:
            session: Database session
            game_id: Game identifier
            market_type: Market type
            hours: Number of hours of history
            
        Returns:
            List of line history data
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        query = select(OddsSnapshot).where(
            and_(
                OddsSnapshot.game_id == game_id,
                OddsSnapshot.market_type == market_type,
                OddsSnapshot.timestamp >= cutoff_time
            )
        ).order_by(OddsSnapshot.timestamp)
        
        result = await session.execute(query)
        snapshots = result.scalars().all()
        
        history = []
        for snapshot in snapshots:
            history.append({
                "timestamp": snapshot.timestamp,
                "bookmaker": snapshot.bookmaker,
                "odds": snapshot.decimal_odds,
                "home_team": snapshot.home_team,
                "away_team": snapshot.away_team
            })
        
        return history
    
    async def detect_reverse_line_movement(
        self,
        session: AsyncSession,
        game_id: str,
        public_betting_percentage: float
    ) -> bool:
        """Detect reverse line movement (line moves against public).
        
        Args:
            session: Database session
            game_id: Game identifier
            public_betting_percentage: Percentage of public on one side
            
        Returns:
            True if reverse line movement detected
        """
        # Get recent line movements
        movements = await self._get_recent_movements(session, game_id)
        
        if not movements:
            return False
        
        # Check if line moved against public money
        # If >70% public on one side but line moves other way
        if public_betting_percentage > 70:
            # Line should move down (worse odds) with public money
            # If it moves up, it's reverse line movement
            avg_movement = sum(m.movement_percent for m in movements) / len(movements)
            return avg_movement > 0.5
        
        return False
    
    async def _get_recent_movements(
        self,
        session: AsyncSession,
        game_id: str,
        hours: int = 2
    ) -> List[LineMovement]:
        """Get recent line movements for a game.
        
        Args:
            session: Database session
            game_id: Game identifier  
            hours: Hours to look back
            
        Returns:
            List of line movements
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        # Query for snapshots grouped by bookmaker
        query = select(
            OddsSnapshot.bookmaker,
            OddsSnapshot.market_type,
            func.min(OddsSnapshot.decimal_odds).label("min_odds"),
            func.max(OddsSnapshot.decimal_odds).label("max_odds"),
            func.min(OddsSnapshot.timestamp).label("first_seen"),
            func.max(OddsSnapshot.timestamp).label("last_seen")
        ).where(
            and_(
                OddsSnapshot.game_id == game_id,
                OddsSnapshot.timestamp >= cutoff_time
            )
        ).group_by(
            OddsSnapshot.bookmaker,
            OddsSnapshot.market_type
        )
        
        result = await session.execute(query)
        movements = []
        
        for row in result:
            if row.min_odds != row.max_odds:
                movement_percent = ((row.max_odds - row.min_odds) / row.min_odds) * 100
                movements.append(
                    LineMovement(
                        game_id=game_id,
                        bookmaker=row.bookmaker,
                        market_type=row.market_type,
                        old_odds=row.min_odds,
                        new_odds=row.max_odds,
                        timestamp=row.last_seen,
                        movement_percent=movement_percent
                    )
                )
        
        return movements