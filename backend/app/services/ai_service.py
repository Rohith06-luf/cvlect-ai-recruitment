from app.services.resume_service import ResumeService


class AIService:
    @staticmethod
    def process_resume(file_path: str) -> dict:
        text = ResumeService.extract_text(file_path)
        parsed = ResumeService.parse_resume(file_path)
        ats_score = ResumeService.calculate_ats_score(text)
        match_percentage = ResumeService.calculate_match_percentage(ats_score)
        skills = ResumeService.extract_skills(text)
        summary = ResumeService.generate_summary(text)

        return {
            "text": text,
            "parsed": parsed,
            "ats_score": ats_score,
            "match_percentage": match_percentage,
            "skills": skills,
            "summary": summary,
        }
