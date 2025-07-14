"""Live data ingestion service for real-time sports data."""
import asyncio
import logging
from typing import Dict, List, Optional, AsyncIterator, Any
from datetime import datetime, timedelta
import aiohttp
import json

from src.models.live_schemas import (
    LiveGameState, LiveOdds, LiveEvent, ScoreUpdate,
    LiveEventType, LiveBetType
)
from src.config.settings import settings

logger = logging.getLogger(__name__)


class DataSource:
    """Base class for live data sources."""
    
    def __init__(self, name: str, base_url: str, api_key: Optional[str] = None):
        self.name = name
        self.base_url = base_url
        self.api_key = api_key
        self.session: Optional[aiohttp.ClientSession] = None
        self.is_connected = False
        
    async def connect(self) -> None:
        """Establish connection to data source."""
        if not self.session:
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(timeout=timeout)
        self.is_connected = True
        logger.info(f"Connected to {self.name}")
    
    async def disconnect(self) -> None:
        """Close connection to data source."""
        if self.session:
            await self.session.close()
        self.is_connected = False
        logger.info(f"Disconnected from {self.name}")
    
    async def fetch_data(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Fetch data from API endpoint."""
        if not self.session:
            await self.connect()
        
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        headers = {}
        
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        try:
            async with self.session.get(url, headers=headers, params=kwargs) as response:
                response.raise_for_status()
                return await response.json()
        except Exception as e:
            logger.error(f"Error fetching from {self.name}: {e}")
            raise


class ESPNLiveDataSource(DataSource):
    """ESPN Live API data source."""
    
    def __init__(self):
        super().__init__(
            name="ESPN Live",
            base_url="http://site.api.espn.com/apis/site/v2/sports"
        )
    
    async def get_live_games(self, sport: str) -> List[Dict[str, Any]]:
        """Get live games for a sport."""
        sport_mapping = {
            "NFL": "football/nfl",
            "NBA": "basketball/nba", 
            "MLB": "baseball/mlb",
            "NHL": "hockey/nhl"
        }
        
        sport_path = sport_mapping.get(sport)
        if not sport_path:
            raise ValueError(f"Sport {sport} not supported")
        
        data = await self.fetch_data(f"{sport_path}/scoreboard")
        return data.get("events", [])
    
    async def get_game_details(self, game_id: str, sport: str) -> Dict[str, Any]:
        """Get detailed game information."""
        sport_mapping = {
            "NFL": "football/nfl",
            "NBA": "basketball/nba",
            "MLB": "baseball/mlb", 
            "NHL": "hockey/nhl"
        }
        
        sport_path = sport_mapping.get(sport)
        if not sport_path:
            raise ValueError(f"Sport {sport} not supported")
        
        data = await self.fetch_data(f"{sport_path}/summary", eventId=game_id)
        return data
    
    def parse_live_game(self, game_data: Dict[str, Any]) -> LiveGameState:
        """Parse ESPN game data into LiveGameState."""
        game_id = game_data["id"]
        
        # Extract team information
        competitions = game_data.get("competitions", [{}])
        competition = competitions[0] if competitions else {}
        competitors = competition.get("competitors", [])
        
        home_team = None
        away_team = None
        home_score = 0
        away_score = 0
        
        for competitor in competitors:
            team_name = competitor.get("team", {}).get("displayName", "")
            score = int(competitor.get("score", 0))
            
            if competitor.get("homeAway") == "home":
                home_team = team_name
                home_score = score
            else:
                away_team = team_name
                away_score = score
        
        # Extract game status and clock
        status = competition.get("status", {})
        clock = status.get("displayClock", "0:00")
        period = status.get("period", 1)
        is_active = status.get("type", {}).get("state") == "in"
        
        return LiveGameState(
            game_id=game_id,
            sport=game_data.get("sport", {}).get("name", "Unknown"),
            home_team=home_team or "Home",
            away_team=away_team or "Away",
            current_score={"home": home_score, "away": away_score},
            game_clock=clock,
            quarter_period=period,
            is_active=is_active
        )


class TheOddsAPILiveSource(DataSource):
    """The Odds API live odds source."""
    
    def __init__(self, api_key: str):
        super().__init__(
            name="The Odds API Live",
            base_url="https://api.the-odds-api.com/v4",
            api_key=api_key
        )
        self.requests_remaining = 500  # Track API usage
    
    async def get_live_odds(self, sport: str) -> List[Dict[str, Any]]:
        """Get live odds for a sport."""
        sport_mapping = {
            "NFL": "americanfootball_nfl",
            "NBA": "basketball_nba",
            "MLB": "baseball_mlb",
            "NHL": "icehockey_nhl"
        }
        
        sport_key = sport_mapping.get(sport)
        if not sport_key:
            raise ValueError(f"Sport {sport} not supported")
        
        params = {
            "apiKey": self.api_key,
            "regions": "us",
            "markets": "h2h,spreads,totals",
            "oddsFormat": "decimal",
            "dateFormat": "iso"
        }
        
        data = await self.fetch_data(f"sports/{sport_key}/odds", **params)
        
        # Update remaining requests from headers
        if hasattr(data, "_headers"):
            remaining = data._headers.get("x-requests-remaining")
            if remaining:
                self.requests_remaining = int(remaining)
        
        return data
    
    def parse_live_odds(self, odds_data: Dict[str, Any]) -> List[LiveOdds]:
        """Parse odds API data into LiveOdds objects."""
        live_odds = []
        
        for event in odds_data:
            game_id = event["id"]
            
            for bookmaker in event.get("bookmakers", []):
                bookmaker_name = bookmaker["title"]
                
                for market in bookmaker.get("markets", []):
                    market_key = market["key"]
                    bet_type = self._map_market_to_bet_type(market_key)
                    
                    for outcome in market.get("outcomes", []):
                        live_odds.append(LiveOdds(
                            game_id=game_id,
                            bookmaker=bookmaker_name,
                            bet_type=bet_type,
                            selection=outcome["name"],
                            odds=float(outcome["price"]),
                            line=outcome.get("point"),
                            timestamp=datetime.utcnow()
                        ))
        
        return live_odds
    
    def _map_market_to_bet_type(self, market_key: str) -> LiveBetType:
        """Map market key to bet type."""
        mapping = {
            "h2h": LiveBetType.MONEYLINE,
            "spreads": LiveBetType.SPREAD,
            "totals": LiveBetType.TOTAL
        }
        return mapping.get(market_key, LiveBetType.MONEYLINE)


class LiveDataPipeline:
    """Process multiple real-time data streams."""
    
    def __init__(self):
        self.data_sources: Dict[str, DataSource] = {}
        self.is_running = False
        self.update_interval = 5  # seconds
        
    async def add_data_source(self, name: str, source: DataSource) -> None:
        """Add a data source to the pipeline."""
        await source.connect()
        self.data_sources[name] = source
        logger.info(f"Added data source: {name}")
    
    async def remove_data_source(self, name: str) -> None:
        """Remove a data source from the pipeline."""
        if name in self.data_sources:
            await self.data_sources[name].disconnect()
            del self.data_sources[name]
            logger.info(f"Removed data source: {name}")
    
    async def start(self) -> None:
        """Start the data ingestion pipeline."""
        self.is_running = True
        logger.info("Starting live data pipeline")
        
        # Start background tasks for each data source
        tasks = []
        for name, source in self.data_sources.items():
            task = asyncio.create_task(self._poll_data_source(name, source))
            tasks.append(task)
        
        try:
            await asyncio.gather(*tasks)
        except Exception as e:
            logger.error(f"Pipeline error: {e}")
        finally:
            self.is_running = False
    
    async def stop(self) -> None:
        """Stop the data ingestion pipeline."""
        self.is_running = False
        
        # Disconnect all sources
        for source in self.data_sources.values():
            await source.disconnect()
        
        logger.info("Stopped live data pipeline")
    
    async def _poll_data_source(self, name: str, source: DataSource) -> None:
        """Continuously poll a data source."""
        while self.is_running:
            try:
                await self._process_data_source(name, source)
                await asyncio.sleep(self.update_interval)
            except Exception as e:
                logger.error(f"Error polling {name}: {e}")
                await asyncio.sleep(self.update_interval * 2)  # Back off on error
    
    async def _process_data_source(self, name: str, source: DataSource) -> None:
        """Process data from a specific source."""
        if isinstance(source, ESPNLiveDataSource):
            await self._process_espn_data(source)
        elif isinstance(source, TheOddsAPILiveSource):
            await self._process_odds_data(source)
    
    async def _process_espn_data(self, source: ESPNLiveDataSource) -> None:
        """Process ESPN live game data."""
        sports = ["NFL", "NBA", "MLB", "NHL"]
        
        for sport in sports:
            try:
                games = await source.get_live_games(sport)
                
                for game_data in games:
                    live_game = source.parse_live_game(game_data)
                    
                    # Emit live game update event
                    await self._emit_game_update(live_game)
                    
            except Exception as e:
                logger.error(f"Error processing ESPN {sport} data: {e}")
    
    async def _process_odds_data(self, source: TheOddsAPILiveSource) -> None:
        """Process live odds data."""
        sports = ["NFL", "NBA", "MLB", "NHL"]
        
        for sport in sports:
            try:
                odds_data = await source.get_live_odds(sport)
                live_odds = source.parse_live_odds(odds_data)
                
                for odds in live_odds:
                    # Emit odds update event
                    await self._emit_odds_update(odds)
                    
            except Exception as e:
                logger.error(f"Error processing odds {sport} data: {e}")
    
    async def _emit_game_update(self, game_state: LiveGameState) -> None:
        """Emit game state update event."""
        # This would integrate with the event system
        logger.debug(f"Game update: {game_state.game_id} - {game_state.current_score}")
    
    async def _emit_odds_update(self, odds: LiveOdds) -> None:
        """Emit odds update event."""
        # This would integrate with the event system
        logger.debug(f"Odds update: {odds.game_id} - {odds.bookmaker} - {odds.odds}")
    
    async def ingest_live_data(self, sources: List[str]) -> Dict[str, Any]:
        """Ingest and normalize data from multiple sources."""
        processed_data = {}
        
        for source_name in sources:
            if source_name in self.data_sources:
                source = self.data_sources[source_name]
                try:
                    # Process each source type
                    if isinstance(source, ESPNLiveDataSource):
                        data = await self._get_espn_snapshot()
                    elif isinstance(source, TheOddsAPILiveSource):
                        data = await self._get_odds_snapshot()
                    else:
                        data = {}
                    
                    processed_data[source_name] = data
                    
                except Exception as e:
                    logger.error(f"Error ingesting from {source_name}: {e}")
                    processed_data[source_name] = None
        
        return processed_data
    
    async def _get_espn_snapshot(self) -> Dict[str, Any]:
        """Get current ESPN data snapshot."""
        espn_source = None
        
        for source in self.data_sources.values():
            if isinstance(source, ESPNLiveDataSource):
                espn_source = source
                break
        
        if not espn_source:
            return {}
        
        snapshot = {}
        sports = ["NFL", "NBA", "MLB", "NHL"]
        
        for sport in sports:
            try:
                games = await espn_source.get_live_games(sport)
                snapshot[sport] = [espn_source.parse_live_game(game) for game in games]
            except Exception as e:
                logger.error(f"Error getting ESPN {sport} snapshot: {e}")
                snapshot[sport] = []
        
        return snapshot
    
    async def _get_odds_snapshot(self) -> Dict[str, Any]:
        """Get current odds data snapshot."""
        odds_source = None
        
        for source in self.data_sources.values():
            if isinstance(source, TheOddsAPILiveSource):
                odds_source = source
                break
        
        if not odds_source:
            return {}
        
        snapshot = {}
        sports = ["NFL", "NBA", "MLB", "NHL"]
        
        for sport in sports:
            try:
                odds_data = await odds_source.get_live_odds(sport)
                snapshot[sport] = odds_source.parse_live_odds(odds_data)
            except Exception as e:
                logger.error(f"Error getting odds {sport} snapshot: {e}")
                snapshot[sport] = []
        
        return snapshot
    
    async def validate_data_quality(self, data: Dict[str, Any]) -> Dict[str, bool]:
        """Ensure data accuracy and detect anomalies."""
        validation_results = {}
        
        for source_name, source_data in data.items():
            if source_data is None:
                validation_results[source_name] = False
                continue
            
            # Basic validation checks
            is_valid = True
            
            try:
                # Check data freshness (within last 10 minutes)
                if isinstance(source_data, dict):
                    for sport_data in source_data.values():
                        if isinstance(sport_data, list):
                            for item in sport_data:
                                if hasattr(item, 'timestamp'):
                                    age = datetime.utcnow() - item.timestamp
                                    if age > timedelta(minutes=10):
                                        is_valid = False
                                        break
                
                # Check for required fields
                if not source_data:
                    is_valid = False
                
            except Exception as e:
                logger.error(f"Validation error for {source_name}: {e}")
                is_valid = False
            
            validation_results[source_name] = is_valid
        
        return validation_results
    
    async def merge_data_streams(self, data_streams: Dict[str, Any]) -> Dict[str, Any]:
        """Merge multiple data sources into unified game state."""
        unified_data = {
            "games": {},
            "odds": {},
            "metadata": {
                "sources": list(data_streams.keys()),
                "updated_at": datetime.utcnow(),
                "quality_scores": await self.validate_data_quality(data_streams)
            }
        }
        
        # Merge game data from ESPN
        for source_name, source_data in data_streams.items():
            if source_data is None:
                continue
                
            if "espn" in source_name.lower():
                # Process ESPN game data
                for sport, games in source_data.items():
                    for game in games:
                        if hasattr(game, 'game_id'):
                            unified_data["games"][game.game_id] = {
                                "state": game,
                                "sport": sport,
                                "source": source_name
                            }
            
            elif "odds" in source_name.lower():
                # Process odds data
                for sport, odds_list in source_data.items():
                    for odds in odds_list:
                        if hasattr(odds, 'game_id'):
                            game_id = odds.game_id
                            if game_id not in unified_data["odds"]:
                                unified_data["odds"][game_id] = []
                            unified_data["odds"][game_id].append(odds)
        
        return unified_data