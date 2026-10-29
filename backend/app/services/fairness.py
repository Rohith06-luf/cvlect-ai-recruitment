"""
CVlect AI — Fairness & Algorithmic Audit Service
Provides resume anonymization (blind review) and diagnostic disparity analysis.
Strictly adheres to ethical AI principles: never infers protected attributes from names or text.
"""

import copy
import re
from datetime import datetime, timezone
from typing import Any, Optional
import numpy as np

from app.schemas.schemas import FairnessReport
from app.utils import get_logger

logger = get_logger(__name__)


def blind_review(resume_dict: dict[str, Any]) -> dict[str, Any]:
    """
    Produce an anonymized version of extracted resume data for unbiased review.
    Redacts personal identifiers: name, email, phone, location, social profile URLs.
    Preserves skills, experience descriptions, education fields, and technical projects.
    """
    blinded = copy.deepcopy(resume_dict)

    # Redact contact details
    if "contact_info" in blinded and isinstance(blinded["contact_info"], dict):
        blinded["contact_info"] = {
            "name": "[REDACTED - BLIND REVIEW]",
            "email": "[REDACTED]",
            "phone": "[REDACTED]",
            "location": "[REDACTED]",
            "linkedin": None,
            "github": None,
        }

    # Scrub identifiable contact fragments from raw text if present
    if "raw_text" in blinded and isinstance(blinded["raw_text"], str):
        text = blinded["raw_text"]
        text = re.sub(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', '[REDACTED_EMAIL]', text)
        text = re.sub(r'(?:\+?\d{1,3}[\s.-]?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}', '[REDACTED_PHONE]', text)
        text = re.sub(r'(?:https?:\/\/)?(?:www\.)?linkedin\.com\/[^\s]+', '[REDACTED_LINK]', text)
        text = re.sub(r'(?:https?:\/\/)?(?:www\.)?github\.com\/[^\s]+', '[REDACTED_LINK]', text)
        blinded["raw_text"] = text

    blinded["is_blinded"] = True
    return blinded


def generate_fairness_report(
    match_results: list[Any],
    metadata: Optional[dict[str, Any]] = None,
) -> FairnessReport:
    """
    Compute descriptive diagnostic fairness metrics across a set of MatchResult objects.
    Attempts Fairlearn metric calculations if demographic metadata is provided and fairlearn is installed.
    Otherwise produces rigorous score distribution and selection-rate statistics.
    """
    metadata = metadata or {}
    sample_size = len(match_results)

    if sample_size == 0:
        return FairnessReport(
            report_type="Score Distribution & Disparity Diagnostic",
            metrics={"status": "No candidate match records available for analysis"},
            limitations=[
                "Sample size is zero; audit cannot proceed.",
                "Diagnostic reports are strictly informational and do not certify regulatory compliance.",
            ],
            sample_size=0,
            generated_at=datetime.now(timezone.utc),
            is_diagnostic=True,
        )

    # Extract score values
    scores = []
    for m in match_results:
        val = getattr(m, "overall_score", None)
        if val is None and isinstance(m, dict):
            val = m.get("overall_score", 0.0)
        scores.append(float(val or 0.0))

    scores_arr = np.array(scores, dtype=np.float32)

    # Standard distribution metrics
    mean_score = float(np.mean(scores_arr))
    median_score = float(np.median(scores_arr))
    std_score = float(np.std(scores_arr))
    min_score = float(np.min(scores_arr))
    max_score = float(np.max(scores_arr))

    # Pass rates at standard thresholds
    pass_50 = float(np.mean(scores_arr >= 50.0))
    pass_65 = float(np.mean(scores_arr >= 65.0))
    pass_80 = float(np.mean(scores_arr >= 80.0))

    metrics: dict[str, Any] = {
        "score_distribution": {
            "mean": round(mean_score, 2),
            "median": round(median_score, 2),
            "std_dev": round(std_score, 2),
            "min": round(min_score, 2),
            "max": round(max_score, 2),
        },
        "pass_rates": {
            "threshold_50_pct": round(pass_50 * 100, 1),
            "threshold_65_pct": round(pass_65 * 100, 1),
            "threshold_80_pct": round(pass_80 * 100, 1),
        },
    }

    # Group disparity evaluation if explicit groups provided in metadata
    group_labels = metadata.get("group_labels")
    if group_labels and len(group_labels) == sample_size:
        unique_groups = list(set(group_labels))
        group_stats = {}
        threshold = metadata.get("selection_threshold", 65.0)

        for g in unique_groups:
            g_indices = [i for i, label in enumerate(group_labels) if label == g]
            g_scores = scores_arr[g_indices]
            g_pass_rate = float(np.mean(g_scores >= threshold)) if len(g_scores) > 0 else 0.0
            group_stats[str(g)] = {
                "count": len(g_scores),
                "mean_score": round(float(np.mean(g_scores)), 2) if len(g_scores) > 0 else 0.0,
                "selection_rate": round(g_pass_rate, 4),
            }

        rates = [v["selection_rate"] for v in group_stats.values() if v["count"] > 0]
        if rates and max(rates) > 0:
            disparate_impact_ratio = min(rates) / max(rates)
            demographic_parity_diff = max(rates) - min(rates)
        else:
            disparate_impact_ratio = 1.0
            demographic_parity_diff = 0.0

        metrics["subgroup_analysis"] = {
            "threshold_used": threshold,
            "groups": group_stats,
            "disparate_impact_ratio": round(disparate_impact_ratio, 4),
            "demographic_parity_difference": round(demographic_parity_diff, 4),
            "four_fifths_rule_met": bool(disparate_impact_ratio >= 0.80),
        }

        # Try Fairlearn if installed
        try:
            from fairlearn.metrics import selection_rate, demographic_parity_difference, demographic_parity_ratio
            y_pred = (scores_arr >= threshold).astype(int)
            fl_dpr = demographic_parity_ratio(y_pred, y_pred, sensitive_features=group_labels)
            fl_dpd = demographic_parity_difference(y_pred, y_pred, sensitive_features=group_labels)
            metrics["fairlearn_metrics"] = {
                "demographic_parity_ratio": round(float(fl_dpr), 4),
                "demographic_parity_difference": round(float(fl_dpd), 4),
            }
        except ImportError:
            pass
        except Exception as e:
            logger.debug(f"Fairlearn calculation skipped: {e}")

    limitations = [
        "Ethical constraint: Protected attributes (e.g. race, gender) are NEVER inferred from candidate names or bios.",
        "Diagnostic only: Statistical parity metrics reflect aggregate distributions and are not proof of algorithmic fairness.",
        f"Sample size caveat: Analysis evaluated {sample_size} candidates. Small samples (< 30) exhibit wide confidence intervals.",
        "Human review required: These metrics are intended to assist human audit teams, not replace human judgment.",
    ]

    return FairnessReport(
        report_type="Score Distribution & Disparity Diagnostic",
        metrics=metrics,
        limitations=limitations,
        sample_size=sample_size,
        generated_at=datetime.now(timezone.utc),
        is_diagnostic=True,
    )
