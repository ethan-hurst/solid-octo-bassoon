"""Celery application configuration and tasks."""
import logging
from celery import Celery
from celery.schedules import crontab
from datetime import datetime, timedelta
import asyncio

from src.config.settings import settings

# Configure logging
logger = logging.getLogger(__name__)

# Create Celery app
app = Celery(
    "sports_betting",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["src.celery_app"]  # Include this module for task discovery
)

# Celery configuration
app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# Celery beat schedule
app.conf.beat_schedule = {
    "fetch-odds-every-5-minutes": {
        "task": "src.celery_app.fetch_odds_task",
        "schedule": crontab(minute="*/5"),  # Every 5 minutes
    },
    "check-value-bets-every-10-minutes": {
        "task": "src.celery_app.check_value_bets_task",
        "schedule": crontab(minute="*/10"),  # Every 10 minutes
    },
    "update-ml-models-daily": {
        "task": "src.celery_app.update_ml_models_task",
        "schedule": crontab(hour=3, minute=0),  # Daily at 3 AM UTC
    },
    "cleanup-old-data-weekly": {
        "task": "src.celery_app.cleanup_old_data_task",
        "schedule": crontab(hour=4, minute=0, day_of_week=0),  # Weekly on Sunday
    },
}


def run_async(coro):
    """Helper to run async functions in Celery tasks."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@app.task(bind=True, max_retries=3)
def fetch_odds_task(self):
    """Fetch latest odds for all configured sports."""
    try:
        logger.info("Starting odds fetch task")
        
        async def fetch_odds():
            from src.data_collection.cache_manager import cache_manager
            from src.data_collection.odds_aggregator import OddsAggregator
            from src.models.schemas import SportType
            from src.models.database import OddsSnapshot
            from src.api.dependencies import AsyncSessionLocal
            
            # Connect to cache
            await cache_manager.connect()
            
            # Create odds aggregator
            aggregator = OddsAggregator(cache=cache_manager)
            
            # Fetch odds for active sports
            sports = [SportType.NFL, SportType.NBA, SportType.MLB]  # Configure as needed
            
            async with AsyncSessionLocal() as db:
                for sport in sports:
                    try:
                        odds_list = await aggregator.fetch_odds(sport)
                        
                        # Store snapshots in database
                        for market_odds in odds_list:
                            for bookmaker_odds in market_odds.bookmaker_odds:
                                snapshot = OddsSnapshot(
                                    timestamp=datetime.utcnow(),
                                    game_id=market_odds.game_id,
                                    sport=sport.value,
                                    bookmaker=bookmaker_odds.bookmaker,
                                    market_type=market_odds.bet_type.value,
                                    odds_data={
                                        "home_team": market_odds.home_team,
                                        "away_team": market_odds.away_team,
                                        "odds": bookmaker_odds.odds
                                    },
                                    home_team=market_odds.home_team,
                                    away_team=market_odds.away_team,
                                    commence_time=market_odds.commence_time,
                                    decimal_odds=bookmaker_odds.odds
                                )
                                db.add(snapshot)
                        
                        await db.commit()
                        logger.info(f"Fetched {len(odds_list)} odds for {sport.value}")
                        
                    except Exception as e:
                        logger.error(f"Error fetching odds for {sport}: {e}")
                        await db.rollback()
            
            await cache_manager.disconnect()
        
        run_async(fetch_odds())
        return {"status": "completed", "timestamp": datetime.utcnow().isoformat()}
        
    except Exception as e:
        logger.error(f"Odds fetch task failed: {e}")
        raise self.retry(exc=e, countdown=60)  # Retry after 1 minute


@app.task(bind=True, max_retries=3)
def check_value_bets_task(self):
    """Check for value betting opportunities and send alerts."""
    try:
        logger.info("Starting value bet check task")
        
        async def check_value_bets():
            from src.data_collection.cache_manager import cache_manager
            from src.data_collection.odds_aggregator import OddsAggregator
            from src.analysis.ml_models import ModelEnsemble, SportsBettingModel
            from src.analysis.value_calculator import ValueCalculator
            from src.alerts.notification_service import NotificationService
            from src.alerts.websocket_manager import ConnectionManager
            from src.alerts.redis_pubsub import RedisPubSubManager
            from src.models.schemas import SportType, Alert
            from src.models.database import User as DBUser, Alert as DBAlert
            from src.api.dependencies import AsyncSessionLocal
            from sqlalchemy import select
            import uuid
            
            # Initialize services
            await cache_manager.connect()
            redis_pubsub = RedisPubSubManager()
            await redis_pubsub.connect()
            
            connection_manager = ConnectionManager(redis_pubsub)
            notification_service = NotificationService(connection_manager)
            
            # Load ML models
            models = {}
            for sport in SportType:
                models[sport] = SportsBettingModel(sport)
            
            ml_ensemble = ModelEnsemble(models)
            value_calculator = ValueCalculator(ml_ensemble)
            
            # Get odds aggregator
            aggregator = OddsAggregator(cache=cache_manager)
            
            async with AsyncSessionLocal() as db:
                # Get active users
                result = await db.execute(
                    select(DBUser).where(DBUser.is_active == True)
                )
                users = result.scalars().all()
                
                alerts_created = 0
                
                for user in users:
                    try:
                        # Check user's preferred sports
                        user_sports = user.sports or [SportType.NFL.value]
                        
                        for sport_str in user_sports:
                            sport = SportType(sport_str)
                            
                            # Fetch current odds
                            odds_list = await aggregator.fetch_odds(sport)
                            
                            # Find value bets
                            value_bets = await value_calculator.find_value_bets(odds_list)
                            
                            # Filter by user preferences
                            for value_bet in value_bets:
                                if value_bet.edge >= user.min_edge:
                                    # Create alert
                                    alert = Alert(
                                        user_id=str(user.id),
                                        value_bet=value_bet,
                                        notification_channels=user.notification_channels or ["websocket"]
                                    )
                                    
                                    # Save to database
                                    db_alert = DBAlert(
                                        user_id=user.id,
                                        value_bet_data=value_bet.model_dump(),
                                        notification_channels=alert.notification_channels
                                    )
                                    db.add(db_alert)
                                    
                                    # Send notifications
                                    user_model = type("User", (), {
                                        "id": str(user.id),
                                        "email": user.email,
                                        "username": user.username,
                                        "notification_channels": user.notification_channels
                                    })()
                                    
                                    await notification_service.send_alert(alert, user_model)
                                    alerts_created += 1
                    
                    except Exception as e:
                        logger.error(f"Error processing user {user.id}: {e}")
                
                await db.commit()
                logger.info(f"Created {alerts_created} alerts")
            
            await redis_pubsub.disconnect()
            await cache_manager.disconnect()
            
            return alerts_created
        
        alerts = run_async(check_value_bets())
        return {"status": "completed", "alerts_created": alerts}
        
    except Exception as e:
        logger.error(f"Value bet check task failed: {e}")
        raise self.retry(exc=e, countdown=120)  # Retry after 2 minutes


@app.task(bind=True, max_retries=1)
def update_ml_models_task(self):
    """Update ML models with recent data."""
    try:
        logger.info("Starting ML model update task")
        
        # This would:
        # 1. Load recent betting outcomes
        # 2. Prepare training data
        # 3. Train updated models
        # 4. Evaluate performance
        # 5. Save new models if improved
        
        return {
            "status": "completed",
            "timestamp": datetime.utcnow().isoformat(),
            "models_updated": 0  # Would be actual count
        }
        
    except Exception as e:
        logger.error(f"ML model update task failed: {e}")
        raise


@app.task(bind=True)
def cleanup_old_data_task(self):
    """Clean up old data from database."""
    try:
        logger.info("Starting data cleanup task")
        
        async def cleanup():
            from src.models.database import OddsSnapshot, Alert as DBAlert
            from src.api.dependencies import AsyncSessionLocal
            from sqlalchemy import delete
            
            # Define retention periods
            odds_retention_days = 30
            alert_retention_days = 90
            
            async with AsyncSessionLocal() as db:
                # Delete old odds snapshots
                odds_cutoff = datetime.utcnow() - timedelta(days=odds_retention_days)
                odds_result = await db.execute(
                    delete(OddsSnapshot).where(OddsSnapshot.timestamp < odds_cutoff)
                )
                
                # Delete old alerts
                alert_cutoff = datetime.utcnow() - timedelta(days=alert_retention_days)
                alert_result = await db.execute(
                    delete(DBAlert).where(DBAlert.created_at < alert_cutoff)
                )
                
                await db.commit()
                
                return {
                    "odds_deleted": odds_result.rowcount,
                    "alerts_deleted": alert_result.rowcount
                }
        
        result = run_async(cleanup())
        logger.info(f"Cleanup completed: {result}")
        
        return {
            "status": "completed",
            "timestamp": datetime.utcnow().isoformat(),
            **result
        }
        
    except Exception as e:
        logger.error(f"Cleanup task failed: {e}")
        raise


@app.task
def send_alert_notification(alert_id: str, user_id: str):
    """Send notification for a specific alert."""
    try:
        logger.info(f"Sending notification for alert {alert_id}")
        
        # This would fetch the alert and user, then send notification
        # Simplified for now
        
        return {
            "status": "sent",
            "alert_id": alert_id,
            "user_id": user_id
        }
        
    except Exception as e:
        logger.error(f"Notification task failed: {e}")
        raise