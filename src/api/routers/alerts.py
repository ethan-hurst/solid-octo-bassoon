"""Alerts API endpoints."""
import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from datetime import datetime, timedelta
import uuid

from src.api.dependencies import (
    get_db,
    get_current_active_user,
    get_notification_service,
    PaginationParams
)
from src.models.schemas import User, Alert, ValueBet
from src.models.database import Alert as DBAlert, User as DBUser
from src.alerts.notification_service import NotificationService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/", response_model=List[Alert])
async def get_alerts(
    status: Optional[str] = Query(None, description="Filter by status"),
    days: int = Query(7, ge=1, le=30, description="Days of history"),
    db: AsyncSession = Depends(get_db),
    pagination: PaginationParams = Depends(),
    current_user: User = Depends(get_current_active_user)
):
    """Get user's alerts.
    
    Args:
        status: Filter by alert status
        days: Number of days of history
        db: Database session
        pagination: Pagination parameters
        current_user: Authenticated user
        
    Returns:
        List of user's alerts
    """
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Build query
        query = select(DBAlert).where(
            and_(
                DBAlert.user_id == uuid.UUID(current_user.id),
                DBAlert.created_at >= cutoff_date
            )
        )
        
        if status:
            query = query.where(DBAlert.status == status)
        
        # Apply pagination
        query = query.offset(pagination.skip).limit(pagination.limit)
        query = query.order_by(DBAlert.created_at.desc())
        
        # Execute query
        result = await db.execute(query)
        db_alerts = result.scalars().all()
        
        # Convert to Pydantic models
        alerts = []
        for db_alert in db_alerts:
            alert = Alert(
                id=str(db_alert.id),
                user_id=str(db_alert.user_id),
                value_bet=ValueBet(**db_alert.value_bet_data),
                created_at=db_alert.created_at,
                notification_channels=db_alert.notification_channels,
                status=db_alert.status,
                sent_at=db_alert.sent_at
            )
            alerts.append(alert)
        
        return alerts
        
    except Exception as e:
        logger.error(f"Error fetching alerts: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch alerts")


