"""Mobile-specific API endpoints optimized for React Native app"""
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.auth.dependencies import get_current_user
from src.models.user import User
from src.models.schemas import (
    ValueBet,
    MarketOdds,
    SportType,
    BetType,
    UserProfile,
    PerformanceSummary,
)
from src.services.analysis_service import AnalysisService
from src.services.odds_service import OddsService
from src.services.live_betting.notification_service import NotificationService
from src.services.live_betting.value_detection import LiveValueDetector
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/v1/mobile", tags=["mobile"])

# Mobile-specific response models
class MobileDeviceInfo(BaseModel):
    """Mobile device registration information"""
    device_id: str
    platform: str = Field(..., pattern="^(ios|android)$")
    push_token: str
    app_version: str
    os_version: str
    device_model: str
    timezone: str
    notification_preferences: dict

class DeviceRegistrationResult(BaseModel):
    """Device registration response"""
    success: bool
    device_id: str
    message: str

class QuickAnalysisResult(BaseModel):
    """Quick analysis optimized for mobile display"""
    bet_summary: str
    value_score: float
    confidence: float
    recommendation: str  # "strong_bet", "good_bet", "pass", "avoid"
    key_insight: Optional[str]
    quick_stats: List[dict]
    estimated_read_time: int  # seconds

class QuickValueBet(BaseModel):
    """Condensed value bet for mobile feed"""
    bet_id: str
    title: str
    subtitle: str
    edge: float
    confidence: float
    odds: int
    sport_icon: str
    urgency: str  # "high", "medium", "low"

class MobileDashboard(BaseModel):
    """Mobile-optimized dashboard response"""
    user_summary: dict
    today_highlights: List[dict]
    quick_value_bets: List[QuickValueBet]
    live_games: List[dict]
    social_updates: List[dict]
    notifications_count: int

class LiveGameMobile(BaseModel):
    """Live game data optimized for mobile"""
    game_id: str
    sport: str
    home_team: str
    away_team: str
    score: dict
    time_remaining: str
    live_bets_available: int
    value_bets_count: int
    is_followed: bool

class QuickBetRequest(BaseModel):
    """Quick bet request from mobile"""
    bet_id: str
    action: str  # "analyze", "add_to_betslip", "dismiss"
    source_screen: str

class QuickBetResult(BaseModel):
    """Quick bet action result"""
    success: bool
    action: str
    message: str
    next_action: Optional[str]

class MobileSocialFeed(BaseModel):
    """Social feed optimized for mobile"""
    posts: List[dict]
    has_more: bool
    next_page: Optional[int]

class PaginatedValueBets(BaseModel):
    """Paginated value bets for infinite scroll"""
    bets: List[QuickValueBet]
    total: int
    page: int
    has_more: bool

