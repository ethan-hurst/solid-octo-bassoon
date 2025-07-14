"""The Odds API client for aggregating sports betting odds."""
import asyncio
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
import httpx
from httpx import HTTPStatusError

from src.models.schemas import (
    SportType, MarketOdds, BookmakerOdds, BetType, OddsResponse
)
from src.data_collection.cache_manager import CacheManager
from src.config.settings import settings

logger = logging.getLogger(__name__)


class OddsAPIError(Exception):
    """Custom exception for Odds API errors."""
    pass


class OddsAggregator:
    """Aggregates odds data from The Odds API."""
    
    def __init__(
        self, 
        api_key: Optional[str] = None,
        cache: Optional[CacheManager] = None
    ):
        """Initialize odds aggregator.
        
        Args:
            api_key: The Odds API key, defaults to settings
            cache: Cache manager instance
        """
        self.api_key = api_key or settings.odds_api_key
        self.base_url = settings.odds_api_base_url
        self.cache = cache or CacheManager()
        self.timeout = settings.odds_api_timeout
        self.retry_attempts = settings.odds_api_retry_attempts
        
        # Track API usage
        self._requests_remaining = None
        self._requests_used = None
    
    async def get_sports(self, active_only: bool = True) -> List[Dict[str, Any]]:
        """Get list of available sports.
        
        Args:
            active_only: Only return in-season sports
            
        Returns:
            List of sport dictionaries
        """
        cache_key = f"sports:{'active' if active_only else 'all'}"
        cached = await self.cache.get(cache_key)
        if cached:
            return cached
        
        params = {"apiKey": self.api_key}
        if active_only:
            params["all"] = "false"
        
        async with httpx.AsyncClient() as client:
            response = await self._make_request(
                client,
                f"{self.base_url}/sports",
                params=params
            )
        
        sports = response.json()
        await self.cache.set(cache_key, sports, ttl=3600)  # Cache for 1 hour
        
        return sports
    
    async def fetch_odds(
        self,
        sport: SportType,
        markets: Optional[List[str]] = None,
        regions: Optional[List[str]] = None,
        odds_format: str = "decimal"
    ) -> List[MarketOdds]:
        """Fetch odds for a specific sport and markets.
        
        Args:
            sport: Sport type to fetch odds for
            markets: List of market types (h2h, spreads, totals)
            regions: List of bookmaker regions (us, uk, au, eu)
            odds_format: Format for odds (decimal, american)
            
        Returns:
            List of MarketOdds objects
        """
        if markets is None:
            markets = ["h2h", "spreads", "totals"]
        
        if regions is None:
            regions = ["us"]
        
        # Check cache first
        cache_key = f"odds:{sport.value}:{','.join(markets)}:{','.join(regions)}"
        cached = await self.cache.get(cache_key)
        if cached:
            return [MarketOdds(**odds) for odds in cached]
        
        params = {
            "apiKey": self.api_key,
            "regions": ",".join(regions),
            "markets": ",".join(markets),
            "oddsFormat": odds_format
        }
        
        async with httpx.AsyncClient() as client:
            response = await self._make_request(
                client,
                f"{self.base_url}/sports/{sport.value}/odds",
                params=params
            )
        
        # Parse response
        data = response.json()
        odds_list = self._parse_odds_response(data, sport)
        
        # Cache the results
        cache_data = [odds.model_dump() for odds in odds_list]
        await self.cache.set(cache_key, cache_data, ttl=settings.cache_ttl_seconds)
        
        return odds_list
    
    async def fetch_all_sports_odds(
        self,
        sports: Optional[List[SportType]] = None,
        markets: Optional[List[str]] = None
    ) -> Dict[SportType, List[MarketOdds]]:
        """Fetch odds for multiple sports concurrently.
        
        Args:
            sports: List of sports to fetch, defaults to all
            markets: Market types to fetch
            
        Returns:
            Dictionary mapping sport to odds
        """
        if sports is None:
            sports = list(SportType)
        
        # Create tasks for concurrent fetching
        tasks = []
        for sport in sports:
            task = self.fetch_odds(sport, markets)
            tasks.append(task)
        
        # Execute concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Build result dictionary
        odds_by_sport = {}
        for sport, result in zip(sports, results):
            if isinstance(result, Exception):
                logger.error(f"Error fetching odds for {sport}: {result}")
                odds_by_sport[sport] = []
            else:
                odds_by_sport[sport] = result
        
        return odds_by_sport
    
    async def _make_request(
        self,
        client: httpx.AsyncClient,
        url: str,
        params: Dict[str, Any]
    ) -> httpx.Response:
        """Make HTTP request with retry logic.
        
        Args:
            client: HTTP client
            url: Request URL
            params: Query parameters
            
        Returns:
            HTTP response
            
        Raises:
            OddsAPIError: If request fails after retries
        """
        last_error = None
        
        for attempt in range(self.retry_attempts):
            try:
                response = await client.get(
                    url,
                    params=params,
                    timeout=self.timeout
                )
                
                # Check rate limit headers
                self._update_rate_limits(response.headers)
                
                response.raise_for_status()
                return response
                
            except HTTPStatusError as e:
                if e.response.status_code == 429:  # Rate limited
                    wait_time = 2 ** attempt
                    logger.warning(
                        f"Rate limited, waiting {wait_time}s before retry"
                    )
                    await asyncio.sleep(wait_time)
                    last_error = e
                    continue
                elif e.response.status_code == 401:
                    raise OddsAPIError("Invalid API key")
                else:
                    raise OddsAPIError(f"API error: {e.response.status_code}")
            
            except httpx.TimeoutException:
                logger.warning(f"Request timeout, attempt {attempt + 1}")
                last_error = OddsAPIError("Request timeout")
                continue
            
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                last_error = e
                continue
        
        raise last_error or OddsAPIError("Failed after retries")
    
    def _parse_odds_response(
        self,
        data: List[Dict[str, Any]],
        sport: SportType
    ) -> List[MarketOdds]:
        """Parse API response into MarketOdds objects.
        
        Args:
            data: Raw API response data
            sport: Sport type
            
        Returns:
            List of MarketOdds objects
        """
        odds_list = []
        
        for game in data:
            game_id = game.get("id", "")
            home_team = game.get("home_team", "")
            away_team = game.get("away_team", "")
            commence_time = datetime.fromisoformat(
                game.get("commence_time", "").replace("Z", "+00:00")
            )
            
            # Process each bookmaker
            for bookmaker_data in game.get("bookmakers", []):
                bookmaker_name = bookmaker_data.get("key", "")
                
                # Process each market type
                for market_data in bookmaker_data.get("markets", []):
                    market_key = market_data.get("key", "")
                    
                    # Map to our BetType enum
                    try:
                        bet_type = BetType(market_key)
                    except ValueError:
                        logger.warning(f"Unknown market type: {market_key}")
                        continue
                    
                    # Extract odds
                    bookmaker_odds = []
                    for outcome in market_data.get("outcomes", []):
                        if outcome.get("name") == home_team:
                            odds_value = outcome.get("price", 0)
                            if odds_value > 1.0:
                                bookmaker_odds.append(
                                    BookmakerOdds(
                                        bookmaker=bookmaker_name,
                                        odds=odds_value,
                                        last_update=datetime.utcnow()
                                    )
                                )
                    
                    if bookmaker_odds:
                        market_odds = MarketOdds(
                            game_id=game_id,
                            sport=sport,
                            home_team=home_team,
                            away_team=away_team,
                            commence_time=commence_time,
                            bet_type=bet_type,
                            bookmaker_odds=bookmaker_odds
                        )
                        odds_list.append(market_odds)
        
        return odds_list
    
    def _update_rate_limits(self, headers: Dict[str, str]) -> None:
        """Update rate limit tracking from response headers.
        
        Args:
            headers: Response headers
        """
        if "x-requests-remaining" in headers:
            self._requests_remaining = int(headers["x-requests-remaining"])
        
        if "x-requests-used" in headers:
            self._requests_used = int(headers["x-requests-used"])
        
        if self._requests_remaining is not None:
            logger.info(
                f"API requests - Used: {self._requests_used}, "
                f"Remaining: {self._requests_remaining}"
            )
    
    @property
    def requests_remaining(self) -> Optional[int]:
        """Get number of API requests remaining."""
        return self._requests_remaining
    
    @property
    def requests_used(self) -> Optional[int]:
        """Get number of API requests used."""
        return self._requests_used