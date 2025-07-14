"""Unit tests for live data ingestion service."""
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
import aiohttp

from src.live_betting.data_ingestion import (
    DataSource, LiveDataIngestionService, MockDataProvider,
    SportsDataAPIProvider, LiveDataAggregator
)
from src.models.live_schemas import (
    LiveGameState, LiveOdds, LiveEvent, ScoreUpdate,
    LiveEventType, LiveBetType
)


class TestDataSource:
    """Test DataSource base class."""
    
    @pytest.mark.asyncio
    async def test_connect_disconnect(self):
        """Test connection lifecycle."""
        source = DataSource("test", "http://test.com", "api_key")
        assert source.session is None
        assert not source.is_connected
        
        await source.connect()
        assert source.session is not None
        assert source.is_connected
        
        await source.disconnect()
        assert not source.is_connected
    
    @pytest.mark.asyncio
    async def test_fetch_data_success(self):
        """Test successful data fetch."""
        source = DataSource("test", "http://test.com")
        
        with patch('aiohttp.ClientSession') as mock_session:
            mock_response = AsyncMock()
            mock_response.json = AsyncMock(return_value={"data": "test"})
            mock_response.raise_for_status = Mock()
            
            mock_session.return_value.get = AsyncMock(return_value=mock_response)
            source.session = mock_session.return_value
            
            result = await source.fetch_data("endpoint")
            assert result == {"data": "test"}
    
    @pytest.mark.asyncio
    async def test_fetch_data_error(self):
        """Test data fetch with error."""
        source = DataSource("test", "http://test.com")
        
        with patch('aiohttp.ClientSession') as mock_session:
            mock_session.return_value.get = AsyncMock(
                side_effect=aiohttp.ClientError("Connection error")
            )
            source.session = mock_session.return_value
            
            with pytest.raises(aiohttp.ClientError):
                await source.fetch_data("endpoint")


class TestMockDataProvider:
    """Test MockDataProvider for development/testing."""
    
    @pytest.mark.asyncio
    async def test_get_live_games(self):
        """Test getting live games."""
        provider = MockDataProvider()
        games = await provider.get_live_games("NBA")
        
        assert len(games) > 0
        assert all(isinstance(game, LiveGameState) for game in games)
        assert all(game.sport == "NBA" for game in games)
    
    @pytest.mark.asyncio
    async def test_stream_game_updates(self):
        """Test streaming game updates."""
        provider = MockDataProvider()
        game_id = "mock_game_1"
        updates = []
        
        async for update in provider.stream_game_updates(game_id):
            updates.append(update)
            if len(updates) >= 3:
                break
        
        assert len(updates) == 3
        assert all(update["game_id"] == game_id for update in updates)
    
    @pytest.mark.asyncio
    async def test_generate_random_event(self):
        """Test random event generation."""
        provider = MockDataProvider()
        event = provider._generate_random_event("game_123", "NBA")
        
        assert isinstance(event, LiveEvent)
        assert event.game_id == "game_123"
        assert event.event_type in LiveEventType.__members__.values()


class TestSportsDataAPIProvider:
    """Test real sports data API provider."""
    
    @pytest.mark.asyncio
    async def test_initialization(self):
        """Test provider initialization."""
        provider = SportsDataAPIProvider("key", "http://api.test.com")
        assert provider.api_key == "key"
        assert provider.base_url == "http://api.test.com"
    
    @pytest.mark.asyncio
    async def test_get_live_games_api_call(self):
        """Test API call for live games."""
        provider = SportsDataAPIProvider("key", "http://api.test.com")
        
        mock_response = {
            "games": [
                {
                    "game_id": "123",
                    "sport": "NBA",
                    "home_team": "Lakers",
                    "away_team": "Celtics",
                    "home_score": 100,
                    "away_score": 95,
                    "period": 4,
                    "time_remaining": "2:30",
                    "status": "LIVE",
                    "start_time": datetime.utcnow().isoformat()
                }
            ]
        }
        
        with patch.object(provider, 'fetch_data', AsyncMock(return_value=mock_response)):
            games = await provider.get_live_games("NBA")
            assert len(games) == 1
            assert games[0].game_id == "123"
            assert games[0].home_team == "Lakers"


