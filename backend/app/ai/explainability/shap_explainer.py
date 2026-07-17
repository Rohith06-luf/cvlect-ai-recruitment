from typing import Any, Dict
import numpy as np
from app.ai.ranking.xgboost_ranker import XGBoostRanker

try:
    import shap
except ImportError:
    shap = None


class SHAPExplainer:
    _explainer = None

    @classmethod
    def get_explainer(cls) -> Any:
        if shap is None:
            return None
        if cls._explainer is None:
            booster = XGBoostRanker.get_booster()
            if booster is not None:
                try:
                    # TreeExplainer is ideal for XGBoost models
                    cls._explainer = shap.TreeExplainer(booster)
                except Exception as e:
                    print(f"Error instantiating SHAP TreeExplainer: {e}")
        return cls._explainer

    def explain(self, candidate: Dict[str, Any], job_description: str) -> Dict[str, Any]:
        features = candidate.get("features", {})
        
        # Prepare inputs
        exp_years = float(features.get("experience_years", 0))
        exp_norm = min(1.0, exp_years / 10.0)
        
        feature_names = [
            "semantic_similarity", "experience_years", "education_score", 
            "skill_overlap", "projects_score", "certifications_score"
        ]
        
        feature_values = [
            float(features.get("semantic_similarity", 0.0)),
            exp_norm,
            float(features.get("education_score", 0.0)),
            float(features.get("skill_overlap", 0.0)),
            float(features.get("projects_score", 0.0)),
            float(features.get("certifications_score", 0.0))
        ]

        explainer = self.get_explainer()
        
        # Default fallback weights if SHAP is not installed or fails
        if explainer is None or shap is None:
            shap_dict = {
                "semantic_similarity": round(feature_values[0] * 0.40, 3),
                "experience_years": round(feature_values[1] * 0.20, 3),
                "education_score": round(feature_values[2] * 0.10, 3),
                "skill_overlap": round(feature_values[3] * 0.15, 3),
                "projects_score": round(feature_values[4] * 0.08, 3),
                "certifications_score": round(feature_values[5] * 0.07, 3),
            }
        else:
            try:
                # Calculate SHAP values for the single candidate vector
                X = np.array([feature_values], dtype=np.float32)
                # TreeExplainer returns a list of shap values for each output or raw array
                raw_shap = explainer.shap_values(X)
                
                # Handle single class output mapping
                if isinstance(raw_shap, list):
                    raw_shap = raw_shap[0]
                
                # Get the 1D array of feature contributions
                contributions = raw_shap[0]
                
                shap_dict = {}
                for name, val in zip(feature_names, contributions):
                    shap_dict[name] = round(float(val), 3)
            except Exception as e:
                print(f"SHAP calculation error: {e}. Falling back to default scoring.")
                shap_dict = {
                    "semantic_similarity": round(feature_values[0] * 0.40, 3),
                    "experience_years": round(feature_values[1] * 0.20, 3),
                    "education_score": round(feature_values[2] * 0.10, 3),
                    "skill_overlap": round(feature_values[3] * 0.15, 3),
                    "projects_score": round(feature_values[4] * 0.08, 3),
                    "certifications_score": round(feature_values[5] * 0.07, 3),
                }

        # Format explanation lists
        positive_features = []
        if shap_dict.get("semantic_similarity", 0.0) > 0.05:
            positive_features.append("Strong semantic matching with the job requirements")
        if shap_dict.get("experience_years", 0.0) > 0.05:
            positive_features.append(f"Highly relevant work duration ({int(exp_years)} years)")
        if shap_dict.get("skill_overlap", 0.0) > 0.05:
            positive_features.append("Excellent technical skill overlap")
        if shap_dict.get("projects_score", 0.0) > 0.02:
            positive_features.append("Strong project background")
        if shap_dict.get("education_score", 0.0) > 0.02:
            positive_features.append("Solid educational foundation")
        if shap_dict.get("certifications_score", 0.0) > 0.02:
            positive_features.append("Relevant professional certifications")

        if not positive_features:
            positive_features.append("Balanced overall candidate profile")

        # Missing skills identification
        parsed = candidate.get("parsed_resume", {})
        skills = {s.lower() for s in parsed.get("skills", [])}
        
        job_tokens = re_extract_skills(job_description.lower())
        missing_skills = sorted(list(job_tokens - skills))
        
        # Sort factors by absolute influence size
        important_factors = sorted(
            shap_dict.keys(),
            key=lambda k: abs(shap_dict[k]),
            reverse=True
        )

        return {
            "positive_features": positive_features,
            "missing_skills": missing_skills[:5] if missing_skills else ["No major gaps detected"],
            "important_factors": [factor.replace("_", " ").title() for factor in important_factors],
            "shap_values": shap_dict,
        }


def re_extract_skills(text: str) -> set:
    import re
    # Simple token parser to extract potential skill matches
    tokens = re.findall(r"\b[a-zA-Z0-9+#.-]+\b", text)
    stopwords = {"the", "and", "for", "with", "are", "we", "you", "will", "have", "experience", "required", "role"}
    return {t for t in tokens if len(t) > 2 and t not in stopwords}
