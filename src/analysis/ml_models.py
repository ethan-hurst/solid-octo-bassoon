"""Machine learning models for sports outcome prediction."""
import logging
import pickle
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import pandas as pd
from sklearn.ensemble import VotingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, log_loss
import xgboost as xgb

from src.models.schemas import SportType, MarketOdds
from src.models.ml_features import FeatureEngineer

logger = logging.getLogger(__name__)


class MLPredictor:
    """Base predictor interface for ML models."""
    
    async def predict_probability(self, features: np.ndarray) -> float:
        """Predict probability of home team winning.
        
        Args:
            features: Feature vector
            
        Returns:
            Probability between 0 and 1
        """
        raise NotImplementedError


class SportsBettingModel:
    """Main ML model for sports betting predictions."""
    
    def __init__(
        self,
        sport: SportType,
        model_type: str = "ensemble",
        model_path: Optional[Path] = None
    ):
        """Initialize sports betting model.
        
        Args:
            sport: Sport type for the model
            model_type: Type of model (xgboost, ensemble, etc.)
            model_path: Path to saved model
        """
        self.sport = sport
        self.model_type = model_type
        self.model_path = model_path or Path(f"models/{sport.value}_{model_type}.pkl")
        self.feature_engineer = FeatureEngineer()
        
        # Initialize model
        self.model = self._create_model()
        self._is_trained = False
        
        # Performance metrics
        self.metrics: Dict[str, float] = {}
        
        # Load if exists
        if self.model_path.exists():
            self.load()
    
    def _create_model(self) -> Any:
        """Create the ML model based on type.
        
        Returns:
            Initialized model
        """
        if self.model_type == "xgboost":
            return xgb.XGBClassifier(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                objective="binary:logistic",
                use_label_encoder=False,
                eval_metric="logloss",
                random_state=42
            )
        elif self.model_type == "ensemble":
            # Ensemble of multiple models
            xgb_model = xgb.XGBClassifier(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                objective="binary:logistic",
                use_label_encoder=False,
                eval_metric="logloss",
                random_state=42
            )
            
            rf_model = RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                random_state=42
            )
            
            lr_model = LogisticRegression(
                max_iter=1000,
                random_state=42
            )
            
            return VotingClassifier(
                estimators=[
                    ("xgb", xgb_model),
                    ("rf", rf_model),
                    ("lr", lr_model)
                ],
                voting="soft"  # Use probability averaging
            )
        else:
            raise ValueError(f"Unknown model type: {self.model_type}")
    
    async def predict_probability(self, features: np.ndarray) -> float:
        """Predict probability of home team winning.
        
        Args:
            features: Feature vector
            
        Returns:
            Probability between 0 and 1
        """
        if not self._is_trained:
            logger.warning("Model not trained, returning 0.5")
            return 0.5
        
        # Ensure 2D array
        if features.ndim == 1:
            features = features.reshape(1, -1)
        
        # Scale features
        features_scaled = self.feature_engineer.transform(features)
        
        # Get probability
        probabilities = self.model.predict_proba(features_scaled)
        
        # Return probability of positive class (home team win)
        return float(probabilities[0, 1])
    
    async def predict_batch(
        self,
        feature_matrix: np.ndarray
    ) -> np.ndarray:
        """Predict probabilities for multiple games.
        
        Args:
            feature_matrix: Feature matrix (n_samples, n_features)
            
        Returns:
            Array of probabilities
        """
        if not self._is_trained:
            logger.warning("Model not trained, returning 0.5 for all")
            return np.full(feature_matrix.shape[0], 0.5)
        
        # Scale features
        features_scaled = self.feature_engineer.transform(feature_matrix)
        
        # Get probabilities
        probabilities = self.model.predict_proba(features_scaled)
        
        # Return probabilities of positive class
        return probabilities[:, 1]
    
    def train(
        self,
        X: np.ndarray,
        y: np.ndarray,
        test_size: float = 0.2,
        cv_folds: int = 5
    ) -> Dict[str, float]:
        """Train the model on historical data.
        
        Args:
            X: Feature matrix
            y: Target labels (1 for home win, 0 for away win)
            test_size: Proportion of data for testing
            cv_folds: Number of cross-validation folds
            
        Returns:
            Dictionary of performance metrics
        """
        logger.info(f"Training {self.model_type} model for {self.sport.value}")
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42, stratify=y
        )
        
        # Fit feature scaler
        X_train_scaled = self.feature_engineer.fit_transform(X_train)
        X_test_scaled = self.feature_engineer.transform(X_test)
        
        # Cross-validation
        cv_scores = cross_val_score(
            self.model, X_train_scaled, y_train,
            cv=cv_folds, scoring="neg_log_loss"
        )
        
        logger.info(f"CV Log Loss: {-cv_scores.mean():.4f} (+/- {cv_scores.std() * 2:.4f})")
        
        # Train final model
        self.model.fit(X_train_scaled, y_train)
        self._is_trained = True
        
        # Evaluate
        y_pred = self.model.predict(X_test_scaled)
        y_pred_proba = self.model.predict_proba(X_test_scaled)[:, 1]
        
        self.metrics = {
            "accuracy": accuracy_score(y_test, y_pred),
            "precision": precision_score(y_test, y_pred),
            "recall": recall_score(y_test, y_pred),
            "f1_score": f1_score(y_test, y_pred),
            "log_loss": log_loss(y_test, y_pred_proba),
            "cv_log_loss": -cv_scores.mean(),
            "train_samples": len(X_train),
            "test_samples": len(X_test)
        }
        
        logger.info(f"Test Accuracy: {self.metrics['accuracy']:.4f}")
        logger.info(f"Test F1 Score: {self.metrics['f1_score']:.4f}")
        
        return self.metrics
    
    def get_confidence_score(
        self,
        probability: float,
        features: Optional[np.ndarray] = None
    ) -> float:
        """Calculate confidence score for a prediction.
        
        Args:
            probability: Predicted probability
            features: Optional feature vector for additional analysis
            
        Returns:
            Confidence score between 0 and 1
        """
        # Base confidence from probability distance from 0.5
        base_confidence = abs(probability - 0.5) * 2
        
        # Adjust based on model performance
        if self.metrics:
            accuracy_factor = self.metrics.get("accuracy", 0.5)
            f1_factor = self.metrics.get("f1_score", 0.5)
            
            # Weight by model performance
            confidence = base_confidence * (accuracy_factor + f1_factor) / 2
        else:
            confidence = base_confidence * 0.7  # Reduce confidence if not evaluated
        
        # Additional adjustments could be made based on:
        # - Feature reliability
        # - Market agreement
        # - Historical accuracy for similar games
        
        return min(confidence, 1.0)
    
    def save(self, path: Optional[Path] = None) -> None:
        """Save model to disk.
        
        Args:
            path: Save path, defaults to model_path
        """
        save_path = path or self.model_path
        save_path.parent.mkdir(parents=True, exist_ok=True)
        
        model_data = {
            "model": self.model,
            "feature_engineer": self.feature_engineer,
            "metrics": self.metrics,
            "sport": self.sport,
            "model_type": self.model_type,
            "is_trained": self._is_trained
        }
        
        with open(save_path, "wb") as f:
            pickle.dump(model_data, f)
        
        logger.info(f"Model saved to {save_path}")
    
    def load(self, path: Optional[Path] = None) -> None:
        """Load model from disk.
        
        Args:
            path: Load path, defaults to model_path
        """
        load_path = path or self.model_path
        
        if not load_path.exists():
            logger.warning(f"No model found at {load_path}")
            return
        
        with open(load_path, "rb") as f:
            model_data = pickle.load(f)
        
        self.model = model_data["model"]
        self.feature_engineer = model_data["feature_engineer"]
        self.metrics = model_data["metrics"]
        self._is_trained = model_data["is_trained"]
        
        logger.info(f"Model loaded from {load_path}")
    
    def get_feature_importance(self, top_k: int = 20) -> List[Tuple[str, float]]:
        """Get top feature importances.
        
        Args:
            top_k: Number of features to return
            
        Returns:
            List of (feature_name, importance) tuples
        """
        if not self._is_trained:
            return []
        
        # Get base model for ensemble
        if self.model_type == "ensemble":
            # Use XGBoost component for feature importance
            xgb_model = self.model.named_estimators_["xgb"]
            return self.feature_engineer.get_feature_importance(xgb_model, top_k)
        else:
            return self.feature_engineer.get_feature_importance(self.model, top_k)


