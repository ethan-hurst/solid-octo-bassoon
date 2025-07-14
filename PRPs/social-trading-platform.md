# Social Trading Platform - Project Requirements & Planning

## 📋 Project Overview

**Project Name**: Social Trading & Copy Betting Platform  
**Priority**: High  
**Estimated Timeline**: 4-5 months  
**Business Impact**: High - Network effects & user acquisition  
**Technical Complexity**: Medium-High  

### Executive Summary
Build a social trading platform that combines sports betting analytics with social networking features, allowing users to follow successful bettors, copy their strategies, and participate in a community-driven betting ecosystem. This creates powerful network effects and differentiates our platform from traditional betting tools.

## 🎯 Business Objectives

### Primary Goals
- **User Acquisition**: Viral growth through social features and referrals
- **User Retention**: Community engagement increases lifetime value by 300%+
- **Revenue Growth**: Commission-based revenue from copy betting transactions
- **Market Differentiation**: First sports betting platform with true social trading

### Success Metrics
- **Community Growth**: 50,000+ active community members within 6 months
- **Copy Trading Volume**: $5M+ in copy trades within first year
- **User Engagement**: 400% increase in session duration
- **Viral Coefficient**: 0.3+ (every user brings 0.3 new users on average)

## 🌐 Market Analysis

### Social Trading Market
- **Forex/Crypto**: $500M+ market with platforms like eToro, ZuluTrade
- **Sports Betting**: Completely untapped market opportunity
- **Network Effects**: Winner-takes-all market dynamics
- **User Behavior**: 80% of retail traders/bettors lose money, seek to follow winners

### Competitive Landscape
- **Current Gap**: No social trading platform for sports betting exists
- **eToro Model**: Copy trading with social features (not sports betting)
- **Traditional Sports**: Basic bet sharing, no performance tracking
- **Opportunity**: First-mover advantage in sports betting social trading

## 👥 User Personas & Community Structure

### Community Member Types
```python
class UserType(str, Enum):
    FOLLOWER = "follower"           # Follows and copies other bettors
    TRADER = "trader"               # Makes own bets, may have followers
    EXPERT = "expert"               # Verified profitable bettor with many followers
    INFLUENCER = "influencer"       # Social media presence, monetizes following
    ANALYST = "analyst"             # Provides analysis and predictions
    BEGINNER = "beginner"           # New to betting, learning from community

class CommunityTier(str, Enum):
    BRONZE = "bronze"               # 0-10 followers, basic features
    SILVER = "silver"               # 11-100 followers, enhanced features  
    GOLD = "gold"                   # 101-1000 followers, premium features
    PLATINUM = "platinum"           # 1000+ followers, pro tools
    VERIFIED = "verified"           # Verified profitable track record
```

### User Journey Mapping
```python
USER_JOURNEYS = {
    "new_user_onboarding": {
        "steps": [
            "account_creation",
            "risk_tolerance_assessment", 
            "interest_sport_selection",
            "follow_recommendation_engine",
            "first_copy_trade_tutorial",
            "community_introduction"
        ],
        "conversion_goals": ["first_follow", "first_copy_trade", "first_post"]
    },
    "follower_to_trader": {
        "steps": [
            "observe_successful_strategies",
            "learn_from_expert_analysis", 
            "start_making_independent_bets",
            "share_first_bet_rationale",
            "gain_first_followers",
            "develop_unique_strategy"
        ],
        "conversion_goals": ["first_original_bet", "first_follower", "consistent_posting"]
    },
    "trader_to_expert": {
        "steps": [
            "demonstrate_consistent_profitability",
            "build_follower_base_organically",
            "apply_for_expert_verification", 
            "pass_verification_process",
            "access_monetization_features",
            "scale_influence_and_earnings"
        ],
        "conversion_goals": ["verification", "monetization", "1000_followers"]
    }
}
```

## 🏗️ Core Platform Features

