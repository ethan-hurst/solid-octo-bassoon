"""Tests for ML models."""
import pytest
import numpy as np
from unittest.mock import MagicMock, patch
from pathlib import Path
import tempfile

from src.analysis.ml_models import SportsBettingModel, ModelEnsemble
from src.models.schemas import SportType


@pytest.mark.asyncio
async def test_sports_betting_model_creation():
    """Test creating a sports betting model."""
    model = SportsBettingModel(SportType.NFL, model_type="xgboost")
    
    assert model.sport == SportType.NFL
    assert model.model_type == "xgboost"
    assert model.model is not None
    assert not model._is_trained


@pytest.mark.asyncio
async def test_predict_untrained_model():
    """Test prediction with untrained model returns default."""
    model = SportsBettingModel(SportType.NBA)
    
    features = np.random.rand(50)
    probability = await model.predict_probability(features)
    
    assert probability == 0.5  # Default for untrained


@pytest.mark.asyncio
async def test_train_model():
    """Test training a model."""
    model = SportsBettingModel(SportType.NFL, model_type="xgboost")
    
    # Create synthetic training data
    np.random.seed(42)
    n_samples = 1000
    n_features = 50
    
    X = np.random.rand(n_samples, n_features)
    # Create labels with some pattern
    y = (X[:, 0] + X[:, 1] > 1.0).astype(int)
    
    # Train model
    metrics = model.train(X, y, test_size=0.2, cv_folds=3)
    
    assert model._is_trained
    assert "accuracy" in metrics
    assert "f1_score" in metrics
    assert metrics["accuracy"] > 0.5  # Should be better than random


@pytest.mark.asyncio
async def test_predict_trained_model():
    """Test prediction with trained model."""
    model = SportsBettingModel(SportType.MLB)
    
    # Train on simple data
    X = np.array([[0, 0], [1, 1], [0, 1], [1, 0]])
    y = np.array([0, 1, 1, 0])
    
    model.train(X, y, test_size=0.25, cv_folds=2)
    
    # Test prediction
    test_features = np.array([0.8, 0.8])
    probability = await model.predict_probability(test_features)
    
    assert 0 <= probability <= 1
    assert probability != 0.5  # Should not be default


@pytest.mark.asyncio
async def test_batch_prediction():
    """Test batch predictions."""
    model = SportsBettingModel(SportType.NHL)
    
    # Train model
    X = np.random.rand(100, 10)
    y = np.random.randint(0, 2, 100)
    model.train(X, y)
    
    # Batch predict
    test_X = np.random.rand(20, 10)
    probabilities = await model.predict_batch(test_X)
    
    assert len(probabilities) == 20
    assert all(0 <= p <= 1 for p in probabilities)


def test_confidence_score_calculation():
    """Test confidence score calculation."""
    model = SportsBettingModel(SportType.NFL)
    
    # Set some metrics
    model.metrics = {
        "accuracy": 0.60,
        "f1_score": 0.58
    }
    
    # Test confidence for various probabilities
    test_cases = [
        (0.9, 0.5),   # High probability, high confidence
        (0.55, 0.05), # Near 50/50, low confidence
        (0.1, 0.5),   # Low probability, high confidence
    ]
    
    for prob, expected_min_confidence in test_cases:
        confidence = model.get_confidence_score(prob)
        assert confidence >= expected_min_confidence


def test_model_save_load():
    """Test saving and loading a model."""
    with tempfile.TemporaryDirectory() as tmpdir:
        save_path = Path(tmpdir) / "test_model.pkl"
        
        # Create and train model
        model = SportsBettingModel(SportType.NFL)
        X = np.random.rand(100, 10)
        y = np.random.randint(0, 2, 100)
        model.train(X, y)
        
        # Save model
        model.save(save_path)
        assert save_path.exists()
        
        # Load into new model
        new_model = SportsBettingModel(SportType.NFL)
        new_model.load(save_path)
        
        assert new_model._is_trained
        assert new_model.metrics == model.metrics


def test_feature_importance():
    """Test getting feature importance."""
    model = SportsBettingModel(SportType.NBA, model_type="xgboost")
    
    # Create data with clear feature importance
    n_samples = 500
    X = np.random.rand(n_samples, 5)
    # Make first feature most important
    y = (X[:, 0] > 0.5).astype(int)
    
    model.train(X, y)
    
    # Get feature importance
    importances = model.get_feature_importance(top_k=3)
    
    assert len(importances) <= 3
    assert all(isinstance(imp[0], str) for imp in importances)
    assert all(isinstance(imp[1], float) for imp in importances)


@pytest.mark.asyncio
async def test_ensemble_model():
    """Test ensemble model with multiple sports."""
    # Create models for different sports
    models = {
        SportType.NFL: SportsBettingModel(SportType.NFL),
        SportType.NBA: SportsBettingModel(SportType.NBA)
    }
    
    # Train models
    for sport, model in models.items():
        X = np.random.rand(100, 50)
        y = np.random.randint(0, 2, 100)
        model.train(X, y)
    
    # Create ensemble
    ensemble = ModelEnsemble(models)
    
    # Test prediction (assumes sport is encoded in first features)
    features = np.zeros(50)
    features[0] = 1  # NFL indicator
    
    probability = await ensemble.predict_probability(features)
    assert 0 <= probability <= 1


def test_ensemble_model_creation():
    """Test creating ensemble model."""
    model = SportsBettingModel(SportType.SOCCER_EPL, model_type="ensemble")
    
    assert model.model_type == "ensemble"
    assert hasattr(model.model, "estimators")
    assert len(model.model.estimators) == 3  # XGB, RF, LR


def test_invalid_model_type():
    """Test creating model with invalid type."""
    with pytest.raises(ValueError, match="Unknown model type"):
        SportsBettingModel(SportType.NFL, model_type="invalid")


def test_train_all_ensemble():
    """Test training all models in ensemble."""
    # Create empty ensemble
    ensemble = ModelEnsemble({})
    
    # Create training data for multiple sports
    data_by_sport = {
        SportType.NFL: (np.random.rand(100, 50), np.random.randint(0, 2, 100)),
        SportType.NBA: (np.random.rand(100, 50), np.random.randint(0, 2, 100))
    }
    
    # Train all
    metrics = ensemble.train_all(data_by_sport)
    
    assert SportType.NFL in metrics
    assert SportType.NBA in metrics
    assert all("accuracy" in m for m in metrics.values())