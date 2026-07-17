import re
import hashlib
from typing import Any, Dict, List
import numpy as np

try:
    from sklearn.ensemble import IsolationForest
except ImportError:
    IsolationForest = None


class FraudDetector:
    _iso_forest = None

    def __init__(self) -> None:
        self.ensure_isolation_forest_trained()

    def ensure_isolation_forest_trained(self) -> None:
        if IsolationForest is None:
            return
            
        if self._iso_forest is not None:
            return
            
        # Fit Isolation Forest on a synthetic dataset of 20 "normal" resume features
        # Columns: [word_count, unique_word_ratio, experience_years, cap_letter_ratio]
        normal_resumes = np.array([
            [400, 0.60, 3, 0.08],
            [500, 0.55, 5, 0.07],
            [350, 0.65, 1, 0.09],
            [600, 0.50, 8, 0.06],
            [450, 0.58, 4, 0.08],
            [300, 0.70, 2, 0.10],
            [700, 0.48, 12, 0.05],
            [550, 0.52, 6, 0.07],
            [420, 0.62, 3, 0.08],
            [480, 0.57, 5, 0.07],
            [380, 0.64, 2, 0.09],
            [620, 0.49, 10, 0.06],
            [460, 0.59, 4, 0.08],
            [320, 0.68, 1, 0.10],
            [680, 0.47, 11, 0.05],
            [530, 0.53, 7, 0.07],
            [410, 0.61, 3, 0.08],
            [490, 0.56, 5, 0.07],
            [390, 0.63, 2, 0.09],
            [610, 0.50, 9, 0.06]
        ], dtype=np.float32)

        # Instantiate forest with low contamination (e.g. 5%)
        self._iso_forest = IsolationForest(contamination=0.05, random_state=42)
        self._iso_forest.fit(normal_resumes)

    def detect(self, candidate: Dict[str, Any]) -> Dict[str, Any]:
        raw_text = candidate.get("raw_text", "")
        parsed = candidate.get("parsed_resume", {})
        experience = parsed.get("experience_years", 0)
        skills = parsed.get("skills", [])
        education = parsed.get("education", [])
        certifications = parsed.get("certifications", [])

        warnings = []
        rule_score_penalty = 0.0

        if not raw_text.strip():
            return {
                "risk_score": 1.0,
                "warnings": ["Empty resume content"],
                "is_high_risk": True
            }

        # 1. Rule: Age/Experience Mismatch & Skill Exaggeration
        if experience > 40:
            warnings.append("Extremely high experience claims (>40 years)")
            rule_score_penalty += 0.40
            
        # Skill Exaggeration
        exaggerated_terms = {
            "fastapi": (2018, "FastAPI was released in 2018"),
            "xgboost": (2014, "XGBoost was released in 2014"),
            "transformers": (2017, "Transformers library was released in 2017"),
            "gpt-4": (2023, "GPT-4 was released in 2023"),
            "flan-t5": (2022, "FLAN-T5 was released in 2022")
        }
        
        raw_text_lower = raw_text.lower()
        for term, (release_year, release_msg) in exaggerated_terms.items():
            if term in raw_text_lower:
                # Search for claims of experience in this specific tool
                pattern = rf"(\d+)\s*(?:\+?\s*years?|yrs?)(?:\s+of\s+experience)?\s+(?:in|with|using)?\s+{re.escape(term)}"
                matches = re.findall(pattern, raw_text_lower)
                if matches:
                    claimed_exp = int(matches[0])
                    current_year = 2026
                    max_possible = current_year - release_year
                    if claimed_exp > max_possible:
                        warnings.append(f"Exaggerated {term.title()} experience: claims {claimed_exp} years, but {release_msg}")
                        rule_score_penalty += 0.30

        # 2. Rule: Impossible Education Timeline
        # Check B.Tech completion vs start of experience
        grad_years = re.findall(r"\b(19\d{2}|20\d{2})\b", raw_text)
        if grad_years:
            unique_years = sorted(list(set([int(y) for y in grad_years])))
            # If graduation year is after experience start year by a large gap
            if len(unique_years) >= 2:
                earliest_work = unique_years[0]
                latest_grad = unique_years[-1]
                # If they graduated college recently but claim decades of experience
                if latest_grad > 2020 and experience > (2026 - latest_grad + 4) and experience > 15:
                    warnings.append("Impossible education timeline: Graduation date conflicts with decades of claimed experience")
                    rule_score_penalty += 0.35

        # 3. Rule: Overlapping experience
        # Detect simultaneous full-time dates (e.g. 2020-2023 company A and 2020-2023 company B)
        date_blocks = re.findall(r"\b(20\d{2})\s*[-–—]\s*(20\d{2}|present)\b", raw_text_lower)
        if len(date_blocks) >= 3:
            # Check for exact matches indicating cloned blocks
            overlaps = 0
            seen_blocks = set()
            for b in date_blocks:
                if b in seen_blocks:
                    overlaps += 1
                seen_blocks.add(b)
            if overlaps >= 2:
                warnings.append("Overlapping job timelines: Multiple concurrent positions detected with identical dates")
                rule_score_penalty += 0.25

        # 4. Isolation Forest Outlier Analysis
        words = raw_text.split()
        word_count = len(words)
        unique_words = len(set(w.lower() for w in words))
        unique_ratio = unique_words / word_count if word_count > 0 else 0.0
        
        cap_letters = sum(1 for c in raw_text if c.isupper())
        cap_ratio = cap_letters / len(raw_text) if len(raw_text) > 0 else 0.0

        is_forest_anomaly = False
        if self._iso_forest is not None:
            try:
                feat = np.array([[word_count, unique_ratio, float(experience), cap_ratio]], dtype=np.float32)
                pred = self._iso_forest.predict(feat)
                if pred[0] == -1:
                    is_forest_anomaly = True
                    warnings.append("Resume layout is statistically anomalous (possible keyword stuffing or AI template)")
                    rule_score_penalty += 0.20
            except Exception as e:
                print(f"Isolation Forest prediction failed: {e}")

        # Compute combined risk score
        risk_score = round(min(1.0, len(warnings) * 0.25 + rule_score_penalty), 3)

        return {
            "risk_score": risk_score,
            "warnings": warnings if warnings else ["No obvious fraud indicators"],
            "is_high_risk": risk_score >= 0.5,
        }