### 1. Social Profiles & Performance Tracking
```python
class UserProfile(BaseModel):
    """Comprehensive user profile with verified performance metrics"""
    
    user_id: str
    username: str
    display_name: str
    bio: Optional[str]
    profile_image: Optional[str]
    
    # Performance metrics (verified)
    total_bets: int
    winning_percentage: float
    total_profit_loss: float
    roi_percentage: float
    average_odds: float
    
    # Time-based performance
    performance_last_30_days: PerformanceMetrics
    performance_last_year: PerformanceMetrics
    performance_all_time: PerformanceMetrics
    
    # Community metrics
    followers_count: int
    following_count: int
    copy_traders_count: int
    total_copied_volume: float
    
    # Verification and credibility
    is_verified: bool
    verification_level: CommunityTier
    trust_score: float  # 0.0 to 1.0
    
    # Specialization
    favorite_sports: List[str]
    betting_styles: List[str]  # ["value_betting", "arbitrage", "props", "live"]
    expertise_tags: List[str]
    
    # Social features
    posts_count: int
    likes_received: int
    comments_made: int
    last_active: datetime

class PerformanceMetrics(BaseModel):
    """Detailed performance breakdown"""
    total_bets: int
    winning_bets: int
    losing_bets: int
    winning_percentage: float
    total_staked: float
    total_profit_loss: float
    roi_percentage: float
    
    # Advanced metrics
    average_odds: float
    longest_winning_streak: int
    longest_losing_streak: int
    best_month: MonthlyStats
    worst_month: MonthlyStats
    
    # Sport-specific breakdown
    sport_performance: Dict[str, SportPerformance]
    
    # Risk metrics
    max_drawdown: float
    sharpe_ratio: float
    volatility: float
```

### 2. Copy Trading System
```python
class CopyTradingEngine:
    """Core engine for copy trading functionality"""
    
    async def create_copy_relationship(
        self, 
        follower_id: str, 
        trader_id: str, 
        copy_settings: CopySettings
    ) -> CopyRelationship:
        """Establish copy trading relationship between users"""
        
        # Validate trader eligibility
        trader = await self.get_trader_profile(trader_id)
        if not trader.is_eligible_for_copying():
            raise ValueError("Trader not eligible for copying")
        
        # Create copy relationship
        relationship = CopyRelationship(
            follower_id=follower_id,
            trader_id=trader_id,
            settings=copy_settings,
            status="active",
            created_at=datetime.utcnow()
        )
        
        await self.db.save(relationship)
        return relationship
    
    async def execute_copy_trade(
        self, 
        original_bet: Bet, 
        copy_relationships: List[CopyRelationship]
    ) -> List[CopyTrade]:
        """Execute copy trades for all followers when trader places bet"""
        
        copy_trades = []
        
        for relationship in copy_relationships:
            if not relationship.should_copy_bet(original_bet):
                continue
                
            # Calculate copy bet size based on settings
            copy_bet_size = self._calculate_copy_bet_size(
                original_bet, 
                relationship.settings,
                relationship.follower_bankroll
            )
            
            if copy_bet_size > 0:
                copy_trade = await self._place_copy_bet(
                    original_bet=original_bet,
                    relationship=relationship,
                    bet_size=copy_bet_size
                )
                copy_trades.append(copy_trade)
        
        return copy_trades
    
    def _calculate_copy_bet_size(
        self, 
        original_bet: Bet, 
        settings: CopySettings,
        follower_bankroll: float
    ) -> float:
        """Calculate appropriate bet size for copy trade"""
        
        if settings.copy_mode == "fixed_amount":
            return min(settings.fixed_amount, follower_bankroll * 0.05)
        
        elif settings.copy_mode == "percentage_of_bankroll":
            return follower_bankroll * settings.percentage / 100
        
        elif settings.copy_mode == "proportional":
            # Copy same percentage of bankroll as original trader
            trader_percentage = original_bet.amount / settings.trader_bankroll
            return follower_bankroll * trader_percentage
        
        elif settings.copy_mode == "kelly_scaled":
            # Scale Kelly Criterion bet to follower's bankroll
            original_kelly = original_bet.kelly_fraction
            return follower_bankroll * original_kelly * settings.kelly_scaling_factor
        
        return 0.0

class CopySettings(BaseModel):
    """Settings for copy trading relationship"""
    
    # Copy mode and sizing
    copy_mode: Literal["fixed_amount", "percentage_of_bankroll", "proportional", "kelly_scaled"]
    fixed_amount: Optional[float] = None
    percentage: Optional[float] = None  # 1-5% typical
    kelly_scaling_factor: float = 1.0  # 0.5 = half Kelly, 1.0 = full Kelly
    
    # Filters for which bets to copy
    sports_filter: Optional[List[str]] = None
    min_odds: Optional[float] = None
    max_odds: Optional[float] = None
    min_edge: Optional[float] = None
    bet_types_filter: Optional[List[str]] = None
    
    # Risk management
    max_bet_size: float
    daily_loss_limit: float
    monthly_loss_limit: float
    
    # Timing
    copy_delay_seconds: int = 0  # Delay before copying (0-300 seconds)
    auto_copy_enabled: bool = True
    
    # Performance-based adjustments
    stop_copying_if_drawdown: float = 0.20  # Stop if 20% drawdown
    reduce_size_if_losing_streak: int = 5  # Reduce size after 5 losses
```

