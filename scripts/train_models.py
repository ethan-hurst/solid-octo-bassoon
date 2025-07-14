#!/usr/bin/env python3
"""
Script to train ML models for sports betting prediction.

Usage:
    python scripts/train_models.py                    # Train all sports
    python scripts/train_models.py --sport NFL        # Train specific sport
    python scripts/train_models.py --sport NBA --test # Include test/validation
"""

import argparse
import asyncio
import logging
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import numpy as np
import pandas as pd
from sqlalchemy import select

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from src.models.schemas import SportType
from src.models.database import OddsSnapshot, GameResult
from src.analysis.ml_models import SportsBettingModel, ModelEnsemble
from src.analysis.feature_engineering import FeatureEngineer
from src.api.dependencies import AsyncSessionLocal
from src.config.settings import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ModelTrainer:
    """ML model trainer for sports betting."""
    
    def __init__(self):
        self.feature_engineer = FeatureEngineer()
        self.models: Dict[SportType, SportsBettingModel] = {}
        
    async def load_training_data(self, sport: SportType, days_back: int = 365) -> Tuple[np.ndarray, np.ndarray]:
        """
        Load training data for a specific sport.
        
        Args:
            sport: Sport to load data for
            days_back: Number of days of historical data to use
            
        Returns:
            Tuple of (features, labels)
        """
        logger.info(f"Loading training data for {sport.value}")
        
        cutoff_date = datetime.utcnow() - timedelta(days=days_back)
        
        async with AsyncSessionLocal() as db:
            # Load odds snapshots
            odds_result = await db.execute(
                select(OddsSnapshot).where(
                    OddsSnapshot.sport == sport.value,
                    OddsSnapshot.timestamp >= cutoff_date
                ).order_by(OddsSnapshot.timestamp)
            )
            odds_data = odds_result.scalars().all()
            
            # Load game results (for labels)
            results_result = await db.execute(
                select(GameResult).where(
                    GameResult.sport == sport.value,
                    GameResult.game_date >= cutoff_date
                ).order_by(GameResult.game_date)
            )
            results_data = results_result.scalars().all()
            
        if not odds_data or not results_data:
            logger.warning(f"Insufficient data for {sport.value}. Creating dummy data.")
            return self._create_dummy_data()
            
        logger.info(f"Loaded {len(odds_data)} odds records and {len(results_data)} game results")
        
        # Convert to DataFrames for easier processing
        odds_df = pd.DataFrame([
            {
                'game_id': snapshot.game_id,
                'timestamp': snapshot.timestamp,
                'home_team': snapshot.home_team,
                'away_team': snapshot.away_team,
                'bookmaker': snapshot.bookmaker,
                'odds': snapshot.decimal_odds,
                'commence_time': snapshot.commence_time
            }
            for snapshot in odds_data
        ])
        
        results_df = pd.DataFrame([
            {
                'game_id': result.game_id,
                'home_score': result.home_score,
                'away_score': result.away_score,
                'winner': result.winner,
                'game_date': result.game_date
            }
            for result in results_data
        ])
        
        # Merge odds with results
        merged_df = odds_df.merge(results_df, on='game_id', how='inner')
        
        if merged_df.empty:
            logger.warning(f"No matching odds and results for {sport.value}")
            return self._create_dummy_data()
            
        # Generate features
        features = await self.feature_engineer.generate_features(merged_df, sport)
        
        # Generate labels (1 if home team won, 0 otherwise)
        labels = (merged_df['winner'] == merged_df['home_team']).astype(int).values
        
        logger.info(f"Generated {features.shape[0]} samples with {features.shape[1]} features")
        
        return features, labels
    
    def _create_dummy_data(self, n_samples: int = 1000, n_features: int = 50) -> Tuple[np.ndarray, np.ndarray]:
        """Create dummy training data when real data is unavailable."""
        logger.info(f"Creating dummy training data: {n_samples} samples, {n_features} features")
        
        np.random.seed(42)  # For reproducibility
        
        # Generate synthetic features
        X = np.random.rand(n_samples, n_features)
        
        # Create labels with some pattern (makes first few features important)
        # This creates a realistic but synthetic relationship
        y = (
            (X[:, 0] > 0.5) &  # Team strength
            (X[:, 1] > 0.4) |  # Recent form
            (X[:, 2] > 0.6)    # Home advantage
        ).astype(int)
        
        # Add some noise
        noise_indices = np.random.choice(n_samples, size=int(0.1 * n_samples), replace=False)
        y[noise_indices] = 1 - y[noise_indices]
        
        return X, y
    
    async def train_sport_model(
        self, 
        sport: SportType, 
        model_type: str = "xgboost",
        test_size: float = 0.2,
        cv_folds: int = 5
    ) -> Dict:
        """
        Train a model for a specific sport.
        
        Args:
            sport: Sport to train model for
            model_type: Type of model to train
            test_size: Fraction of data to use for testing
            cv_folds: Number of cross-validation folds
            
        Returns:
            Dictionary with training metrics
        """
        logger.info(f"Training {model_type} model for {sport.value}")
        
        # Load training data
        X, y = await self.load_training_data(sport)
        
        if X.shape[0] < 100:
            logger.warning(f"Insufficient samples ({X.shape[0]}) for {sport.value}")
            return {"error": "insufficient_data"}
        
        # Create and train model
        model = SportsBettingModel(sport, model_type=model_type)
        metrics = model.train(X, y, test_size=test_size, cv_folds=cv_folds)
        
        # Save trained model
        model_path = Path(f"models/{sport.value}_{model_type}_model.pkl")
        model_path.parent.mkdir(exist_ok=True)
        model.save(model_path)
        
        self.models[sport] = model
        
        logger.info(f"Model training completed for {sport.value}")
        logger.info(f"Metrics: {metrics}")
        
        return {
            "sport": sport.value,
            "model_type": model_type,
            "metrics": metrics,
            "model_path": str(model_path),
            "training_samples": X.shape[0],
            "features": X.shape[1]
        }
    
    async def train_ensemble_model(self, sport: SportType) -> Dict:
        """Train an ensemble model combining multiple algorithms."""
        logger.info(f"Training ensemble model for {sport.value}")
        
        X, y = await self.load_training_data(sport)
        
        if X.shape[0] < 100:
            return {"error": "insufficient_data"}
        
        # Train ensemble model
        ensemble_model = SportsBettingModel(sport, model_type="ensemble")
        metrics = ensemble_model.train(X, y)
        
        # Save model
        model_path = Path(f"models/{sport.value}_ensemble_model.pkl")
        model_path.parent.mkdir(exist_ok=True)
        ensemble_model.save(model_path)
        
        self.models[sport] = ensemble_model
        
        return {
            "sport": sport.value,
            "model_type": "ensemble",
            "metrics": metrics,
            "model_path": str(model_path),
            "training_samples": X.shape[0]
        }
    
    async def validate_model(self, sport: SportType, model: SportsBettingModel) -> Dict:
        """Validate model performance on recent data."""
        logger.info(f"Validating model for {sport.value}")
        
        # Load recent data (last 30 days)
        validation_data = await self.load_training_data(sport, days_back=30)
        
        if validation_data[0].shape[0] < 10:
            return {"error": "insufficient_validation_data"}
        
        X_val, y_val = validation_data
        
        # Get predictions
        probabilities = await model.predict_batch(X_val)
        predictions = (np.array(probabilities) > 0.5).astype(int)
        
        # Calculate metrics
        accuracy = np.mean(predictions == y_val)
        
        # Calculate Brier score (lower is better)
        brier_score = np.mean((np.array(probabilities) - y_val) ** 2)
        
        # Calculate log loss
        epsilon = 1e-15  # To avoid log(0)
        probabilities = np.clip(probabilities, epsilon, 1 - epsilon)
        log_loss = -np.mean(y_val * np.log(probabilities) + (1 - y_val) * np.log(1 - probabilities))
        
        return {
            "validation_samples": len(y_val),
            "accuracy": accuracy,
            "brier_score": brier_score,
            "log_loss": log_loss
        }
    
    async def train_all_sports(self, model_type: str = "xgboost") -> Dict:
        """Train models for all supported sports."""
        logger.info(f"Training {model_type} models for all sports")
        
        results = {}
        
        for sport in SportType:
            try:
                result = await self.train_sport_model(sport, model_type)
                results[sport.value] = result
                
                # Validate if training was successful
                if "error" not in result and sport in self.models:
                    validation_metrics = await self.validate_model(sport, self.models[sport])
                    result["validation"] = validation_metrics
                    
            except Exception as e:
                logger.error(f"Error training model for {sport.value}: {e}")
                results[sport.value] = {"error": str(e)}
        
        return results
    
    def print_summary(self, results: Dict):
        """Print training summary."""
        print("\n" + "="*80)
        print("MODEL TRAINING SUMMARY")
        print("="*80)
        
        for sport, result in results.items():
            print(f"\n{sport}:")
            if "error" in result:
                print(f"  ❌ Error: {result['error']}")
            else:
                metrics = result.get("metrics", {})
                validation = result.get("validation", {})
                
                print(f"  ✅ Model Type: {result.get('model_type', 'unknown')}")
                print(f"  📊 Training Samples: {result.get('training_samples', 0)}")
                print(f"  🎯 Accuracy: {metrics.get('accuracy', 0):.3f}")
                print(f"  📈 F1 Score: {metrics.get('f1_score', 0):.3f}")
                
                if validation:
                    print(f"  🔍 Validation Accuracy: {validation.get('accuracy', 0):.3f}")
                    print(f"  📉 Brier Score: {validation.get('brier_score', 0):.3f}")
                    print(f"  📊 Log Loss: {validation.get('log_loss', 0):.3f}")
        
        print("\n" + "="*80)


