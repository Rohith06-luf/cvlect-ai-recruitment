"""
CVlect AI — Neural Ranking Network Training Pipeline
Generates synthetic candidate-job feature pairs and trains CandidateRankingNetwork using PyTorch.

Mode: DEMONSTRATION / SYNTHETIC TRAINING
Usage:
    python -m app.ml.train
"""

import os
import sys
import numpy as np

from app.ml.ranking_network import CandidateRankingNetwork, ranking_model_manager, MODEL_WEIGHTS_PATH
from app.utils import get_logger

logger = get_logger("app.ml.train")


def generate_synthetic_dataset(num_samples: int = 5000, random_seed: int = 42) -> tuple[np.ndarray, np.ndarray]:
    """
    Generate realistic synthetic feature vectors and target relevance scores.
    Features:
      0: skill_coverage [0, 1]
      1: preferred_skill_coverage [0, 1]
      2: semantic_similarity [0, 1]
      3: experience_alignment [0, 1]
      4: education_alignment [0, 1]
      5: project_relevance [0, 1]
    """
    np.random.seed(random_seed)

    # Sample realistic correlated distributions
    skill_cov = np.random.beta(a=2.5, b=2.0, size=(num_samples, 1))
    pref_skill_cov = np.random.beta(a=2.0, b=3.0, size=(num_samples, 1))
    semantic_sim = np.clip(0.3 * skill_cov + 0.7 * np.random.beta(a=3.0, b=2.0, size=(num_samples, 1)), 0.0, 1.0)
    exp_align = np.random.beta(a=2.0, b=2.0, size=(num_samples, 1))
    edu_align = np.random.choice([0.6, 0.8, 1.0], size=(num_samples, 1), p=[0.2, 0.3, 0.5])
    proj_rel = np.clip(0.4 * skill_cov + 0.6 * np.random.beta(a=2.0, b=2.5, size=(num_samples, 1)), 0.0, 1.0)

    X = np.hstack([skill_cov, pref_skill_cov, semantic_sim, exp_align, edu_align, proj_rel]).astype(np.float32)

    # Compute ground truth relevance with non-linear interaction and gaussian noise
    interaction = skill_cov * exp_align
    noise = np.random.normal(loc=0.0, scale=0.03, size=(num_samples, 1))

    raw_y = (
        0.30 * skill_cov +
        0.10 * pref_skill_cov +
        0.20 * semantic_sim +
        0.15 * exp_align +
        0.10 * edu_align +
        0.10 * proj_rel +
        0.05 * interaction +
        noise
    )

    y = np.clip(raw_y, 0.0, 1.0).astype(np.float32)
    return X, y


def train_model(
    num_samples: int = 5000,
    epochs: int = 25,
    batch_size: int = 64,
    learning_rate: float = 0.001,
) -> bool:
    """Train the candidate ranking neural network and save weights."""
    print("=" * 70)
    print(" CVLECT AI — NEURAL RANKING NETWORK TRAINING")
    print(" [MODE: DEMONSTRATION / SYNTHETIC DATA TRAINING]")
    print("=" * 70)

    try:
        import torch
        import torch.nn as nn
        from torch.utils.data import TensorDataset, DataLoader
    except ImportError:
        logger.error("PyTorch is required for training. Install torch to proceed.")
        return False

    logger.info(f"Generating {num_samples} synthetic feature pairs...")
    X, y = generate_synthetic_dataset(num_samples=num_samples)

    # Train/Validation Split (80/20)
    split_idx = int(num_samples * 0.8)
    X_train, y_train = torch.from_numpy(X[:split_idx]), torch.from_numpy(y[:split_idx])
    X_val, y_val = torch.from_numpy(X[split_idx:]), torch.from_numpy(y[split_idx:])

    train_dataset = TensorDataset(X_train, y_train)
    val_dataset = TensorDataset(X_val, y_val)

    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)

    feature_dim = X.shape[1]
    model = CandidateRankingNetwork(feature_dim=feature_dim)
    criterion = nn.BCELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate, weight_decay=1e-4)

    logger.info(f"Starting training on {len(X_train)} samples for {epochs} epochs...")

    for epoch in range(1, epochs + 1):
        model.train()
        train_loss = 0.0
        for batch_X, batch_y in train_loader:
            optimizer.zero_grad()
            preds = model(batch_X)
            loss = criterion(preds, batch_y)
            loss.backward()
            optimizer.step()
            train_loss += loss.item() * len(batch_X)

        train_loss /= len(X_train)

        # Validation phase
        model.eval()
        val_loss = 0.0
        with torch.no_grad():
            for batch_X, batch_y in val_loader:
                preds = model(batch_X)
                loss = criterion(preds, batch_y)
                val_loss += loss.item() * len(batch_X)
        val_loss /= len(X_val)

        if epoch % 5 == 0 or epoch == 1:
            logger.info(f"Epoch {epoch:02d}/{epochs:02d} — Train Loss: {train_loss:.5f} | Val Loss: {val_loss:.5f}")

    # Save trained model to disk
    success = ranking_model_manager.save_model(model)
    if success:
        logger.info(f"Model saved successfully to: {MODEL_WEIGHTS_PATH}")
        print("\nTraining completed successfully. Weights persisted.")
    else:
        logger.error("Failed to save trained weights.")

    return success


if __name__ == "__main__":
    train_model()