### 3. Community Feed & Social Features
```python
class CommunityFeed:
    """Social feed with betting-specific content"""
    
    async def create_bet_post(self, bet: Bet, user_id: str, content: str) -> BetPost:
        """Create a social post for a bet with analysis"""
        
        post = BetPost(
            user_id=user_id,
            bet_id=bet.bet_id,
            content=content,
            bet_summary=self._generate_bet_summary(bet),
            tags=self._extract_tags(content),
            created_at=datetime.utcnow()
        )
        
        # Auto-notify followers
        await self._notify_followers(user_id, post)
        
        return post
    
    async def generate_personalized_feed(self, user_id: str, limit: int = 50) -> List[FeedItem]:
        """Generate personalized feed based on user interests and following"""
        
        user = await self.get_user(user_id)
        
        # Get content from followed users
        following_content = await self._get_following_content(user.following_list)
        
        # Get content from similar users (collaborative filtering)
        similar_users_content = await self._get_similar_users_content(user)
        
        # Get trending content in user's sports
        trending_content = await self._get_trending_content(user.favorite_sports)
        
        # Get educational content for user's skill level
        educational_content = await self._get_educational_content(user.skill_level)
        
        # Combine and rank content
        all_content = (
            following_content + 
            similar_users_content + 
            trending_content + 
            educational_content
        )
        
        # Rank by relevance score
        ranked_content = self._rank_content_by_relevance(all_content, user)
        
        return ranked_content[:limit]

class BetPost(BaseModel):
    """Social post for a specific bet"""
    
    post_id: str
    user_id: str
    bet_id: str
    content: str
    
    # Bet information
    bet_summary: BetSummary
    sport: str
    bet_type: str
    odds: float
    stake: float
    potential_payout: float
    
    # Analysis and reasoning
    analysis: Optional[str]
    confidence_level: Optional[int]  # 1-10 scale
    tags: List[str]
    
    # Social engagement
    likes_count: int = 0
    comments_count: int = 0
    copies_count: int = 0  # How many people copied this bet
    
    # Performance tracking
    bet_result: Optional[Literal["won", "lost", "push", "pending"]]
    actual_payout: Optional[float]
    
    # Metadata
    created_at: datetime
    updated_at: datetime
    is_featured: bool = False

class LeaderboardSystem:
    """Community leaderboards and rankings"""
    
    async def get_top_performers(
        self, 
        timeframe: str = "30_days",
        sport: Optional[str] = None,
        min_bets: int = 10
    ) -> List[LeaderboardEntry]:
        """Get top performing bettors for leaderboard"""
        
        filters = {
            "min_bets": min_bets,
            "timeframe": timeframe
        }
        
        if sport:
            filters["sport"] = sport
        
        # Calculate performance metrics
        performers = await self.db.query("""
            SELECT 
                user_id,
                username,
                COUNT(*) as total_bets,
                SUM(CASE WHEN result = 'won' THEN 1 ELSE 0 END) as winning_bets,
                SUM(CASE WHEN result = 'won' THEN payout - stake ELSE -stake END) as profit_loss,
                SUM(stake) as total_staked,
                AVG(odds) as avg_odds
            FROM bets b
            JOIN users u ON b.user_id = u.user_id
            WHERE b.placed_at >= %s
            AND (%(sport)s IS NULL OR b.sport = %(sport)s)
            GROUP BY user_id, username
            HAVING COUNT(*) >= %(min_bets)s
            ORDER BY (SUM(CASE WHEN result = 'won' THEN payout - stake ELSE -stake END) / SUM(stake)) DESC
            LIMIT 100
        """, filters)
        
        return [LeaderboardEntry.from_db_row(row) for row in performers]
```

