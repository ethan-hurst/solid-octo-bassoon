"""Feature engineering for sports betting ML models."""
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, LabelEncoder

from src.models.schemas import SportType, MarketOdds

logger = logging.getLogger(__name__)


class FeatureEngineer:
    """Handles feature engineering for sports betting models."""
    
    def __init__(self):
        """Initialize feature engineer with scalers and encoders."""
        self.scaler = StandardScaler()
        self.team_encoder = LabelEncoder()
        self.feature_names: List[str] = []
        self._is_fitted = False
    
    def extract_features(
        self,
        market_odds: MarketOdds,
        historical_data: Optional[pd.DataFrame] = None,
        weather_data: Optional[Dict[str, Any]] = None,
        injury_data: Optional[Dict[str, Any]] = None
    ) -> np.ndarray:
        """Extract features from market odds and additional data.
        
        Args:
            market_odds: Current market odds
            historical_data: Historical performance data
            weather_data: Weather conditions (if applicable)
            injury_data: Injury reports
            
        Returns:
            Feature vector as numpy array
        """
        features = {}
        
        # Basic features
        features.update(self._extract_basic_features(market_odds))
        
        # Odds-based features
        features.update(self._extract_odds_features(market_odds))
        
        # Time-based features
        features.update(self._extract_time_features(market_odds))
        
        # Historical features if available
        if historical_data is not None:
            features.update(self._extract_historical_features(
                market_odds, historical_data
            ))
        
        # Sport-specific features
        features.update(self._extract_sport_specific_features(
            market_odds, weather_data, injury_data
        ))
        
        # Convert to array
        if not self._is_fitted:
            self.feature_names = list(features.keys())
        
        feature_vector = np.array([features[name] for name in self.feature_names])
        
        return feature_vector
    
    def _extract_basic_features(self, market_odds: MarketOdds) -> Dict[str, float]:
        """Extract basic game features.
        
        Args:
            market_odds: Market odds data
            
        Returns:
            Dictionary of basic features
        """
        features = {}
        
        # Sport type as one-hot encoding
        for sport in SportType:
            features[f"sport_{sport.value}"] = float(market_odds.sport == sport)
        
        # Market type
        features["is_moneyline"] = float(market_odds.bet_type.value == "h2h")
        features["is_spread"] = float(market_odds.bet_type.value == "spreads")
        features["is_total"] = float(market_odds.bet_type.value == "totals")
        
        return features
    
    def _extract_odds_features(self, market_odds: MarketOdds) -> Dict[str, float]:
        """Extract features from odds data.
        
        Args:
            market_odds: Market odds data
            
        Returns:
            Dictionary of odds features
        """
        features = {}
        
        if not market_odds.bookmaker_odds:
            # No odds available
            features.update({
                "best_odds": 0.0,
                "avg_odds": 0.0,
                "odds_std": 0.0,
                "num_bookmakers": 0.0,
                "implied_probability": 0.5,
                "odds_range": 0.0
            })
            return features
        
        odds_values = [bo.odds for bo in market_odds.bookmaker_odds]
        
        features["best_odds"] = max(odds_values)
        features["avg_odds"] = np.mean(odds_values)
        features["odds_std"] = np.std(odds_values) if len(odds_values) > 1 else 0.0
        features["num_bookmakers"] = len(odds_values)
        features["implied_probability"] = 1.0 / features["best_odds"]
        features["odds_range"] = max(odds_values) - min(odds_values) if odds_values else 0.0
        
        # Market efficiency indicator
        features["market_efficiency"] = (
            features["odds_std"] / features["avg_odds"] 
            if features["avg_odds"] > 0 else 0.0
        )
        
        return features
    
    def _extract_time_features(self, market_odds: MarketOdds) -> Dict[str, float]:
        """Extract time-based features.
        
        Args:
            market_odds: Market odds data
            
        Returns:
            Dictionary of time features
        """
        features = {}
        
        now = datetime.utcnow()
        time_to_game = market_odds.commence_time - now
        
        features["hours_until_game"] = time_to_game.total_seconds() / 3600
        features["is_primetime"] = float(market_odds.commence_time.hour >= 20)  # 8 PM or later
        features["day_of_week"] = market_odds.commence_time.weekday()
        features["is_weekend"] = float(market_odds.commence_time.weekday() >= 5)
        
        # Season timing (simplified)
        month = market_odds.commence_time.month
        if market_odds.sport in [SportType.NFL, SportType.NBA, SportType.NHL]:
            features["is_early_season"] = float(month in [9, 10, 11])
            features["is_late_season"] = float(month in [3, 4])
        else:
            features["is_early_season"] = float(month in [4, 5])
            features["is_late_season"] = float(month in [9, 10])
        
        return features
    
    def _extract_historical_features(
        self,
        market_odds: MarketOdds,
        historical_data: pd.DataFrame
    ) -> Dict[str, float]:
        """Extract features from historical data.
        
        Args:
            market_odds: Current market odds
            historical_data: Historical performance data
            
        Returns:
            Dictionary of historical features
        """
        features = {}
        
        # Filter for relevant teams
        home_data = historical_data[
            historical_data["team"] == market_odds.home_team
        ].tail(10)  # Last 10 games
        
        away_data = historical_data[
            historical_data["team"] == market_odds.away_team
        ].tail(10)
        
        # Home team features
        if not home_data.empty:
            features["home_win_rate"] = home_data["won"].mean()
            features["home_avg_score"] = home_data["score"].mean()
            features["home_avg_against"] = home_data["opponent_score"].mean()
            features["home_recent_form"] = home_data.tail(5)["won"].mean()
        else:
            features.update({
                "home_win_rate": 0.5,
                "home_avg_score": 0.0,
                "home_avg_against": 0.0,
                "home_recent_form": 0.5
            })
        
        # Away team features
        if not away_data.empty:
            features["away_win_rate"] = away_data["won"].mean()
            features["away_avg_score"] = away_data["score"].mean()
            features["away_avg_against"] = away_data["opponent_score"].mean()
            features["away_recent_form"] = away_data.tail(5)["won"].mean()
        else:
            features.update({
                "away_win_rate": 0.5,
                "away_avg_score": 0.0,
                "away_avg_against": 0.0,
                "away_recent_form": 0.5
            })
        
        # Head-to-head
        h2h_data = historical_data[
            ((historical_data["team"] == market_odds.home_team) & 
             (historical_data["opponent"] == market_odds.away_team)) |
            ((historical_data["team"] == market_odds.away_team) & 
             (historical_data["opponent"] == market_odds.home_team))
        ]
        
        if not h2h_data.empty:
            home_h2h_wins = h2h_data[
                (h2h_data["team"] == market_odds.home_team) & 
                (h2h_data["won"] == 1)
            ].shape[0]
            features["h2h_home_win_rate"] = home_h2h_wins / len(h2h_data)
        else:
            features["h2h_home_win_rate"] = 0.5
        
        return features
    
    def _extract_sport_specific_features(
        self,
        market_odds: MarketOdds,
        weather_data: Optional[Dict[str, Any]] = None,
        injury_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, float]:
        """Extract sport-specific features.
        
        Args:
            market_odds: Market odds data
            weather_data: Weather conditions
            injury_data: Injury reports
            
        Returns:
            Dictionary of sport-specific features
        """
        features = {}
        
        # Weather features (for outdoor sports)
        if market_odds.sport in [SportType.NFL, SportType.MLB, SportType.SOCCER_EPL]:
            if weather_data:
                features["temperature"] = weather_data.get("temperature", 70)
                features["wind_speed"] = weather_data.get("wind_speed", 0)
                features["precipitation"] = weather_data.get("precipitation", 0)
                features["is_dome"] = float(weather_data.get("is_dome", False))
            else:
                features.update({
                    "temperature": 70,
                    "wind_speed": 0,
                    "precipitation": 0,
                    "is_dome": 0
                })
        
        # Injury impact
        if injury_data:
            home_injuries = injury_data.get(market_odds.home_team, {})
            away_injuries = injury_data.get(market_odds.away_team, {})
            
            features["home_key_injuries"] = home_injuries.get("key_players_out", 0)
            features["away_key_injuries"] = away_injuries.get("key_players_out", 0)
            features["home_injury_impact"] = home_injuries.get("impact_score", 0)
            features["away_injury_impact"] = away_injuries.get("impact_score", 0)
        else:
            features.update({
                "home_key_injuries": 0,
                "away_key_injuries": 0,
                "home_injury_impact": 0,
                "away_injury_impact": 0
            })
        
        # Travel and rest (simplified)
        features["is_home_b2b"] = 0  # Back-to-back games
        features["is_away_b2b"] = 0
        features["travel_distance"] = 0  # Miles traveled
        
        return features
    
    def fit(self, feature_matrix: np.ndarray) -> None:
        """Fit the scaler on training data.
        
        Args:
            feature_matrix: Training feature matrix
        """
        self.scaler.fit(feature_matrix)
        self._is_fitted = True
    
    def transform(self, feature_matrix: np.ndarray) -> np.ndarray:
        """Transform features using fitted scaler.
        
        Args:
            feature_matrix: Feature matrix to transform
            
        Returns:
            Scaled feature matrix
        """
        if not self._is_fitted:
            logger.warning("Scaler not fitted, returning raw features")
            return feature_matrix
        
        return self.scaler.transform(feature_matrix)
    
    def fit_transform(self, feature_matrix: np.ndarray) -> np.ndarray:
        """Fit scaler and transform features.
        
        Args:
            feature_matrix: Feature matrix to fit and transform
            
        Returns:
            Scaled feature matrix
        """
        self.fit(feature_matrix)
        return self.transform(feature_matrix)
    
    def get_feature_importance(
        self,
        model: Any,
        top_k: int = 20
    ) -> List[Tuple[str, float]]:
        """Get feature importance from trained model.
        
        Args:
            model: Trained model with feature_importances_
            top_k: Number of top features to return
            
        Returns:
            List of (feature_name, importance) tuples
        """
        if not hasattr(model, "feature_importances_"):
            logger.warning("Model does not have feature_importances_")
            return []
        
        importances = model.feature_importances_
        indices = np.argsort(importances)[::-1][:top_k]
        
        return [
            (self.feature_names[i], importances[i])
            for i in indices
        ]