async def main():
    """Main training function."""
    parser = argparse.ArgumentParser(description='Train ML models for sports betting')
    parser.add_argument('--sport', type=str, choices=[s.value for s in SportType],
                       help='Specific sport to train (default: all)')
    parser.add_argument('--model-type', type=str, default='xgboost',
                       choices=['xgboost', 'random_forest', 'logistic_regression', 'ensemble'],
                       help='Type of model to train')
    parser.add_argument('--test', action='store_true',
                       help='Include validation testing')
    parser.add_argument('--no-save', action='store_true',
                       help='Do not save trained models')
    
    args = parser.parse_args()
    
    trainer = ModelTrainer()
    
    try:
        if args.sport:
            # Train specific sport
            sport = SportType(args.sport)
            logger.info(f"Training model for {sport.value}")
            
            if args.model_type == 'ensemble':
                result = await trainer.train_ensemble_model(sport)
            else:
                result = await trainer.train_sport_model(sport, args.model_type)
            
            results = {sport.value: result}
            
        else:
            # Train all sports
            if args.model_type == 'ensemble':
                results = {}
                for sport in SportType:
                    results[sport.value] = await trainer.train_ensemble_model(sport)
            else:
                results = await trainer.train_all_sports(args.model_type)
        
        # Print summary
        trainer.print_summary(results)
        
        # Save summary to file
        import json
        summary_path = Path(f"training_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        with open(summary_path, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n📄 Training summary saved to {summary_path}")
        
    except KeyboardInterrupt:
        logger.info("Training interrupted by user")
    except Exception as e:
        logger.error(f"Training failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())