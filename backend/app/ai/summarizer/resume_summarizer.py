from typing import Any, Dict

from app.ai.summarizer.nim_client import NIMClient

try:
    from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
except ImportError:
    AutoModelForSeq2SeqLM = None
    AutoTokenizer = None


class ResumeSummarizer:
    _tokenizer = None
    _model = None

    @classmethod
    def get_model_and_tokenizer(cls):
        if AutoModelForSeq2SeqLM is None or AutoTokenizer is None:
            return None, None
            
        if cls._model is None or cls._tokenizer is None:
            try:
                # Load the instruction-tuned FLAN-T5 model
                # We use the google/flan-t5-base model as requested
                model_name = "google/flan-t5-base"
                cls._tokenizer = AutoTokenizer.from_pretrained(model_name)
                cls._model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
            except Exception as e:
                print(f"Error loading FLAN-T5 model: {e}")
                
        return cls._model, cls._tokenizer

    def summarize(self, candidate: Dict[str, Any]) -> Dict[str, Any]:
        parsed = candidate.get("parsed_resume", {})
        name = parsed.get("name", "The candidate")
        experience = parsed.get("experience_years", 0)
        skills = parsed.get("skills", [])
        education = parsed.get("education", [])
        projects = parsed.get("projects", [])
        certifications = parsed.get("certifications", [])

        # Construct prompt
        skills_str = ", ".join(skills[:8]) if skills else "various technical skills"
        edu_str = ", ".join(education[:2]) if education else "a relevant degree"
        proj_str = ", ".join(projects[:2]) if projects else "multiple technical projects"
        
        prompt = (
            f"Write a short, professional one-sentence summary for a candidate with the following profile: "
            f"Name: {name}. "
            f"Experience: {experience} years. "
            f"Skills: {skills_str}. "
            f"Education: {edu_str}. "
            f"Projects: {proj_str}. "
            f"Professional summary:"
        )

        summary_text = None
        nim_client = NIMClient()
        if nim_client.is_configured():
            try:
                nim_prompt = (
                    f"Write a concise, professional resume summary for a candidate with the following profile:\n"
                    f"Name: {name}\n"
                    f"Experience: {experience} years\n"
                    f"Skills: {skills_str}\n"
                    f"Education: {edu_str}\n"
                    f"Projects: {proj_str}\n"
                )
                if candidate.get("job_description"):
                    nim_prompt += f"Job description: {candidate['job_description']}\n"
                nim_prompt += "Summary:"
                summary_text = nim_client.generate(nim_prompt)
            except Exception as e:
                print(f"NIM generation failed: {e}. Falling back to local summarizer.")

        if not summary_text:
            model, tokenizer = self.get_model_and_tokenizer()
            if model is not None and tokenizer is not None:
                try:
                    inputs = tokenizer(prompt, return_tensors="pt", max_length=512, truncation=True)
                    outputs = model.generate(
                        **inputs,
                        max_length=150,
                        num_beams=4,
                        early_stopping=True,
                    )
                    summary_text = tokenizer.decode(outputs[0], skip_special_tokens=True).strip()
                except Exception as e:
                    print(f"FLAN-T5 generation failed: {e}. Falling back to template summarizer.")

        # Fallback Template Summarizer
        if not summary_text:
            exp_text = f"{experience} years" if experience else "a solid background"
            skills_text = f"in {', '.join(skills[:4])}" if skills else "in software engineering"
            cert_text = f" and holds certifications like {', '.join(certifications[:2])}" if certifications else ""
            summary_text = (
                f"{name} has {exp_text} of professional experience with strong expertise {skills_text}{cert_text}. "
                f"They have successfully delivered projects including {', '.join(projects[:2]) or 'several backend and frontend systems'}."
            )

        return {
            "summary": summary_text,
            "highlights": projects[:3],
            "education": education,
            "certifications": certifications,
        }
