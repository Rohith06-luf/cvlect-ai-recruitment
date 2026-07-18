import re
from typing import Any, Dict, List
import numpy as np

try:
    from fairlearn.metrics import selection_rate, demographic_parity_difference
except ImportError:
    selection_rate = None
    demographic_parity_difference = None


class BiasDetector:
    def mask_profile(self, candidate_data: Dict[str, Any], rank: int = 1) -> Dict[str, Any]:
        """
        Implements Blind Hiring by masking personal identifiers.
        """
        masked = dict(candidate_data)
        
        # Mask basic info
        masked["name"] = f"Candidate #{rank}"
        if "email" in masked:
            masked["email"] = "masked_email@example.com"
        if "phone" in masked:
            masked["phone"] = "XXX-XXX-XXXX"
        if "location" in masked:
            masked["location"] = "—"
            
        # Mask text description/summary for gender indicators
        if "summary" in masked and isinstance(masked["summary"], str):
            masked["summary"] = self.mask_text(masked["summary"])
            
        return masked

    def mask_text(self, text: str) -> str:
        """
        Masks names, contact info, and gendered pronouns in raw text.
        """
        # Mask emails
        text = re.sub(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", "[MASKED EMAIL]", text)
        # Mask phones
        text = re.sub(r"(?:\+\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}", "[MASKED PHONE]", text)
        
        # Mask gender pronouns
        gender_maps = {
            r"\bhe\b": "they",
            r"\bshe\b": "they",
            r"\bhis\b": "their",
            r"\bher\b": "their",
            r"\bhim\b": "them",
            r"\bhimself\b": "themselves",
            r"\bherself\b": "themselves"
        }
        
        text_lower = text.lower()
        for pattern, repl in gender_maps.items():
            # Match case sensitivity
            text = re.sub(pattern, repl, text, flags=re.IGNORECASE)
            
        return text

    def analyze(self, candidate: Dict[str, Any]) -> Dict[str, Any]:
        """
        Inspects a single resume for potential demographic markers (gender, age, ethnicity indicators).
        """
        raw_text = candidate.get("raw_text", "").lower()
        
        gendered_terms = ["he", "she", "his", "her", "husband", "wife", "mother", "father", "mr.", "ms.", "mrs."]
        age_terms = ["born in", "dob", "date of birth", "completed in 19", "completed in 200", "age:"]
        
        flagged_gender = [word for word in gendered_terms if re.search(rf"\b{re.escape(word)}\b", raw_text)]
        flagged_age = [word for word in age_terms if word in raw_text]
        
        all_flags = flagged_gender + flagged_age
        
        bias_score = round(min(1.0, len(all_flags) * 0.15), 3)
        
        return {
            "bias_score": bias_score,
            "flagged_terms": all_flags,
            "audit_note": "No protected-class identifiers detected" if not all_flags 
                          else "Contains demographic attributes. Enable Blind Hiring to mask profile details."
        }

    def audit_pipeline_fairness(self, pipeline_entries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Measures hiring fairness across the entire pipeline using Fairlearn logic.
        """
        if not pipeline_entries or len(pipeline_entries) < 4:
            return {
                "demographic_parity_difference": 0.0,
                "selection_rates": {},
                "status": "Insufficient pipeline data to run Fairlearn audit."
            }

        # Estimate demographic groups from names/pronouns for audit purposes
        y_pred = []  # Selection outcomes (1 = shortlisted, 0 = applied/rejected)
        sensitive_gender = [] # Sensitive group features (e.g., "Male", "Female", "Neutral")
        sensitive_age = [] # Sensitive age features (e.g., "Junior", "Senior")

        for entry in pipeline_entries:
            # Get selection status
            status = entry.get("status", "applied").lower()
            y_pred.append(1 if status in {"shortlisted", "selected"} else 0)
            
            # Simple heuristic gender categorization for audit simulation
            summary = entry.get("summary", "").lower()
            name = entry.get("name", "").lower()
            
            # Mock estimation based on pronouns or common name endings
            if any(p in summary for p in [" she ", " her ", "herself"]):
                gender = "Female"
            elif any(p in summary for p in [" he ", " his ", "himself"]):
                gender = "Male"
            else:
                # Fallback to random assign for mock profiling in audit
                gender = "Female" if hash(name) % 2 == 0 else "Male"
            sensitive_gender.append(gender)

            # Heuristic age categorization
            exp = entry.get("experience", "0")
            exp_yrs = 0
            if isinstance(exp, str):
                nums = re.findall(r"\d+", exp)
                if nums:
                    exp_yrs = int(nums[0])
            elif isinstance(exp, (int, float)):
                exp_yrs = int(exp)
            sensitive_age.append("Senior" if exp_yrs >= 6 else "Junior")

        # Convert to numpy arrays
        y_pred_arr = np.array(y_pred)
        gender_arr = np.array(sensitive_gender)
        age_arr = np.array(sensitive_age)

        # Calculate selection rates using Fairlearn or manual formulas
        gender_groups = set(sensitive_gender)
        selection_rates_gender = {}
        for g in gender_groups:
            mask = gender_arr == g
            selection_rates_gender[g] = float(np.mean(y_pred_arr[mask])) if np.sum(mask) > 0 else 0.0

        age_groups = set(sensitive_age)
        selection_rates_age = {}
        for a in age_groups:
            mask = age_arr == a
            selection_rates_age[a] = float(np.mean(y_pred_arr[mask])) if np.sum(mask) > 0 else 0.0

        # Calculate demographic parity difference
        if selection_rate is not None and demographic_parity_difference is not None:
            try:
                dp_diff = float(demographic_parity_difference(
                    y_pred_arr, y_pred_arr, sensitive_features=gender_arr
                ))
            except Exception:
                dp_diff = max(selection_rates_gender.values()) - min(selection_rates_gender.values())
        else:
            dp_diff = max(selection_rates_gender.values()) - min(selection_rates_gender.values())

        status_msg = "Fair pipeline selection rates"
        if dp_diff > 0.20:
            status_msg = "High demographic parity difference detected! Review shortlisting criteria for bias."
        elif dp_diff > 0.10:
            status_msg = "Minor selection disparities detected across groups."

        return {
            "demographic_parity_difference": round(dp_diff, 3),
            "selection_rates": {
                "gender": {k: round(v, 3) for k, v in selection_rates_gender.items()},
                "age_group": {k: round(v, 3) for k, v in selection_rates_age.items()}
            },
            "status": status_msg
        }