### 4. Expert Verification & Monetization
```python
class ExpertVerificationSystem:
    """System for verifying and managing expert bettors"""
    
    async def apply_for_verification(self, user_id: str) -> VerificationApplication:
        """User applies for expert verification"""
        
        user = await self.get_user(user_id)
        
        # Check minimum requirements
        requirements = await self._check_verification_requirements(user)
        if not requirements.all_met:
            raise ValueError(f"Requirements not met: {requirements.missing}")
        
        # Create verification application
        application = VerificationApplication(
            user_id=user_id,
            applied_at=datetime.utcnow(),
            status="pending",
            requirements_snapshot=requirements,
            performance_data=await self._gather_performance_data(user_id)
        )
        
        await self.db.save(application)
        
        # Start verification process
        await self._initiate_verification_process(application)
        
        return application
    
    async def _check_verification_requirements(self, user: User) -> VerificationRequirements:
        """Check if user meets verification requirements"""
        
        performance = await self.get_user_performance(user.user_id, "1_year")
        
        requirements = VerificationRequirements(
            min_bets_met=performance.total_bets >= 100,
            min_profit_met=performance.roi_percentage >= 5.0,
            min_timeframe_met=user.account_age_days >= 90,
            min_followers_met=user.followers_count >= 50,
            no_suspicious_activity=await self._check_suspicious_activity(user.user_id),
            identity_verified=user.identity_verified
        )
        
        return requirements
    
    async def verify_expert(self, application_id: str, reviewer_id: str) -> VerificationResult:
        """Manually verify expert application"""
        
        application = await self.get_application(application_id)
        
        # Detailed performance analysis
        performance_analysis = await self._deep_performance_analysis(application.user_id)
        
        # Check for bet manipulation or suspicious patterns
        integrity_check = await self._integrity_analysis(application.user_id)
        
        # Final verification decision
        if performance_analysis.verified and integrity_check.passed:
            await self._grant_expert_status(application.user_id)
            status = "approved"
        else:
            status = "rejected"
        
        result = VerificationResult(
            application_id=application_id,
            reviewer_id=reviewer_id,
            status=status,
            performance_analysis=performance_analysis,
            integrity_check=integrity_check,
            reviewed_at=datetime.utcnow()
        )
        
        await self.db.save(result)
        return result

class MonetizationSystem:
    """Monetization features for expert bettors"""
    
    async def setup_expert_monetization(self, user_id: str) -> ExpertMonetization:
        """Setup monetization options for verified expert"""
        
        expert = await self.get_verified_expert(user_id)
        
        monetization = ExpertMonetization(
            expert_id=user_id,
            
            # Copy trading commissions
            copy_commission_rate=0.10,  # 10% of copy trading profits
            min_copy_amount=10.0,
            
            # Premium subscriptions
            premium_subscription_price=29.99,  # Monthly
            premium_features=["exclusive_tips", "detailed_analysis", "1on1_chat"],
            
            # Pay-per-tip
            tip_price=9.99,
            tip_guarantee="money_back_if_loses",
            
            # Course/education sales
            course_creation_enabled=True,
            course_commission_rate=0.30,  # Platform takes 30%
            
            # Affiliate partnerships
            affiliate_programs=["draftkings", "fanduel", "betmgm"],
            affiliate_commission_rate=0.25
        )
        
        await self.db.save(monetization)
        return monetization
```

## 📱 API Design

### Social Trading Endpoints
```python
# User profiles and social features
@router.get("/social/users/{user_id}/profile")
async def get_user_profile(user_id: str) -> UserProfile:
    """Get detailed user profile with performance metrics"""

@router.get("/social/users/{user_id}/followers")
async def get_user_followers(user_id: str, page: int = 1) -> PaginatedUsers:
    """Get user's followers list"""

@router.post("/social/users/{user_id}/follow")
async def follow_user(user_id: str, current_user: User = Depends(get_current_user)) -> FollowResult:
    """Follow another user"""

# Copy trading
@router.post("/social/copy-trading/relationships")
async def create_copy_relationship(
    relationship: CreateCopyRelationship,
    current_user: User = Depends(get_current_user)
) -> CopyRelationship:
    """Start copying another user's bets"""

@router.get("/social/copy-trading/my-relationships")
async def get_my_copy_relationships(current_user: User = Depends(get_current_user)) -> List[CopyRelationship]:
    """Get user's copy trading relationships"""

@router.put("/social/copy-trading/relationships/{relationship_id}/settings")
async def update_copy_settings(
    relationship_id: str,
    settings: CopySettings,
    current_user: User = Depends(get_current_user)
) -> CopyRelationship:
    """Update copy trading settings"""

# Community feed
@router.get("/social/feed")
async def get_personalized_feed(
    current_user: User = Depends(get_current_user),
    page: int = 1,
    limit: int = 50
) -> PaginatedFeed:
    """Get personalized community feed"""

@router.post("/social/posts")
async def create_bet_post(
    post: CreateBetPost,
    current_user: User = Depends(get_current_user)
) -> BetPost:
    """Create a post about a bet"""

@router.post("/social/posts/{post_id}/like")
async def like_post(post_id: str, current_user: User = Depends(get_current_user)) -> LikeResult:
    """Like a community post"""

@router.post("/social/posts/{post_id}/copy-bet")
async def copy_bet_from_post(
    post_id: str,
    copy_settings: CopyBetSettings,
    current_user: User = Depends(get_current_user)
) -> CopyBetResult:
    """Copy a bet from a community post"""

# Leaderboards
@router.get("/social/leaderboards/top-performers")
async def get_top_performers(
    timeframe: str = "30_days",
    sport: Optional[str] = None,
    min_bets: int = 10
) -> List[LeaderboardEntry]:
    """Get top performing bettors leaderboard"""

@router.get("/social/leaderboards/trending")
async def get_trending_users(
    timeframe: str = "7_days"
) -> List[TrendingUser]:
    """Get trending/hot users in the community"""

# Expert verification
@router.post("/social/expert/apply")
async def apply_for_expert_verification(
    current_user: User = Depends(get_current_user)
) -> VerificationApplication:
    """Apply for expert verification"""

@router.get("/social/expert/requirements")
async def get_verification_requirements(
    current_user: User = Depends(get_current_user)
) -> VerificationRequirements:
    """Check expert verification requirements"""
```