class ModelEnsemble(MLPredictor):
    """Ensemble of multiple sport-specific models."""
    
    def __init__(self, models: Dict[SportType, SportsBettingModel]):
        """Initialize model ensemble.
        
        Args:
            models: Dictionary of sport-specific models
        """
        self.models = models
    
    async def predict_probability(self, features: np.ndarray) -> float:
        """Predict using appropriate sport model.
        
        Args:
            features: Feature vector
            
        Returns:
            Probability from sport-specific model
        """
        # Determine sport from features (assuming one-hot encoding)
        # This is simplified - in practice you'd pass sport type explicitly
        sport_idx = np.argmax(features[:len(SportType)])
        sport = list(SportType)[sport_idx]
        
        if sport in self.models:
            return await self.models[sport].predict_probability(features)
        else:
            logger.warning(f"No model for sport {sport}")
            return 0.5
    
    def train_all(
        self,
        data_by_sport: Dict[SportType, Tuple[np.ndarray, np.ndarray]]
    ) -> Dict[SportType, Dict[str, float]]:
        """Train all sport-specific models.
        
        Args:
            data_by_sport: Dictionary mapping sport to (X, y) data
            
        Returns:
            Dictionary of metrics by sport
        """
        metrics_by_sport = {}
        
        for sport, (X, y) in data_by_sport.items():
            if sport not in self.models:
                self.models[sport] = SportsBettingModel(sport)
            
            metrics = self.models[sport].train(X, y)
            metrics_by_sport[sport] = metrics
        
        return metrics_by_sport