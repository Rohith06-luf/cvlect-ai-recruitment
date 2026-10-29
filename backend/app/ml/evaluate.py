"""
CVlect AI — Ranking Network Evaluation Pipeline
Evaluates candidate ranking metrics: Precision@K, Recall@K, NDCG@K, and MRR.

Usage:
    python -m app.ml.evaluate
"""

import sys
import numpy as np

from app.ml.ranking_network import ranking_model_manager, CandidateRankingNetwork
from app.ml.train import generate_synthetic_dataset
from app.utils import get_logger

logger = get_logger("app.ml.evaluate")


def compute_dcg(relevances: np.ndarray, k: int) -> float:
    """Compute Discounted Cumulative Gain at K."""
    rel = np.asarray(relevances)[:k]
    if len(rel) == 0:
        return 0.0
    discounts = np.log2(np.arange(len(rel)) + 2)
    return float(np.sum((2 ** rel - 1) / discounts))


def compute_ndcg(true_relevances: np.ndarray, predicted_scores: np.ndarray, k: int = 5) -> float:
    """Compute Normalized Discounted Cumulative Gain at K."""
    order = np.argsort(-predicted_scores)
    ranked_true = true_relevances[order]

    actual_dcg = compute_dcg(ranked_true, k)
    ideal_dcg = compute_dcg(np.sort(true_relevances)[::-1], k)

    if ideal_dcg == 0:
        return 1.0 if actual_dcg == 0 else 0.0
    return float(actual_dcg / ideal_dcg)


def compute_precision_recall_at_k(
    true_relevances: np.ndarray,
    predicted_scores: np.ndarray,
    k: int = 5,
    threshold: float = 0.65,
) -> tuple[float, float]:
    """Calculate Precision@K and Recall@K based on a relevance threshold."""
    order = np.argsort(-predicted_scores)
    top_k_indices = order[:k]

    is_relevant = (true_relevances >= threshold)
    total_relevant = int(np.sum(is_relevant))

    if total_relevant == 0:
        return 1.0, 1.0

    retrieved_relevant = int(np.sum(is_relevant[top_k_indices]))
    precision = retrieved_relevant / float(k)
    recall = retrieved_relevant / float(total_relevant)

    return precision, recall


def compute_mrr(
    true_relevances: np.ndarray,
    predicted_scores: np.ndarray,
    threshold: float = 0.65,
) -> float:
    """Compute Reciprocal Rank for the first relevant item."""
    order = np.argsort(-predicted_scores)
    for rank, idx in enumerate(order, start=1):
        if true_relevances[idx] >= threshold:
            return 1.0 / float(rank)
    return 0.0


def evaluate_ranking_model(
    num_queries: int = 100,
    candidates_per_query: int = 20,
    k_list: tuple[int, ...] = (3, 5, 10),
) -> dict[str, float]:
    """
    Simulate job query candidate lists, predict scores, and evaluate performance.
    """
    print("=" * 70)
    print(" CVLECT AI — RANKING MODEL EVALUATION REPORT")
    print("=" * 70)

    total_samples = num_queries * candidates_per_query
    X, y = generate_synthetic_dataset(num_samples=total_samples, random_seed=999)

    # Obtain predictions
    if ranking_model_manager.is_trained:
        print("[INFO] Evaluating trained PyTorch CandidateRankingNetwork...")
        preds = []
        for feat in X:
            p = ranking_model_manager.predict(feat)
            preds.append(p if p is not None else 0.5)
        predictions = np.array(preds)
    else:
        print("[INFO] No trained PyTorch weights found. Evaluating baseline weighted scoring...")
        weights = np.array([0.30, 0.10, 0.20, 0.15, 0.10, 0.15], dtype=np.float32)
        predictions = np.dot(X, weights)

    # Compute metrics grouped by query
    ndcg_scores = {k: [] for k in k_list}
    precision_scores = {k: [] for k in k_list}
    recall_scores = {k: [] for k in k_list}
    mrr_scores = []

    for q in range(num_queries):
        start = q * candidates_per_query
        end = start + candidates_per_query
        q_true = y[start:end].flatten()
        q_pred = predictions[start:end].flatten()

        for k in k_list:
            ndcg = compute_ndcg(q_true, q_pred, k=k)
            prec, rec = compute_precision_recall_at_k(q_true, q_pred, k=k)
            ndcg_scores[k].append(ndcg)
            precision_scores[k].append(prec)
            recall_scores[k].append(rec)

        mrr_scores.append(compute_mrr(q_true, q_pred))

    results = {}
    for k in k_list:
        results[f"NDCG@{k}"] = float(np.mean(ndcg_scores[k]))
        results[f"Precision@{k}"] = float(np.mean(precision_scores[k]))
        results[f"Recall@{k}"] = float(np.mean(recall_scores[k]))
    results["MRR"] = float(np.mean(mrr_scores))

    # Print clean markdown summary table
    print(f"\nEvaluated on {num_queries} queries with {candidates_per_query} candidates each ({total_samples} total pairs):\n")
    print(f"| Metric         | Score    | Benchmark Range |")
    print(f"|----------------|----------|-----------------|")
    for metric_name, val in results.items():
        bench = "0.75 - 0.95" if "NDCG" in metric_name else "0.60 - 0.90"
        print(f"| {metric_name:<14} | {val:.4f}   | {bench:<15} |")
    print("\n" + "=" * 70)

    return results


if __name__ == "__main__":
    evaluate_ranking_model()