## 🛠️ Database Schema

### Social Trading Tables
```sql
-- User relationships (following/followers)
CREATE TABLE user_relationships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    follower_id UUID REFERENCES users(user_id),
    following_id UUID REFERENCES users(user_id),
    relationship_type VARCHAR(50) DEFAULT 'follow', -- 'follow', 'copy', 'block'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(follower_id, following_id)
);

-- Copy trading relationships
CREATE TABLE copy_trading_relationships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    follower_id UUID REFERENCES users(user_id),
    trader_id UUID REFERENCES users(user_id),
    settings JSONB NOT NULL,
    status VARCHAR(20) DEFAULT 'active', -- 'active', 'paused', 'cancelled'
    total_copied_amount DECIMAL(15,2) DEFAULT 0,
    total_profit_loss DECIMAL(15,2) DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(follower_id, trader_id)
);

-- Copy trades (individual copied bets)
CREATE TABLE copy_trades (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    relationship_id UUID REFERENCES copy_trading_relationships(id),
    original_bet_id UUID REFERENCES bets(bet_id),
    copy_bet_id UUID REFERENCES bets(bet_id),
    copy_amount DECIMAL(15,2) NOT NULL,
    copy_ratio DECIMAL(5,4) NOT NULL, -- What % of original bet size
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Community posts
CREATE TABLE community_posts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(user_id),
    post_type VARCHAR(50) NOT NULL, -- 'bet_post', 'analysis', 'discussion'
    title VARCHAR(255),
    content TEXT NOT NULL,
    
    -- Bet-specific fields
    bet_id UUID REFERENCES bets(bet_id),
    sport VARCHAR(50),
    confidence_level INTEGER, -- 1-10
    
    -- Engagement metrics
    likes_count INTEGER DEFAULT 0,
    comments_count INTEGER DEFAULT 0,
    shares_count INTEGER DEFAULT 0,
    copies_count INTEGER DEFAULT 0,
    
    -- Content moderation
    is_featured BOOLEAN DEFAULT false,
    is_flagged BOOLEAN DEFAULT false,
    moderation_status VARCHAR(20) DEFAULT 'approved',
    
    -- Metadata
    tags JSONB,
    media_urls JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Post interactions
CREATE TABLE post_interactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(user_id),
    post_id UUID REFERENCES community_posts(id),
    interaction_type VARCHAR(20) NOT NULL, -- 'like', 'comment', 'share', 'copy'
    content TEXT, -- For comments
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, post_id, interaction_type)
);

-- User performance tracking
CREATE TABLE user_performance_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(user_id),
    snapshot_date DATE NOT NULL,
    timeframe VARCHAR(20) NOT NULL, -- '7_days', '30_days', '1_year', 'all_time'
    
    -- Performance metrics
    total_bets INTEGER NOT NULL,
    winning_bets INTEGER NOT NULL,
    losing_bets INTEGER NOT NULL,
    winning_percentage DECIMAL(5,4) NOT NULL,
    total_staked DECIMAL(15,2) NOT NULL,
    total_profit_loss DECIMAL(15,2) NOT NULL,
    roi_percentage DECIMAL(8,4) NOT NULL,
    average_odds DECIMAL(10,3),
    
    -- Advanced metrics
    sharpe_ratio DECIMAL(8,4),
    max_drawdown DECIMAL(8,4),
    longest_winning_streak INTEGER,
    longest_losing_streak INTEGER,
    
    -- Social metrics
    followers_count INTEGER DEFAULT 0,
    copy_traders_count INTEGER DEFAULT 0,
    total_copied_volume DECIMAL(15,2) DEFAULT 0,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, snapshot_date, timeframe)
);

-- Expert verification
CREATE TABLE expert_verification_applications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(user_id),
    status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'approved', 'rejected'
    
    -- Application data
    application_data JSONB NOT NULL,
    performance_snapshot JSONB NOT NULL,
    
    -- Review data
    reviewer_id UUID REFERENCES users(user_id),
    review_notes TEXT,
    reviewed_at TIMESTAMP WITH TIME ZONE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Expert monetization settings
CREATE TABLE expert_monetization (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    expert_id UUID REFERENCES users(user_id),
    
    -- Copy trading monetization
    copy_commission_rate DECIMAL(5,4) DEFAULT 0.10,
    min_copy_amount DECIMAL(10,2) DEFAULT 10.00,
    
    -- Subscription monetization
    subscription_price DECIMAL(10,2),
    subscription_features JSONB,
    
    -- Pay-per-tip monetization
    tip_price DECIMAL(10,2),
    tip_guarantee VARCHAR(50),
    
    -- Course/education monetization
    course_creation_enabled BOOLEAN DEFAULT false,
    course_commission_rate DECIMAL(5,4) DEFAULT 0.30,
    
    -- Settings
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_user_relationships_follower ON user_relationships(follower_id);
CREATE INDEX idx_user_relationships_following ON user_relationships(following_id);
CREATE INDEX idx_copy_relationships_active ON copy_trading_relationships(status, created_at) WHERE status = 'active';
CREATE INDEX idx_community_posts_user_created ON community_posts(user_id, created_at DESC);
CREATE INDEX idx_community_posts_featured ON community_posts(is_featured, created_at DESC) WHERE is_featured = true;
CREATE INDEX idx_post_interactions_post ON post_interactions(post_id, interaction_type);
CREATE INDEX idx_user_performance_user_date ON user_performance_snapshots(user_id, snapshot_date DESC);
CREATE INDEX idx_expert_verification_status ON expert_verification_applications(status, created_at);

-- TimescaleDB hypertables
SELECT create_hypertable('copy_trades', 'created_at');
SELECT create_hypertable('post_interactions', 'created_at');
SELECT create_hypertable('user_performance_snapshots', 'snapshot_date');
```

