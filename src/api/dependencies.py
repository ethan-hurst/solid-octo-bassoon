"""Shared dependencies for FastAPI application."""
import logging
from typing import AsyncGenerator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from jose import JWTError, jwt
import redis.asyncio as redis

from src.config.settings import settings
from src.models.schemas import TokenData, User
from src.data_collection.cache_manager import CacheManager, cache_manager
from src.data_collection.odds_aggregator import OddsAggregator
from src.analysis.ml_models import SportsBettingModel, ModelEnsemble
from src.analysis.value_calculator import ValueCalculator
from src.alerts.redis_pubsub import RedisPubSubManager
from src.alerts.websocket_manager import ConnectionManager
from src.alerts.notification_service import NotificationService

logger = logging.getLogger(__name__)

# Security
security = HTTPBearer()

# Database
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    future=True
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Global instances
redis_pubsub_manager = RedisPubSubManager()
connection_manager = ConnectionManager(redis_pubsub_manager)
notification_service = NotificationService(connection_manager)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get database session.
    
    Yields:
        Database session
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def get_cache() -> CacheManager:
    """Get cache manager instance.
    
    Returns:
        Cache manager
    """
    return cache_manager


async def get_redis() -> redis.Redis:
    """Get Redis connection.
    
    Returns:
        Redis connection
    """
    return await redis.from_url(settings.redis_url)


def get_odds_aggregator(
    cache: CacheManager = Depends(get_cache)
) -> OddsAggregator:
    """Get odds aggregator instance.
    
    Args:
        cache: Cache manager
        
    Returns:
        Odds aggregator
    """
    return OddsAggregator(cache=cache)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Get current authenticated user.
    
    Args:
        credentials: JWT token credentials
        db: Database session
        
    Returns:
        Current user
        
    Raises:
        HTTPException: If authentication fails
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.secret_key,
            algorithms=[settings.algorithm]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
            
        token_data = TokenData(user_id=user_id)
        
    except JWTError:
        raise credentials_exception
    
    # Get user from database
    from src.models.database import User as DBUser
    from sqlalchemy import select
    
    result = await db.execute(
        select(DBUser).where(DBUser.id == token_data.user_id)
    )
    db_user = result.scalar_one_or_none()
    
    if db_user is None:
        raise credentials_exception
    
    # Convert to Pydantic model
    user = User(
        id=str(db_user.id),
        email=db_user.email,
        username=db_user.username,
        is_active=db_user.is_active,
        created_at=db_user.created_at,
        sports=db_user.sports or [],
        min_edge=db_user.min_edge,
        max_kelly_fraction=db_user.max_kelly_fraction,
        notification_channels=db_user.notification_channels or ["websocket"]
    )
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current active user.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Active user
        
    Raises:
        HTTPException: If user is inactive
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


def get_ml_ensemble() -> ModelEnsemble:
    """Get ML model ensemble.
    
    Returns:
        Model ensemble for predictions
    """
    # Load or create models
    from src.models.schemas import SportType
    
    models = {}
    for sport in SportType:
        model = SportsBettingModel(sport)
        # Models would be loaded from disk if available
        models[sport] = model
    
    return ModelEnsemble(models)


def get_value_calculator(
    ml_ensemble: ModelEnsemble = Depends(get_ml_ensemble)
) -> ValueCalculator:
    """Get value calculator instance.
    
    Args:
        ml_ensemble: ML model ensemble
        
    Returns:
        Value calculator
    """
    return ValueCalculator(ml_ensemble)


def get_pubsub_manager() -> RedisPubSubManager:
    """Get Redis pub/sub manager.
    
    Returns:
        Redis pub/sub manager
    """
    return redis_pubsub_manager


def get_connection_manager() -> ConnectionManager:
    """Get WebSocket connection manager.
    
    Returns:
        Connection manager
    """
    return connection_manager


def get_notification_service() -> NotificationService:
    """Get notification service.
    
    Returns:
        Notification service
    """
    return notification_service


# Pagination dependencies
class PaginationParams:
    """Common pagination parameters."""
    
    def __init__(
        self,
        skip: int = 0,
        limit: int = 100
    ):
        """Initialize pagination parameters.
        
        Args:
            skip: Number of items to skip
            limit: Maximum number of items to return
        """
        self.skip = skip
        self.limit = min(limit, 1000)  # Cap at 1000


# Filter dependencies
class OddsFilterParams:
    """Odds filtering parameters."""
    
    def __init__(
        self,
        sport: Optional[str] = None,
        min_edge: Optional[float] = None,
        min_odds: Optional[float] = None,
        max_odds: Optional[float] = None
    ):
        """Initialize filter parameters.
        
        Args:
            sport: Sport to filter by
            min_edge: Minimum edge percentage
            min_odds: Minimum odds value
            max_odds: Maximum odds value
        """
        self.sport = sport
        self.min_edge = min_edge
        self.min_odds = min_odds
        self.max_odds = max_odds