@router.get("/dashboard", response_model=MobileDashboard)
async def get_mobile_dashboard(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> MobileDashboard:
    """Get mobile-optimized dashboard with essential data"""
    
    analysis_service = AnalysisService(db)
    odds_service = OddsService()
    
    # Get user performance summary
    performance = await analysis_service.get_performance_summary(current_user.id)
    
    # Get today's top value bets
    value_bets = await analysis_service.get_value_bets(
        sports=[SportType.NFL, SportType.NBA],
        min_edge=0.05,
        limit=5
    )
    
    # Convert to mobile format
    quick_bets = []
    for bet in value_bets:
        quick_bet = QuickValueBet(
            bet_id=bet.id,
            title=f"{bet.market.home_team} vs {bet.market.away_team}",
            subtitle=f"{bet.market.sport} • {bet.market.bet_type}",
            edge=bet.edge,
            confidence=bet.confidence_score,
            odds=int(bet.market.bookmaker_odds[0].odds),
            sport_icon=_get_sport_icon(bet.market.sport),
            urgency="high" if bet.edge > 0.08 else "medium"
        )
        quick_bets.append(quick_bet)
    
    # Get live games
    live_games = await odds_service.get_live_games()
    
    return MobileDashboard(
        user_summary={
            "username": current_user.username,
            "total_profit": performance.total_profit,
            "win_rate": performance.win_rate,
            "active_bets": performance.active_bets
        },
        today_highlights=[
            {"type": "stat", "label": "Today's P&L", "value": f"${performance.today_profit:+.2f}"},
            {"type": "stat", "label": "Win Rate", "value": f"{performance.win_rate:.1f}%"},
            {"type": "alert", "label": "New Value Bets", "value": str(len(quick_bets))}
        ],
        quick_value_bets=quick_bets,
        live_games=live_games[:5],  # Top 5 live games
        social_updates=[],  # TODO: Implement social updates
        notifications_count=0  # TODO: Get unread notifications count
    )

@router.get("/quick-analysis/{bet_id}", response_model=QuickAnalysisResult)
async def get_quick_bet_analysis(
    bet_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> QuickAnalysisResult:
    """Get quick bet analysis optimized for mobile display"""
    
    analysis_service = AnalysisService(db)
    
    # Get bet details
    bet = await analysis_service.get_bet_by_id(bet_id)
    if not bet:
        raise HTTPException(status_code=404, detail="Bet not found")
    
    # Generate quick analysis
    recommendation = _get_recommendation(bet.edge, bet.confidence_score)
    
    return QuickAnalysisResult(
        bet_summary=f"{bet.market.home_team} vs {bet.market.away_team} - {bet.market.bet_type}",
        value_score=bet.edge,
        confidence=bet.confidence_score,
        recommendation=recommendation,
        key_insight=f"Historical win rate: {bet.confidence_score * 100:.0f}% with similar edge",
        quick_stats=[
            {"label": "Edge", "value": f"{bet.edge * 100:.1f}%"},
            {"label": "Odds", "value": f"{bet.market.bookmaker_odds[0].odds:+d}"},
            {"label": "Kelly %", "value": f"{bet.kelly_fraction * 100:.1f}%"},
            {"label": "Confidence", "value": f"{bet.confidence_score * 100:.0f}%"}
        ],
        estimated_read_time=5
    )

@router.get("/value-bets/feed", response_model=PaginatedValueBets)
async def get_value_bets_feed(
    page: int = 1,
    limit: int = 20,
    sports: Optional[List[str]] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> PaginatedValueBets:
    """Get paginated value bets feed for mobile scrolling"""
    
    analysis_service = AnalysisService(db)
    
    # Convert sports strings to enums
    sport_types = None
    if sports:
        sport_types = [SportType(sport) for sport in sports]
    
    # Get value bets
    offset = (page - 1) * limit
    value_bets = await analysis_service.get_value_bets(
        sports=sport_types,
        min_edge=0.03,
        limit=limit,
        offset=offset
    )
    
    # Convert to mobile format
    quick_bets = []
    for bet in value_bets:
        quick_bet = QuickValueBet(
            bet_id=bet.id,
            title=f"{bet.market.home_team} vs {bet.market.away_team}",
            subtitle=f"{bet.market.sport} • {bet.market.bet_type}",
            edge=bet.edge,
            confidence=bet.confidence_score,
            odds=int(bet.market.bookmaker_odds[0].odds),
            sport_icon=_get_sport_icon(bet.market.sport),
            urgency=_get_urgency(bet.edge, bet.market.commence_time)
        )
        quick_bets.append(quick_bet)
    
    # Get total count for pagination
    total_count = await analysis_service.get_value_bets_count(
        sports=sport_types,
        min_edge=0.03
    )
    
    return PaginatedValueBets(
        bets=quick_bets,
        total=total_count,
        page=page,
        has_more=(page * limit) < total_count
    )

@router.post("/notifications/register", response_model=DeviceRegistrationResult)
async def register_mobile_device(
    device_info: MobileDeviceInfo,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> DeviceRegistrationResult:
    """Register mobile device for push notifications"""
    
    # TODO: Implement device registration in database
    # For now, return success
    
    return DeviceRegistrationResult(
        success=True,
        device_id=device_info.device_id,
        message="Device registered successfully"
    )

@router.get("/games/live", response_model=List[LiveGameMobile])
async def get_live_games_mobile(
    sports: Optional[List[str]] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> List[LiveGameMobile]:
    """Get live games optimized for mobile display"""
    
    odds_service = OddsService()
    analysis_service = AnalysisService(db)
    
    # Get live games
    live_games = await odds_service.get_live_games(sports=sports)
    
    # Convert to mobile format
    mobile_games = []
    for game in live_games[:10]:  # Limit to 10 for mobile
        # Count available value bets for this game
        value_bets_count = await analysis_service.get_game_value_bets_count(game["game_id"])
        
        mobile_game = LiveGameMobile(
            game_id=game["game_id"],
            sport=game["sport"],
            home_team=game["home_team"],
            away_team=game["away_team"],
            score=game.get("score", {"home": 0, "away": 0}),
            time_remaining=game.get("time_remaining", "0:00"),
            live_bets_available=game.get("markets_count", 0),
            value_bets_count=value_bets_count,
            is_followed=False  # TODO: Check if user follows this game
        )
        mobile_games.append(mobile_game)
    
    return mobile_games

@router.post("/bets/quick-add", response_model=QuickBetResult)
async def quick_add_to_betslip(
    bet_request: QuickBetRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> QuickBetResult:
    """Quickly add bet to betslip from mobile interface"""
    
    # TODO: Implement betslip functionality
    
    if bet_request.action == "analyze":
        return QuickBetResult(
            success=True,
            action="analyze",
            message="Opening detailed analysis",
            next_action="navigate_to_analysis"
        )
    elif bet_request.action == "add_to_betslip":
        return QuickBetResult(
            success=True,
            action="add_to_betslip",
            message="Added to betslip",
            next_action="view_betslip"
        )
    else:
        return QuickBetResult(
            success=True,
            action="dismiss",
            message="Bet dismissed",
            next_action=None
        )

@router.get("/social/feed", response_model=MobileSocialFeed)
async def get_mobile_social_feed(
    page: int = 1,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> MobileSocialFeed:
    """Get social feed optimized for mobile scrolling"""
    
    # TODO: Implement social feed
    
    return MobileSocialFeed(
        posts=[],
        has_more=False,
        next_page=None
    )

@router.websocket("/ws/{user_id}")
async def mobile_websocket_endpoint(
    websocket: WebSocket,
    user_id: str,
    db: AsyncSession = Depends(get_db)
):
    """WebSocket endpoint optimized for mobile clients"""
    
    await websocket.accept()
    
    # TODO: Implement mobile-specific WebSocket handling
    # - Reduced message size
    # - Battery-efficient heartbeat
    # - Automatic reconnection handling
    
    try:
        while True:
            data = await websocket.receive_text()
            # Process mobile WebSocket messages
            await websocket.send_text(f"Echo: {data}")
    except WebSocketDisconnect:
        print(f"Mobile client {user_id} disconnected")

# Helper functions
def _get_sport_icon(sport: str) -> str:
    """Get icon name for sport"""
    icons = {
        SportType.NFL: "football",
        SportType.NBA: "basketball", 
        SportType.MLB: "baseball",
        SportType.NHL: "hockey",
        SportType.SOCCER_EPL: "soccer",
    }
    return icons.get(sport, "sports")

def _get_recommendation(edge: float, confidence: float) -> str:
    """Get bet recommendation based on edge and confidence"""
    if edge >= 0.08 and confidence >= 0.65:
        return "strong_bet"
    elif edge >= 0.05 and confidence >= 0.60:
        return "good_bet"
    elif edge >= 0.03:
        return "pass"
    else:
        return "avoid"

def _get_urgency(edge: float, commence_time: str) -> str:
    """Determine urgency level for a bet"""
    # High urgency if high edge or game starting soon
    if edge >= 0.08:
        return "high"
    
    # Check if game is starting soon
    try:
        game_time = datetime.fromisoformat(commence_time.replace('Z', '+00:00'))
        time_until_game = (game_time - datetime.utcnow()).total_seconds() / 3600
        
        if time_until_game < 1:  # Less than 1 hour
            return "high"
        elif time_until_game < 6:  # Less than 6 hours
            return "medium"
    except:
        pass
    
    return "low"