class TestLiveDataIngestionService:
    """Test main data ingestion service."""
    
    @pytest.mark.asyncio
    async def test_add_remove_provider(self):
        """Test adding and removing providers."""
        service = LiveDataIngestionService()
        provider = MockDataProvider()
        
        service.add_provider("mock", provider)
        assert "mock" in service.providers
        
        service.remove_provider("mock")
        assert "mock" not in service.providers
    
    @pytest.mark.asyncio
    async def test_ingest_live_games(self):
        """Test ingesting games from multiple providers."""
        service = LiveDataIngestionService()
        provider1 = MockDataProvider()
        provider2 = MockDataProvider()
        
        service.add_provider("mock1", provider1)
        service.add_provider("mock2", provider2)
        
        games = await service.ingest_live_games("NBA")
        assert len(games) > 0
        assert all(isinstance(game, LiveGameState) for game in games)
    
    @pytest.mark.asyncio
    async def test_stream_game_updates_multiple_providers(self):
        """Test streaming from multiple providers."""
        service = LiveDataIngestionService()
        provider = MockDataProvider()
        service.add_provider("mock", provider)
        
        updates = []
        async for update in service.stream_game_updates("game_1"):
            updates.append(update)
            if len(updates) >= 5:
                break
        
        assert len(updates) == 5
    
    @pytest.mark.asyncio
    async def test_provider_failure_handling(self):
        """Test handling provider failures gracefully."""
        service = LiveDataIngestionService()
        
        # Add failing provider
        failing_provider = Mock()
        failing_provider.get_live_games = AsyncMock(
            side_effect=Exception("Provider error")
        )
        
        # Add working provider
        working_provider = MockDataProvider()
        
        service.add_provider("failing", failing_provider)
        service.add_provider("working", working_provider)
        
        # Should still get games from working provider
        games = await service.ingest_live_games("NBA")
        assert len(games) > 0


class TestLiveDataAggregator:
    """Test data aggregation functionality."""
    
    def test_merge_game_states(self):
        """Test merging game states from multiple sources."""
        aggregator = LiveDataAggregator()
        
        games1 = [
            LiveGameState(
                game_id="1",
                sport="NBA",
                home_team="Lakers",
                away_team="Celtics",
                home_score=100,
                away_score=95,
                period=4,
                time_remaining="2:00",
                status="LIVE",
                start_time=datetime.utcnow()
            )
        ]
        
        games2 = [
            LiveGameState(
                game_id="1",
                sport="NBA",
                home_team="Lakers",
                away_team="Celtics",
                home_score=102,
                away_score=95,
                period=4,
                time_remaining="1:30",
                status="LIVE",
                start_time=datetime.utcnow()
            )
        ]
        
        merged = aggregator.merge_game_states([games1, games2])
        assert len(merged) == 1
        # Should take most recent update
        assert merged[0].home_score == 102
        assert merged[0].time_remaining == "1:30"
    
    def test_merge_odds(self):
        """Test merging odds from multiple sources."""
        aggregator = LiveDataAggregator()
        
        odds1 = [
            LiveOdds(
                odds_id="1",
                game_id="game1",
                bookmaker="BookA",
                bet_type=LiveBetType.MONEYLINE,
                selection="Lakers",
                odds=1.85,
                timestamp=datetime.utcnow()
            )
        ]
        
        odds2 = [
            LiveOdds(
                odds_id="2",
                game_id="game1",
                bookmaker="BookB",
                bet_type=LiveBetType.MONEYLINE,
                selection="Lakers",
                odds=1.90,
                timestamp=datetime.utcnow()
            )
        ]
        
        merged = aggregator.merge_odds([odds1, odds2])
        assert len(merged) == 2  # Should keep both bookmaker odds
        assert {o.bookmaker for o in merged} == {"BookA", "BookB"}