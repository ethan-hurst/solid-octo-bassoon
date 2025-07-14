#!/usr/bin/env python3
"""
Script to evaluate trained ML models for sports betting.

Usage:
    python scripts/evaluate_models.py                     # Evaluate all models
    python scripts/evaluate_models.py --sport NFL         # Evaluate specific sport
    python scripts/evaluate_models.py --backtest          # Include backtesting
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
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score, roc_curve
from sqlalchemy import select

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from src.models.schemas import SportType
from src.models.database import OddsSnapshot, GameResult
from src.analysis.ml_models import SportsBettingModel
from src.analysis.value_calculator import ValueCalculator
from src.api.dependencies import AsyncSessionLocal

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ModelEvaluator:
    """Evaluates trained ML models for sports betting."""
    
    def __init__(self):
        self.models: Dict[SportType, SportsBettingModel] = {}
        self.results_dir = Path("evaluation_results")
        self.results_dir.mkdir(exist_ok=True)
    
    def load_model(self, sport: SportType, model_type: str = "xgboost") -> Optional[SportsBettingModel]:
        """Load a trained model for a sport."""
        model_path = Path(f"models/{sport.value}_{model_type}_model.pkl")
        
        if not model_path.exists():
            logger.warning(f"Model not found: {model_path}")
            return None
        
        try:
            model = SportsBettingModel(sport, model_type=model_type)
            model.load(model_path)
            return model
        except Exception as e:
            logger.error(f"Error loading model {model_path}: {e}")
            return None
    
    async def load_evaluation_data(self, sport: SportType, days_back: int = 90) -> Tuple[np.ndarray, np.ndarray, pd.DataFrame]:
        """Load recent data for evaluation."""
        logger.info(f"Loading evaluation data for {sport.value}")
        
        cutoff_date = datetime.utcnow() - timedelta(days=days_back)
        
        async with AsyncSessionLocal() as db:
            # Load recent odds snapshots
            odds_result = await db.execute(
                select(OddsSnapshot).where(
                    OddsSnapshot.sport == sport.value,
                    OddsSnapshot.timestamp >= cutoff_date
                ).order_by(OddsSnapshot.timestamp)
            )
            odds_data = odds_result.scalars().all()
            
            # Load corresponding results
            results_result = await db.execute(
                select(GameResult).where(
                    GameResult.sport == sport.value,
                    GameResult.game_date >= cutoff_date
                )
            )
            results_data = results_result.scalars().all()
        
        if not odds_data or not results_data:
            logger.warning(f"No evaluation data found for {sport.value}")
            return np.array([]), np.array([]), pd.DataFrame()
        
        # Convert to DataFrame and merge
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
        
        merged_df = odds_df.merge(results_df, on='game_id', how='inner')
        
        if merged_df.empty:
            return np.array([]), np.array([]), pd.DataFrame()
        
        # Generate features (simplified version)
        features = self._generate_simple_features(merged_df)
        labels = (merged_df['winner'] == merged_df['home_team']).astype(int).values
        
        return features, labels, merged_df
    
    def _generate_simple_features(self, df: pd.DataFrame) -> np.ndarray:
        """Generate simple features for evaluation."""
        # This is a simplified feature generation for evaluation
        # In practice, you'd use the same FeatureEngineer as in training
        
        features = []
        for _, row in df.iterrows():
            feature_vector = [
                row['odds'],  # Bookmaker odds
                1.0 / row['odds'],  # Implied probability
                len(row['home_team']),  # Team name length (dummy feature)
                len(row['away_team']),  # Team name length (dummy feature)
                # Add more realistic features here
            ]
            features.append(feature_vector)
        
        # Pad to 50 features (matching training)
        features_array = np.array(features)
        if features_array.shape[1] < 50:
            padding = np.random.rand(features_array.shape[0], 50 - features_array.shape[1])
            features_array = np.hstack([features_array, padding])
        
        return features_array
    
    async def evaluate_model_performance(self, sport: SportType, model: SportsBettingModel) -> Dict:
        """Evaluate model performance on recent data."""
        logger.info(f"Evaluating model performance for {sport.value}")
        
        X, y, df = await self.load_evaluation_data(sport)
        
        if len(X) == 0:
            return {"error": "no_evaluation_data"}
        
        # Get predictions
        probabilities = await model.predict_batch(X)
        predictions = (np.array(probabilities) > 0.5).astype(int)
        
        # Calculate metrics
        metrics = self._calculate_metrics(y, predictions, probabilities)
        
        # Add model-specific info
        metrics.update({
            "sport": sport.value,
            "model_type": model.model_type,
            "evaluation_samples": len(y),
            "date_range": f"{datetime.now() - timedelta(days=90):%Y-%m-%d} to {datetime.now():%Y-%m-%d}"
        })
        
        return metrics
    
    def _calculate_metrics(self, y_true: np.ndarray, y_pred: np.ndarray, y_prob: np.ndarray) -> Dict:
        """Calculate comprehensive evaluation metrics."""
        
        # Basic metrics
        accuracy = np.mean(y_true == y_pred)
        
        # Classification report
        report = classification_report(y_true, y_pred, output_dict=True)
        
        # Confusion matrix
        cm = confusion_matrix(y_true, y_pred)
        
        # ROC AUC
        try:
            auc = roc_auc_score(y_true, y_prob)
        except ValueError:
            auc = 0.5  # If only one class present
        
        # Brier score (calibration)
        brier_score = np.mean((y_prob - y_true) ** 2)
        
        # Log loss
        epsilon = 1e-15
        y_prob_clipped = np.clip(y_prob, epsilon, 1 - epsilon)
        log_loss = -np.mean(y_true * np.log(y_prob_clipped) + (1 - y_true) * np.log(1 - y_prob_clipped))
        
        # Betting-specific metrics
        edge_threshold = 0.05
        value_bets = np.abs(y_prob - 0.5) > edge_threshold
        value_bet_accuracy = np.mean(y_true[value_bets] == y_pred[value_bets]) if np.any(value_bets) else 0
        
        return {
            "accuracy": accuracy,
            "precision": report['1']['precision'] if '1' in report else 0,
            "recall": report['1']['recall'] if '1' in report else 0,
            "f1_score": report['1']['f1-score'] if '1' in report else 0,
            "auc_roc": auc,
            "brier_score": brier_score,
            "log_loss": log_loss,
            "confusion_matrix": cm.tolist(),
            "value_bets_found": int(np.sum(value_bets)),
            "value_bet_accuracy": value_bet_accuracy,
            "total_games": len(y_true)
        }
    
    def plot_model_performance(self, sport: SportType, y_true: np.ndarray, y_prob: np.ndarray):
        """Create performance visualization plots."""
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle(f'Model Performance - {sport.value}', fontsize=16)
        
        # ROC Curve
        fpr, tpr, _ = roc_curve(y_true, y_prob)
        auc = roc_auc_score(y_true, y_prob)
        
        axes[0, 0].plot(fpr, tpr, label=f'ROC Curve (AUC = {auc:.3f})')
        axes[0, 0].plot([0, 1], [0, 1], 'k--', label='Random')
        axes[0, 0].set_xlabel('False Positive Rate')
        axes[0, 0].set_ylabel('True Positive Rate')
        axes[0, 0].set_title('ROC Curve')
        axes[0, 0].legend()
        axes[0, 0].grid(True)
        
        # Prediction Distribution
        axes[0, 1].hist(y_prob[y_true == 0], alpha=0.5, label='Losses', bins=20)
        axes[0, 1].hist(y_prob[y_true == 1], alpha=0.5, label='Wins', bins=20)
        axes[0, 1].set_xlabel('Predicted Probability')
        axes[0, 1].set_ylabel('Frequency')
        axes[0, 1].set_title('Prediction Distribution')
        axes[0, 1].legend()
        
        # Calibration Plot
        n_bins = 10
        bin_boundaries = np.linspace(0, 1, n_bins + 1)
        bin_lowers = bin_boundaries[:-1]
        bin_uppers = bin_boundaries[1:]
        
        bin_centers = []
        bin_accuracies = []
        
        for bin_lower, bin_upper in zip(bin_lowers, bin_uppers):
            in_bin = (y_prob > bin_lower) & (y_prob <= bin_upper)
            prop_in_bin = in_bin.mean()
            
            if prop_in_bin > 0:
                accuracy_in_bin = y_true[in_bin].mean()
                bin_centers.append((bin_lower + bin_upper) / 2)
                bin_accuracies.append(accuracy_in_bin)
        
        axes[1, 0].plot([0, 1], [0, 1], 'k--', label='Perfect Calibration')
        axes[1, 0].scatter(bin_centers, bin_accuracies, label='Model')
        axes[1, 0].set_xlabel('Mean Predicted Probability')
        axes[1, 0].set_ylabel('Fraction of Positives')
        axes[1, 0].set_title('Calibration Plot')
        axes[1, 0].legend()
        axes[1, 0].grid(True)
        
        # Feature Importance (if available)
        try:
            model_path = Path(f"models/{sport.value}_xgboost_model.pkl")
            if model_path.exists():
                model = SportsBettingModel(sport, model_type="xgboost")
                model.load(model_path)
                importance = model.get_feature_importance(top_k=10)
                
                if importance:
                    features, importances = zip(*importance)
                    axes[1, 1].barh(range(len(features)), importances)
                    axes[1, 1].set_yticks(range(len(features)))
                    axes[1, 1].set_yticklabels(features)
                    axes[1, 1].set_xlabel('Importance')
                    axes[1, 1].set_title('Top 10 Feature Importances')
        except Exception as e:
            axes[1, 1].text(0.5, 0.5, f'Feature importance\nnot available\n({str(e)})', 
                           ha='center', va='center', transform=axes[1, 1].transAxes)
            axes[1, 1].set_title('Feature Importance')
        
        plt.tight_layout()
        
        # Save plot
        plot_path = self.results_dir / f"{sport.value}_performance.png"
        plt.savefig(plot_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"Performance plot saved to {plot_path}")
    
    async def backtest_model(self, sport: SportType, model: SportsBettingModel, days_back: int = 30) -> Dict:
        """Backtest model performance for betting strategy."""
        logger.info(f"Backtesting model for {sport.value}")
        
        X, y, df = await self.load_evaluation_data(sport, days_back)
        
        if len(X) == 0:
            return {"error": "no_backtest_data"}
        
        # Get predictions
        probabilities = await model.predict_batch(X)
        
        # Simulate betting strategy
        initial_bankroll = 10000
        current_bankroll = initial_bankroll
        bets_placed = 0
        bets_won = 0
        total_staked = 0
        
        bet_history = []
        
        for i, (prob, actual, odds) in enumerate(zip(probabilities, y, df['odds'].values)):
            # Simple value betting strategy
            implied_prob = 1 / odds
            edge = prob - implied_prob
            
            # Only bet if we have an edge > 5%
            if edge > 0.05:
                # Kelly criterion for bet sizing
                kelly_fraction = edge / (odds - 1)
                kelly_fraction = min(kelly_fraction, 0.25)  # Cap at 25%
                
                bet_size = current_bankroll * kelly_fraction
                bet_size = max(bet_size, 10)  # Minimum bet
                
                # Place bet
                bets_placed += 1
                total_staked += bet_size
                
                if actual == 1:  # Won
                    winnings = bet_size * (odds - 1)
                    current_bankroll += winnings
                    bets_won += 1
                else:  # Lost
                    current_bankroll -= bet_size
                
                bet_history.append({
                    'bet_number': bets_placed,
                    'probability': prob,
                    'odds': odds,
                    'edge': edge,
                    'bet_size': bet_size,
                    'won': actual == 1,
                    'bankroll': current_bankroll
                })
        
        # Calculate metrics
        win_rate = bets_won / bets_placed if bets_placed > 0 else 0
        roi = (current_bankroll - initial_bankroll) / initial_bankroll
        profit = current_bankroll - initial_bankroll
        
        return {
            "initial_bankroll": initial_bankroll,
            "final_bankroll": current_bankroll,
            "profit": profit,
            "roi": roi,
            "bets_placed": bets_placed,
            "bets_won": bets_won,
            "win_rate": win_rate,
            "total_staked": total_staked,
            "average_bet_size": total_staked / bets_placed if bets_placed > 0 else 0,
            "bet_history": bet_history[-20:]  # Last 20 bets
        }
    
    async def evaluate_all_models(self, include_backtest: bool = False) -> Dict:
        """Evaluate all trained models."""
        logger.info("Evaluating all trained models")
        
        results = {}
        
        for sport in SportType:
            logger.info(f"Evaluating {sport.value}")
            
            # Try different model types
            for model_type in ["xgboost", "ensemble"]:
                model = self.load_model(sport, model_type)
                
                if model is None:
                    continue
                
                key = f"{sport.value}_{model_type}"
                
                try:
                    # Performance evaluation
                    performance = await self.evaluate_model_performance(sport, model)
                    results[key] = performance
                    
                    # Create plots if we have data
                    if "error" not in performance:
                        X, y, df = await self.load_evaluation_data(sport)
                        if len(X) > 0:
                            probabilities = await model.predict_batch(X)
                            self.plot_model_performance(sport, y, np.array(probabilities))
                    
                    # Backtest if requested
                    if include_backtest and "error" not in performance:
                        backtest_results = await self.backtest_model(sport, model)
                        results[key]["backtest"] = backtest_results
                
                except Exception as e:
                    logger.error(f"Error evaluating {key}: {e}")
                    results[key] = {"error": str(e)}
        
        return results
    
    def print_evaluation_summary(self, results: Dict):
        """Print evaluation summary."""
        print("\n" + "="*80)
        print("MODEL EVALUATION SUMMARY")
        print("="*80)
        
        for model_key, result in results.items():
            print(f"\n{model_key.upper()}:")
            
            if "error" in result:
                print(f"  ❌ Error: {result['error']}")
                continue
            
            # Performance metrics
            print(f"  📊 Evaluation Samples: {result.get('evaluation_samples', 0)}")
            print(f"  🎯 Accuracy: {result.get('accuracy', 0):.3f}")
            print(f"  📈 Precision: {result.get('precision', 0):.3f}")
            print(f"  📉 Recall: {result.get('recall', 0):.3f}")
            print(f"  🔄 F1 Score: {result.get('f1_score', 0):.3f}")
            print(f"  📊 AUC-ROC: {result.get('auc_roc', 0):.3f}")
            print(f"  🎲 Brier Score: {result.get('brier_score', 0):.3f}")
            print(f"  💰 Value Bets Found: {result.get('value_bets_found', 0)}")
            print(f"  ✅ Value Bet Accuracy: {result.get('value_bet_accuracy', 0):.3f}")
            
            # Backtest results
            if "backtest" in result:
                backtest = result["backtest"]
                if "error" not in backtest:
                    print(f"  💵 Backtest ROI: {backtest.get('roi', 0):.1%}")
                    print(f"  🎰 Bets Placed: {backtest.get('bets_placed', 0)}")
                    print(f"  🏆 Win Rate: {backtest.get('win_rate', 0):.1%}")
                    print(f"  💲 Profit: ${backtest.get('profit', 0):.2f}")
        
        print("\n" + "="*80)


async def main():
    """Main evaluation function."""
    parser = argparse.ArgumentParser(description='Evaluate ML models for sports betting')
    parser.add_argument('--sport', type=str, choices=[s.value for s in SportType],
                       help='Specific sport to evaluate (default: all)')
    parser.add_argument('--backtest', action='store_true',
                       help='Include backtesting analysis')
    parser.add_argument('--plots', action='store_true', default=True,
                       help='Generate performance plots')
    
    args = parser.parse_args()
    
    evaluator = ModelEvaluator()
    
    try:
        if args.sport:
            # Evaluate specific sport
            sport = SportType(args.sport)
            
            results = {}
            for model_type in ["xgboost", "ensemble"]:
                model = evaluator.load_model(sport, model_type)
                if model:
                    key = f"{sport.value}_{model_type}"
                    results[key] = await evaluator.evaluate_model_performance(sport, model)
                    
                    if args.backtest and "error" not in results[key]:
                        results[key]["backtest"] = await evaluator.backtest_model(sport, model)
        else:
            # Evaluate all models
            results = await evaluator.evaluate_all_models(include_backtest=args.backtest)
        
        # Print summary
        evaluator.print_evaluation_summary(results)
        
        # Save results
        import json
        results_path = evaluator.results_dir / f"evaluation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_path, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n📄 Evaluation results saved to {results_path}")
        
    except KeyboardInterrupt:
        logger.info("Evaluation interrupted by user")
    except Exception as e:
        logger.error(f"Evaluation failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())