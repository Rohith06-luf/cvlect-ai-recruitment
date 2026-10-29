"""
CVlect AI — Candidate Ranking Neural Network
Deep learning architecture for multi-feature candidate-job relevance scoring.
"""

import os
from typing import Optional, Union, Any
import numpy as np

from app.utils import get_logger

logger = get_logger(__name__)

# Default model weight persistence path
MODEL_WEIGHTS_PATH = os.path.join(os.path.dirname(__file__), "ranking_model.pt")

try:
    import torch
    import torch.nn as nn

    class CandidateRankingNetwork(nn.Module):
        """
        Deep neural network with 3 hidden layers, Batch Normalization,
        Dropout regularization, and Sigmoid output for candidate-job relevance scoring.
        """
        def __init__(self, feature_dim: int = 6, dropout_rate: float = 0.2):
            super().__init__()
            self.network = nn.Sequential(
                # Hidden Layer 1
                nn.Linear(feature_dim, 64),
                nn.BatchNorm1d(64),
                nn.ReLU(),
                nn.Dropout(dropout_rate),

                # Hidden Layer 2
                nn.Linear(64, 32),
                nn.BatchNorm1d(32),
                nn.ReLU(),
                nn.Dropout(dropout_rate),

                # Hidden Layer 3
                nn.Linear(32, 16),
                nn.ReLU(),

                # Output Layer
                nn.Linear(16, 1),
                nn.Sigmoid(),
            )

        def forward(self, x: torch.Tensor) -> torch.Tensor:
            """Forward pass mapping feature tensor to [0, 1] relevance score."""
            return self.network(x)

except ImportError:
    torch = None
    nn = None
    CandidateRankingNetwork = None
    logger.warning("PyTorch is not available. RankingModel will operate in baseline/demo mode.")


class RankingModelManager:
    """
    Manages loading, saving, and inference for the CandidateRankingNetwork.
    Provides graceful fallbacks when the model is not yet trained.
    """
    def __init__(self, weights_path: str = MODEL_WEIGHTS_PATH, feature_dim: int = 6):
        self.weights_path = weights_path
        self.feature_dim = feature_dim
        self.model: Optional[Any] = None
        self._is_trained = False
        self._load_if_exists()

    @property
    def is_trained(self) -> bool:
        """Returns True if a valid trained neural model is loaded in memory."""
        return self._is_trained and self.model is not None

    def _load_if_exists(self) -> bool:
        """Attempts to load pre-trained weights from disk."""
        if torch is None or CandidateRankingNetwork is None:
            return False

        if os.path.exists(self.weights_path):
            try:
                model = CandidateRankingNetwork(feature_dim=self.feature_dim)
                state_dict = torch.load(self.weights_path, map_location=torch.device("cpu"))
                model.load_state_dict(state_dict)
                model.eval()
                self.model = model
                self._is_trained = True
                logger.info(f"Loaded ranking network from {self.weights_path}")
                return True
            except Exception as e:
                logger.warning(f"Failed to load ranking weights ({e}). Model marked as untrained.")
                self.model = None
                self._is_trained = False
                return False
        return False

    def save_model(self, model: Any) -> bool:
        """Save network state dictionary to disk."""
        if torch is None:
            return False
        try:
            os.makedirs(os.path.dirname(self.weights_path), exist_ok=True)
            torch.save(model.state_dict(), self.weights_path)
            self.model = model
            self.model.eval()
            self._is_trained = True
            logger.info(f"CandidateRankingNetwork successfully saved to {self.weights_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving ranking model: {e}")
            return False

    def predict(self, feature_vector: Union[list[float], np.ndarray]) -> Optional[float]:
        """
        Predict relevance score for a given feature vector.
        Returns float in range [0, 1] if model is trained; otherwise None.
        """
        if not self.is_trained or torch is None:
            return None

        try:
            arr = np.asarray(feature_vector, dtype=np.float32).reshape(1, -1)
            if arr.shape[1] != self.feature_dim:
                logger.warning(
                    f"Feature dimension mismatch: expected {self.feature_dim}, got {arr.shape[1]}"
                )
                return None

            tensor = torch.from_numpy(arr)
            self.model.eval()
            with torch.no_grad():
                output = self.model(tensor)
                score = float(output.item())
                return float(np.clip(score, 0.0, 1.0))
        except Exception as e:
            logger.error(f"Ranking network inference error: {e}")
            return None


# Global singleton instance
ranking_model_manager = RankingModelManager()
