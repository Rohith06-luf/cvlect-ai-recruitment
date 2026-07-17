import os
from typing import Any, List, Dict
import numpy as np

try:
    import xgboost as xgb
except ImportError:
    xgb = None


class XGBoostRanker:
    _model = None

    def __init__(self) -> None:
        self.model_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
            "uploads", "xgboost_ranker.json"
        )
        self.ensure_model_trained()

    def ensure_model_trained(self) -> None:
        if xgb is None:
            return
            
        if self._model is not None:
            return

        # Try to load existing model
        if os.path.exists(self.model_path):
            try:
                self._model = xgb.Booster()
                self._model.load_model(self.model_path)
                return
            except Exception as e:
                print(f"Error loading XGBoost model: {e}. Retraining...")

        # Train a default Booster model with synthetic training data
        # Feature columns: [semantic_similarity, experience_years_norm, education_score, skill_overlap, projects_score, certifications_score]
        X = np.array([
            [0.90, 0.50, 1.0, 0.90, 0.80, 0.80], # Top tier candidate (5 yrs, PhD, high overlap)
            [0.80, 0.30, 0.8, 0.80, 0.60, 0.60], # Strong match (3 yrs, Masters)
            [0.60, 0.20, 0.5, 0.50, 0.40, 0.20], # Mid tier candidate (2 yrs, Bachelors)
            [0.40, 0.10, 0.5, 0.30, 0.20, 0.00], # Junior match (1 yr)
            [0.20, 0.05, 0.2, 0.10, 0.00, 0.00], # Minimal match
            [0.85, 0.10, 0.5, 0.80, 0.80, 0.40], # Junior but very high skills overlap
            [0.50, 0.80, 0.8, 0.40, 0.40, 0.60], # High experience but low semantic match
            [0.30, 0.40, 0.5, 0.20, 0.20, 0.20], # Experienced but wrong skills
        ], dtype=np.float32)
        
        # Match percentage score targets (0 to 1)
        y = np.array([0.95, 0.88, 0.62, 0.42, 0.18, 0.80, 0.58, 0.35], dtype=np.float32)

        # Build booster
        dtrain = xgb.DMatrix(X, label=y, feature_names=[
            "semantic_similarity", "experience_years", "education_score", 
            "skill_overlap", "projects_score", "certifications_score"
        ])
        
        params = {
            "objective": "reg:squarederror",
            "max_depth": 3,
            "eta": 0.3,
            "eval_metric": "rmse"
        }
        
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        self._model = xgb.train(params, dtrain, num_boost_round=15)
        self._model.save_model(self.model_path)

    @classmethod
    def get_booster(cls) -> Any:
        if cls._model is None:
            # Instantiate to trigger ensure_model_trained
            XGBoostRanker()
        return cls._model

    def rank(self, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if not candidates:
            return []

        booster = self.get_booster()
        if booster is None:
            # Fallback ranking if xgboost package is missing
            ranked = []
            for candidate in candidates:
                features = candidate.get("features", {})
                score = (
                    float(features.get("semantic_similarity", 0.0)) * 0.40
                    + float(features.get("experience_years", 0) / 10.0) * 0.20
                    + float(features.get("education_score", 0.0)) * 0.10
                    + float(features.get("skill_overlap", 0.0)) * 0.15
                    + float(features.get("projects_score", 0.0)) * 0.08
                    + float(features.get("certifications_score", 0.0)) * 0.07
                )
                ranked.append({**candidate, "rank_score": round(score, 4)})
            ranked.sort(key=lambda item: item["rank_score"], reverse=True)
            return ranked

        # Extract features matrix
        rows = []
        for c in candidates:
            f = c.get("features", {})
            # Normalize experience years (e.g., 5 years -> 0.5)
            exp_norm = min(1.0, float(f.get("experience_years", 0)) / 10.0)
            rows.append([
                float(f.get("semantic_similarity", 0.0)),
                exp_norm,
                float(f.get("education_score", 0.0)),
                float(f.get("skill_overlap", 0.0)),
                float(f.get("projects_score", 0.0)),
                float(f.get("certifications_score", 0.0))
            ])

        dmatrix = xgb.DMatrix(np.array(rows, dtype=np.float32), feature_names=[
            "semantic_similarity", "experience_years", "education_score", 
            "skill_overlap", "projects_score", "certifications_score"
        ])
        
        preds = booster.predict(dmatrix)
        
        ranked = []
        for idx, candidate in enumerate(candidates):
            # Clip predictions between 0.0 and 1.0
            score = float(np.clip(preds[idx], 0.0, 1.0))
            ranked.append({**candidate, "rank_score": round(score, 4)})

        ranked.sort(key=lambda item: item["rank_score"], reverse=True)
        return ranked