## 🧪 Testing Strategy

### Test Categories

#### 1. Social Features Tests
```python
@pytest.mark.asyncio
async def test_follow_user_workflow():
    """Test complete follow user workflow"""
    
    # Create test users
    user_a = await create_test_user("user_a")
    user_b = await create_test_user("user_b")
    
    # User A follows User B
    follow_result = await social_service.follow_user(user_a.user_id, user_b.user_id)
    assert follow_result.success == True
    
    # Verify relationship created
    relationships = await social_service.get_user_relationships(user_a.user_id)
    assert len(relationships.following) == 1
    assert relationships.following[0].user_id == user_b.user_id
    
    # Verify follower count updated
    user_b_updated = await user_service.get_user(user_b.user_id)
    assert user_b_updated.followers_count == 1

@pytest.mark.asyncio
async def test_copy_trading_workflow():
    """Test end-to-end copy trading workflow"""
    
    # Setup trader and follower
    trader = await create_test_user("trader", with_performance=True)
    follower = await create_test_user("follower", bankroll=1000.0)
    
    # Create copy relationship
    copy_settings = CopySettings(
        copy_mode="percentage_of_bankroll",
        percentage=2.0,  # 2% of bankroll
        max_bet_size=50.0
    )
    
    relationship = await copy_trading_service.create_copy_relationship(
        follower.user_id,
        trader.user_id,
        copy_settings
    )
    
    # Trader places a bet
    original_bet = Bet(
        user_id=trader.user_id,
        sport="NFL",
        bet_type="moneyline",
        amount=100.0,
        odds=2.0
    )
    
    # Execute copy trades
    copy_trades = await copy_trading_service.execute_copy_trade(
        original_bet,
        [relationship]
    )
    
    # Verify copy trade created correctly
    assert len(copy_trades) == 1
    copy_trade = copy_trades[0]
    assert copy_trade.copy_amount == 20.0  # 2% of 1000 bankroll
    assert copy_trade.relationship_id == relationship.id

@pytest.mark.asyncio
async def test_community_feed_generation():
    """Test personalized community feed generation"""
    
    # Create user with interests
    user = await create_test_user("user", favorite_sports=["NFL", "NBA"])
    
    # Create users they follow with content
    followed_users = []
    for i in range(5):
        followed_user = await create_test_user(f"followed_{i}")
        await social_service.follow_user(user.user_id, followed_user.user_id)
        
        # Create some posts
        await create_test_post(followed_user.user_id, sport="NFL")
        followed_users.append(followed_user)
    
    # Generate personalized feed
    feed = await community_service.generate_personalized_feed(user.user_id)
    
    # Verify feed content
    assert len(feed.items) > 0
    assert all(item.sport in ["NFL", "NBA"] for item in feed.items if item.sport)
    
    # Verify following content appears first
    following_posts = [item for item in feed.items if item.user_id in [u.user_id for u in followed_users]]
    assert len(following_posts) > 0
```

