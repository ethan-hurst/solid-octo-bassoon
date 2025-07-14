"""Tests for odds aggregator."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime
import httpx

from src.data_collection.odds_aggregator import OddsAggregator, OddsAPIError
from src.models.schemas import SportType, MarketOdds, BetType


@pytest.mark.asyncio
async def test_get_sports(mock_cache_manager):
    """Test fetching available sports."""
    # Mock API response
    mock_sports = [
        {"key": "americanfootball_nfl", "active": True, "title": "NFL"},
        {"key": "basketball_nba", "active": True, "title": "NBA"}
    ]
    
    with patch("httpx.AsyncClient") as mock_client:
        mock_response = MagicMock()
        mock_response.json.return_value = mock_sports
        mock_response.raise_for_status = MagicMock()
        
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(
            return_value=mock_response
        )
        
        aggregator = OddsAggregator(cache=mock_cache_manager)
        sports = await aggregator.get_sports()
        
        assert len(sports) == 2
        assert sports[0]["key"] == "americanfootball_nfl"


@pytest.mark.asyncio
async def test_fetch_odds_from_cache(mock_cache_manager, mock_odds_response):
    """Test fetching odds from cache."""
    # Setup cache to return data
    cached_data = [
        {
            "game_id": "test_game_123",
            "sport": "NFL",
            "home_team": "Team A",
            "away_team": "Team B",
            "commence_time": datetime.utcnow().isoformat(),
            "bet_type": "h2h",
            "bookmaker_odds": [
                {
                    "bookmaker": "DraftKings",
                    "odds": 2.10,
                    "last_update": datetime.utcnow().isoformat()
                }
            ]
        }
    ]
    
    mock_cache_manager.get = AsyncMock(return_value=cached_data)
    
    aggregator = OddsAggregator(cache=mock_cache_manager)
    odds_list = await aggregator.fetch_odds(SportType.NFL)
    
    assert len(odds_list) == 1
    assert isinstance(odds_list[0], MarketOdds)
    mock_cache_manager.get.assert_called_once()


@pytest.mark.asyncio
async def test_fetch_odds_from_api(mock_cache_manager, mock_odds_response):
    """Test fetching odds from API when not cached."""
    mock_cache_manager.get = AsyncMock(return_value=None)
    
    with patch("httpx.AsyncClient") as mock_client:
        mock_response = MagicMock()
        mock_response.json.return_value = mock_odds_response
        mock_response.raise_for_status = MagicMock()
        mock_response.headers = {
            "x-requests-remaining": "100",
            "x-requests-used": "50"
        }
        
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(
            return_value=mock_response
        )
        
        aggregator = OddsAggregator(cache=mock_cache_manager)
        odds_list = await aggregator.fetch_odds(SportType.NFL)
        
        assert len(odds_list) > 0
        assert aggregator.requests_remaining == 100
        assert aggregator.requests_used == 50
        
        # Verify cache was set
        mock_cache_manager.set.assert_called_once()


@pytest.mark.asyncio
async def test_fetch_odds_rate_limit_retry(mock_cache_manager):
    """Test rate limit retry logic."""
    mock_cache_manager.get = AsyncMock(return_value=None)
    
    with patch("httpx.AsyncClient") as mock_client:
        # First call returns 429, second succeeds
        mock_response_429 = MagicMock()
        mock_response_429.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Rate limited",
            request=MagicMock(),
            response=MagicMock(status_code=429)
        )
        
        mock_response_success = MagicMock()
        mock_response_success.json.return_value = []
        mock_response_success.raise_for_status = MagicMock()
        mock_response_success.headers = {}
        
        mock_get = AsyncMock(side_effect=[mock_response_429, mock_response_success])
        mock_client.return_value.__aenter__.return_value.get = mock_get
        
        with patch("asyncio.sleep", new_callable=AsyncMock):
            aggregator = OddsAggregator(cache=mock_cache_manager)
            odds_list = await aggregator.fetch_odds(SportType.NFL)
            
            assert mock_get.call_count == 2
            assert isinstance(odds_list, list)


@pytest.mark.asyncio
async def test_fetch_odds_invalid_api_key(mock_cache_manager):
    """Test handling invalid API key."""
    mock_cache_manager.get = AsyncMock(return_value=None)
    
    with patch("httpx.AsyncClient") as mock_client:
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Unauthorized",
            request=MagicMock(),
            response=MagicMock(status_code=401)
        )
        
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(
            return_value=mock_response
        )
        
        aggregator = OddsAggregator(cache=mock_cache_manager)
        
        with pytest.raises(OddsAPIError, match="Invalid API key"):
            await aggregator.fetch_odds(SportType.NFL)


@pytest.mark.asyncio
async def test_fetch_all_sports_odds(mock_cache_manager):
    """Test fetching odds for multiple sports."""
    mock_cache_manager.get = AsyncMock(return_value=None)
    
    with patch("httpx.AsyncClient") as mock_client:
        mock_response = MagicMock()
        mock_response.json.return_value = []
        mock_response.raise_for_status = MagicMock()
        mock_response.headers = {}
        
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(
            return_value=mock_response
        )
        
        aggregator = OddsAggregator(cache=mock_cache_manager)
        sports = [SportType.NFL, SportType.NBA]
        
        odds_by_sport = await aggregator.fetch_all_sports_odds(sports)
        
        assert len(odds_by_sport) == 2
        assert SportType.NFL in odds_by_sport
        assert SportType.NBA in odds_by_sport


@pytest.mark.asyncio
async def test_parse_odds_response(mock_cache_manager, mock_odds_response):
    """Test parsing odds response."""
    aggregator = OddsAggregator(cache=mock_cache_manager)
    
    odds_list = aggregator._parse_odds_response(
        mock_odds_response,
        SportType.NFL
    )
    
    assert len(odds_list) > 0
    assert odds_list[0].sport == SportType.NFL
    assert odds_list[0].home_team == "Kansas City Chiefs"
    assert odds_list[0].away_team == "Buffalo Bills"
    assert odds_list[0].bet_type == BetType.MONEYLINE
    assert len(odds_list[0].bookmaker_odds) > 0


@pytest.mark.asyncio
async def test_request_timeout(mock_cache_manager):
    """Test handling request timeout."""
    mock_cache_manager.get = AsyncMock(return_value=None)
    
    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(
            side_effect=httpx.TimeoutException("Request timed out")
        )
        
        aggregator = OddsAggregator(cache=mock_cache_manager)
        aggregator.retry_attempts = 1  # Reduce retries for test
        
        with pytest.raises(OddsAPIError):
            await aggregator.fetch_odds(SportType.NFL)