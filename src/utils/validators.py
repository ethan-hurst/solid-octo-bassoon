"""Input validation utilities."""
import re
from typing import Any, Optional
from datetime import datetime, timedelta


def validate_email(email: str) -> bool:
    """Validate email format.
    
    Args:
        email: Email address to validate
        
    Returns:
        True if valid email format
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_username(username: str) -> bool:
    """Validate username format.
    
    Args:
        username: Username to validate
        
    Returns:
        True if valid username
    """
    # Username must be 3-20 characters, alphanumeric with underscores
    pattern = r'^[a-zA-Z0-9_]{3,20}$'
    return bool(re.match(pattern, username))


def validate_password(password: str) -> tuple[bool, Optional[str]]:
    """Validate password strength.
    
    Args:
        password: Password to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    
    if not re.search(r'[0-9]', password):
        return False, "Password must contain at least one number"
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "Password must contain at least one special character"
    
    return True, None


def validate_odds(odds: float) -> bool:
    """Validate odds value.
    
    Args:
        odds: Decimal odds value
        
    Returns:
        True if valid odds
    """
    return 1.01 <= odds <= 1000.0


def validate_probability(prob: float) -> bool:
    """Validate probability value.
    
    Args:
        prob: Probability value
        
    Returns:
        True if valid probability
    """
    return 0.0 <= prob <= 1.0


def validate_stake(stake: float, min_stake: float = 1.0, max_stake: float = 100000.0) -> bool:
    """Validate bet stake amount.
    
    Args:
        stake: Stake amount
        min_stake: Minimum allowed stake
        max_stake: Maximum allowed stake
        
    Returns:
        True if valid stake
    """
    return min_stake <= stake <= max_stake


def validate_date_range(
    start_date: datetime,
    end_date: datetime,
    max_days: int = 365
) -> tuple[bool, Optional[str]]:
    """Validate date range.
    
    Args:
        start_date: Start date
        end_date: End date
        max_days: Maximum allowed days in range
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if end_date < start_date:
        return False, "End date must be after start date"
    
    if (end_date - start_date).days > max_days:
        return False, f"Date range cannot exceed {max_days} days"
    
    if end_date > datetime.utcnow():
        return False, "End date cannot be in the future"
    
    return True, None


def sanitize_string(value: str, max_length: int = 255) -> str:
    """Sanitize string input.
    
    Args:
        value: String to sanitize
        max_length: Maximum allowed length
        
    Returns:
        Sanitized string
    """
    # Remove leading/trailing whitespace
    value = value.strip()
    
    # Limit length
    value = value[:max_length]
    
    # Remove null characters
    value = value.replace('\x00', '')
    
    return value


def validate_sport_type(sport: str) -> bool:
    """Validate sport type.
    
    Args:
        sport: Sport identifier
        
    Returns:
        True if valid sport
    """
    valid_sports = {
        "americanfootball_nfl",
        "basketball_nba",
        "baseball_mlb",
        "icehockey_nhl",
        "soccer_epl",
        "soccer_uefa_champs_league",
        "soccer_uefa_europa_league",
        "tennis_atp",
        "tennis_wta"
    }
    return sport in valid_sports


def validate_market_type(market: str) -> bool:
    """Validate betting market type.
    
    Args:
        market: Market identifier
        
    Returns:
        True if valid market
    """
    valid_markets = {"h2h", "spreads", "totals"}
    return market in valid_markets


def validate_notification_channel(channel: str) -> bool:
    """Validate notification channel.
    
    Args:
        channel: Notification channel
        
    Returns:
        True if valid channel
    """
    valid_channels = {"websocket", "email", "discord", "telegram"}
    return channel in valid_channels