#### 2. Performance Tests
```python
@pytest.mark.asyncio
async def test_copy_trading_scalability():
    """Test copy trading system can handle scale"""
    
    # Create popular trader with 1000 followers
    trader = await create_test_user("popular_trader")
    followers = []
    
    for i in range(1000):
        follower = await create_test_user(f"follower_{i}")
        relationship = await copy_trading_service.create_copy_relationship(
            follower.user_id,
            trader.user_id,
            CopySettings(copy_mode="fixed_amount", fixed_amount=10.0)
        )
        followers.append(relationship)
    
    # Trader places bet
    start_time = time.time()
    
    original_bet = Bet(user_id=trader.user_id, amount=100.0, odds=2.0)
    copy_trades = await copy_trading_service.execute_copy_trade(original_bet, followers)
    
    execution_time = time.time() - start_time
    
    # Verify performance requirements
    assert len(copy_trades) == 1000, "Not all copy trades executed"
    assert execution_time < 10.0, f"Copy trade execution too slow: {execution_time}s"

@pytest.mark.asyncio
async def test_community_feed_performance():
    """Test community feed generation performance"""
    
    # Create user following 500 people
    user = await create_test_user("active_user")
    
    for i in range(500):
        followed_user = await create_test_user(f"followed_{i}")
        await social_service.follow_user(user.user_id, followed_user.user_id)
        
        # Each creates 10 posts
        for j in range(10):
            await create_test_post(followed_user.user_id)
    
    # Generate feed (5000 potential posts)
    start_time = time.time()
    feed = await community_service.generate_personalized_feed(user.user_id, limit=50)
    generation_time = time.time() - start_time
    
    # Verify performance
    assert len(feed.items) == 50, "Feed should return requested limit"
    assert generation_time < 2.0, f"Feed generation too slow: {generation_time}s"
```

#### 3. Security Tests
```python
@pytest.mark.asyncio
async def test_copy_trading_security():
    """Test copy trading system security measures"""
    
    # Test malicious bet manipulation
    trader = await create_test_user("trader")
    follower = await create_test_user("follower", bankroll=1000.0)
    
    relationship = await copy_trading_service.create_copy_relationship(
        follower.user_id,
        trader.user_id,
        CopySettings(copy_mode="percentage_of_bankroll", percentage=50.0)  # 50% - risky
    )
    
    # Attempt to place bet larger than follower's bankroll
    malicious_bet = Bet(
        user_id=trader.user_id,
        amount=10000.0,  # Much larger than follower can afford
        odds=1.1
    )
    
    copy_trades = await copy_trading_service.execute_copy_trade(malicious_bet, [relationship])
    
    # Verify security measures applied
    if copy_trades:
        copy_trade = copy_trades[0]
        assert copy_trade.copy_amount <= follower.bankroll * 0.05, "Copy bet size should be capped"

@pytest.mark.asyncio
async def test_expert_verification_integrity():
    """Test expert verification prevents manipulation"""
    
    # Create user with suspicious betting patterns
    user = await create_test_user("suspicious_user")
    
    # Simulate suspicious activity (coordinated bets, wash trading, etc.)
    await simulate_suspicious_betting_pattern(user.user_id)
    
    # Apply for verification
    application = await expert_verification_service.apply_for_verification(user.user_id)
    
    # Run integrity checks
    integrity_result = await expert_verification_service._integrity_analysis(user.user_id)
    
    # Verify suspicious activity detected
    assert integrity_result.passed == False
    assert "suspicious_pattern" in integrity_result.flags
```