@router.get("/{alert_id}", response_model=Alert)
async def get_alert(
    alert_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get specific alert.
    
    Args:
        alert_id: Alert identifier
        db: Database session
        current_user: Authenticated user
        
    Returns:
        Alert details
    """
    try:
        # Query alert
        query = select(DBAlert).where(
            and_(
                DBAlert.id == uuid.UUID(alert_id),
                DBAlert.user_id == uuid.UUID(current_user.id)
            )
        )
        
        result = await db.execute(query)
        db_alert = result.scalar_one_or_none()
        
        if not db_alert:
            raise HTTPException(status_code=404, detail="Alert not found")
        
        # Convert to Pydantic model
        alert = Alert(
            id=str(db_alert.id),
            user_id=str(db_alert.user_id),
            value_bet=ValueBet(**db_alert.value_bet_data),
            created_at=db_alert.created_at,
            notification_channels=db_alert.notification_channels,
            status=db_alert.status,
            sent_at=db_alert.sent_at
        )
        
        return alert
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching alert: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch alert")


@router.post("/test")
async def create_test_alert(
    notification_service: NotificationService = Depends(get_notification_service),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a test alert for the current user.
    
    Args:
        notification_service: Notification service
        db: Database session
        current_user: Authenticated user
        
    Returns:
        Test alert creation status
    """
    try:
        # Create a sample value bet
        from src.models.schemas import MarketOdds, BookmakerOdds, SportType, BetType
        
        market_odds = MarketOdds(
            game_id="test_game_123",
            sport=SportType.NFL,
            home_team="Test Home Team",
            away_team="Test Away Team",
            commence_time=datetime.utcnow() + timedelta(hours=3),
            bet_type=BetType.MONEYLINE,
            bookmaker_odds=[
                BookmakerOdds(
                    bookmaker="TestBook",
                    odds=2.15,
                    last_update=datetime.utcnow()
                )
            ]
        )
        
        value_bet = ValueBet(
            game_id="test_game_123",
            market=market_odds,
            true_probability=0.52,
            implied_probability=0.465,  # 1/2.15
            edge=0.055,
            expected_value=0.118,
            confidence_score=0.75,
            kelly_fraction=0.025
        )
        
        # Create alert
        alert = Alert(
            user_id=current_user.id,
            value_bet=value_bet,
            notification_channels=current_user.notification_channels
        )
        
        # Save to database
        db_alert = DBAlert(
            user_id=uuid.UUID(current_user.id),
            value_bet_data=value_bet.model_dump(),
            notification_channels=alert.notification_channels,
            status="pending"
        )
        db.add(db_alert)
        await db.commit()
        
        # Update alert with DB ID
        alert.id = str(db_alert.id)
        
        # Send notifications
        results = await notification_service.send_alert(alert, current_user)
        
        # Update status
        db_alert.status = "sent" if any(results.values()) else "failed"
        db_alert.sent_at = datetime.utcnow()
        await db.commit()
        
        return {
            "alert_id": alert.id,
            "status": "created",
            "notification_results": results
        }
        
    except Exception as e:
        logger.error(f"Error creating test alert: {e}")
        raise HTTPException(status_code=500, detail="Failed to create test alert")


@router.put("/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Mark alert as acknowledged.
    
    Args:
        alert_id: Alert identifier
        db: Database session
        current_user: Authenticated user
        
    Returns:
        Update status
    """
    try:
        # Get alert
        query = select(DBAlert).where(
            and_(
                DBAlert.id == uuid.UUID(alert_id),
                DBAlert.user_id == uuid.UUID(current_user.id)
            )
        )
        
        result = await db.execute(query)
        db_alert = result.scalar_one_or_none()
        
        if not db_alert:
            raise HTTPException(status_code=404, detail="Alert not found")
        
        # Update status
        db_alert.status = "acknowledged"
        await db.commit()
        
        return {"status": "acknowledged", "alert_id": alert_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error acknowledging alert: {e}")
        raise HTTPException(status_code=500, detail="Failed to acknowledge alert")


@router.delete("/{alert_id}")
async def delete_alert(
    alert_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete an alert.
    
    Args:
        alert_id: Alert identifier
        db: Database session
        current_user: Authenticated user
        
    Returns:
        Deletion status
    """
    try:
        # Get alert
        query = select(DBAlert).where(
            and_(
                DBAlert.id == uuid.UUID(alert_id),
                DBAlert.user_id == uuid.UUID(current_user.id)
            )
        )
        
        result = await db.execute(query)
        db_alert = result.scalar_one_or_none()
        
        if not db_alert:
            raise HTTPException(status_code=404, detail="Alert not found")
        
        # Delete alert
        await db.delete(db_alert)
        await db.commit()
        
        return {"status": "deleted", "alert_id": alert_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting alert: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete alert")


@router.get("/stats/summary")
async def get_alert_stats(
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get alert statistics for user.
    
    Args:
        days: Number of days for statistics
        db: Database session
        current_user: Authenticated user
        
    Returns:
        Alert statistics
    """
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Query alerts
        query = select(DBAlert).where(
            and_(
                DBAlert.user_id == uuid.UUID(current_user.id),
                DBAlert.created_at >= cutoff_date
            )
        )
        
        result = await db.execute(query)
        alerts = result.scalars().all()
        
        # Calculate statistics
        total_alerts = len(alerts)
        sent_alerts = sum(1 for a in alerts if a.status == "sent")
        failed_alerts = sum(1 for a in alerts if a.status == "failed")
        
        # Edge distribution
        edges = []
        for alert in alerts:
            if "edge" in alert.value_bet_data:
                edges.append(alert.value_bet_data["edge"])
        
        avg_edge = sum(edges) / len(edges) if edges else 0
        
        return {
            "period_days": days,
            "total_alerts": total_alerts,
            "sent_alerts": sent_alerts,
            "failed_alerts": failed_alerts,
            "average_edge": avg_edge,
            "alerts_per_day": total_alerts / days if days > 0 else 0
        }
        
    except Exception as e:
        logger.error(f"Error calculating alert stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to calculate stats")