## 🚀 Implementation Phases

### Phase 1: Core Social Features (Month 1-2)
**Deliverables:**
- User profiles with performance tracking
- Follow/unfollow functionality
- Basic community feed
- Social post creation and engagement

**Acceptance Criteria:**
- User can follow/unfollow other users
- Performance metrics accurately calculated and displayed
- Community feed shows relevant content
- Users can create and interact with posts

### Phase 2: Copy Trading System (Month 2-3)
**Deliverables:**
- Copy trading relationship management
- Automated copy trade execution
- Copy trading settings and filters
- Performance tracking for copy trades

**Acceptance Criteria:**
- Copy trades execute within 30 seconds of original bet
- Copy trade sizing works correctly for all modes
- Copy trading performance tracked separately
- Risk management features prevent over-exposure

### Phase 3: Advanced Social Features (Month 3-4)
**Deliverables:**
- Personalized feed algorithm
- Leaderboards and rankings
- Advanced search and filtering
- Community moderation tools

**Acceptance Criteria:**
- Feed relevance score >0.7 for user satisfaction
- Leaderboards update in real-time
- Content moderation prevents spam/abuse
- Search results returned in <500ms

### Phase 4: Expert Program & Monetization (Month 4-5)
**Deliverables:**
- Expert verification system
- Monetization features for experts
- Premium subscriptions
- Commission tracking and payouts

**Acceptance Criteria:**
- Expert verification process completes within 5 business days
- Commission calculations 100% accurate
- Payment processing integrated
- Premium features increase user retention by 40%

## 💰 Business Impact & ROI

### Revenue Projections
- **Year 1**: $3.2M in platform revenue
  - Copy trading commissions: $1.8M
  - Premium subscriptions: $1.0M  
  - Expert monetization: $400K
- **User Growth**: 500% increase through viral/social features
- **Engagement**: 400% increase in session duration

### Cost Structure
- **Development**: $1.0M (5 months, 8 engineers)
- **Infrastructure**: $300K/year (social features, feeds, real-time)
- **Content Moderation**: $200K/year (automated + human)
- **Total Investment**: $1.5M first year

### ROI Calculation
- **Break-even**: Month 10 post-launch
- **3-Year ROI**: 520%
- **Network Effect Value**: +$25M company valuation

## ⚠️ Risk Assessment

### Technical Risks
- **Scalability**: 40% risk - Mitigation: Horizontal scaling, CDN
- **Real-time Performance**: 30% risk - Mitigation: Redis, message queues
- **Data Consistency**: 25% risk - Mitigation: ACID transactions, eventual consistency

### Business Risks
- **Regulatory Compliance**: 35% risk - Mitigation: Legal review, KYC/AML
- **Content Moderation**: 30% risk - Mitigation: AI + human moderation
- **User Trust**: 25% risk - Mitigation: Transparency, verified performance

### Mitigation Strategies
- Phased rollout with closed beta testing
- Comprehensive content moderation from day 1
- Transparent performance verification
- Strong community guidelines and enforcement

## 📊 Success Metrics & KPIs

### Social Engagement KPIs
- **Monthly Active Users**: Target 50,000 within 6 months
- **Daily Posts**: Target 1,000+ community posts daily
- **Follow Rate**: Target 15 follows per new user
- **Engagement Rate**: Target 8% (likes, comments, shares per post)

### Copy Trading KPIs
- **Copy Relationships**: Target 10,000 active relationships
- **Copy Trading Volume**: Target $5M copied within first year
- **Copy Success Rate**: Target 65%+ profitable copy relationships
- **Average Copy Size**: Target $25 per copy trade

### Business KPIs
- **Viral Coefficient**: Target 0.3+ (each user brings 0.3 new users)
- **Revenue Per User**: Target $150 annual revenue per active user
- **Retention Rate**: Target 70% monthly retention for social features
- **Expert Conversion**: Target 5% of users become verified experts

### Technical KPIs
- **Feed Generation**: <2 seconds for personalized feed
- **Copy Trade Execution**: <30 seconds from original bet
- **Real-time Updates**: <5 seconds for social notifications
- **System Uptime**: 99.9% availability during peak hours

---

**Project Owner**: Product Team  
**Technical Lead**: Backend Engineering Team  
**Stakeholders**: Engineering, Product, Legal, Community Management  
**Review Cycle**: Weekly standups, bi-weekly milestone reviews  
**Launch Target**: Q3 2025