import re
from typing import Any, List, Dict

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None

try:
    import spacy
except ImportError:
    spacy = None


class ResumeParser:
    def __init__(self) -> None:
        self.nlp = None
        if spacy is not None:
            try:
                self.nlp = spacy.load("en_core_web_sm")
            except OSError:
                # If the package was installed but the model wasn't downloaded yet
                self.nlp = spacy.blank("en")

        # Compile common technology skills list for keyword matching
        self.skills_db = {
            "python", "javascript", "typescript", "c++", "c#", "java", "ruby", "php", "go", "rust",
            "sql", "postgresql", "mysql", "sqlite", "mongodb", "redis", "cassandra", "elasticsearch",
            "html", "css", "react", "angular", "vue", "next.js", "tailwind", "bootstrap",
            "fastapi", "django", "flask", "express", "nest.js", "spring boot", "laravel",
            "aws", "azure", "gcp", "docker", "kubernetes", "git", "github", "jenkins", "terraform",
            "machine learning", "deep learning", "nlp", "computer vision", "tensorflow", "pytorch",
            "scikit-learn", "keras", "xgboost", "pandas", "numpy", "matplotlib", "seaborn", "nltk",
            "spacy", "transformer", "bert", "gpt", "llm", "shap", "fairlearn", "flan-t5", "faiss"
        }

    def extract_text_from_pdf(self, file_path: str) -> str:
        if fitz is None:
            return ""
        try:
            doc = fitz.open(file_path)
            text_chunks = []
            for page in doc:
                text_chunks.append(page.get_text())
            doc.close()
            return "\n".join(text_chunks)
        except Exception as e:
            print(f"Error reading PDF: {e}")
            return ""

    def parse(self, file_path_or_text: str) -> Dict[str, Any]:
        # Check if it's a file path (ends with .pdf or exists as file)
        import os
        if file_path_or_text.lower().endswith('.pdf') and os.path.exists(file_path_or_text):
            text = self.extract_text_from_pdf(file_path_or_text)
        else:
            text = file_path_or_text
            
        normalized_text = re.sub(r"\s+", " ", text).strip()
        
        # 1. Name Extraction using spaCy NER (PERSON) with fallback
        name = self._extract_name(text)
        
        # 2. Email Extraction
        email_match = re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text)
        email = email_match.group(0) if email_match else None
        
        # 3. Phone Extraction
        phone_match = re.search(r"(?:\+\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}|\+?\d{1,4}[-.\s]?\d{7,10}", text)
        phone = phone_match.group(0) if phone_match else None
        
        # 4. Skills extraction
        skills = self._extract_skills(text)
        
        # 5. Experience
        experience_years = self._estimate_experience(text)
        
        # 6. Education
        education = self._extract_education(text)
        
        # 7. Projects
        projects = self._extract_projects(text)
        
        # 8. Certifications
        certifications = self._extract_certifications(text)
        
        return {
            "name": name or "Candidate Profile",
            "email": email,
            "phone": phone,
            "skills": skills,
            "experience_years": experience_years,
            "education": education,
            "projects": projects,
            "certifications": certifications,
            "raw_text": text,
        }

    def _extract_name(self, text: str) -> str | None:
        # Check first 3 lines of text
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        if not lines:
            return None
            
        candidate_lines = lines[:4]
        
        # Check spaCy NER in the top lines
        if self.nlp is not None:
            # Join top lines to inspect entities
            header = " ".join(candidate_lines)
            doc = self.nlp(header)
            persons = [ent.text for ent in doc.ents if ent.label_ == "PERSON"]
            if persons:
                return persons[0]
                
        # Simple fallback rules
        for line in candidate_lines:
            # A valid name line should have no punctuation or numbers, and be 2-3 words
            if re.match(r"^[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2}$", line):
                return line
        return lines[0] if lines else None

    def _estimate_experience(self, text: str) -> int:
        # Look for phrases like "3+ years", "4 years of experience", etc.
        exp_matches = re.findall(r"(\d+)\s*(?:\+?\s*years?|yrs?)(?:\s+of\s+experience)?", text, re.IGNORECASE)
        if exp_matches:
            return int(exp_matches[0])
            
        # Fallback: check years range like 2018-2022 to estimate years
        year_ranges = re.findall(r"\b(20\d{2})\s*[-–—]\s*(20\d{2}|present)\b", text, re.IGNORECASE)
        if year_ranges:
            total_years = 0
            for start, end in year_ranges:
                start_yr = int(start)
                end_yr = 2026 if "present" in end.lower() else int(end)
                diff = end_yr - start_yr
                if 0 < diff < 20:
                    total_years += diff
            return max(1, total_years) if total_years > 0 else 0
            
        return 0

    def _extract_skills(self, text: str) -> List[str]:
        found_skills = set()
        text_lower = text.lower()
        
        # Direct word matching
        for skill in self.skills_db:
            # Use word boundaries so "go" doesn't match inside "government"
            pattern = rf"\b{re.escape(skill)}\b"
            # Support special characters like C++, C#
            if skill in {"c++", "c#"}:
                pattern = rf"\b{re.escape(skill)}"
            if re.search(pattern, text_lower):
                found_skills.add(skill.title() if len(skill) > 2 else skill.upper())
                
        # Fallback to structural extraction if headers are found
        header_skills = []
        normalized = re.sub(r"\s+", " ", text).strip()
        for marker in ["skills:", "technologies:", "technical skills:", "core competencies:"]:
            if marker in normalized.lower():
                part = normalized.lower().split(marker, 1)[1]
                # grab words up to the next section or end of sentence
                candidate_words = re.findall(r"[A-Za-z0-9+#.-]+", part[:300])
                for w in candidate_words:
                    w_clean = w.strip(" ,;:.()[]{}")
                    if w_clean.lower() in self.skills_db:
                        header_skills.append(w_clean.title() if len(w_clean) > 2 else w_clean.upper())
                        
        final_skills = list(found_skills | set(header_skills))
        return final_skills[:25]  # Cap at 25 skills

    def _extract_education(self, text: str) -> List[str]:
        # Search for degrees and institutions
        degree_patterns = [
            r"B\.Tech\b", r"M\.Tech\b", r"B\.E\b", r"M\.E\b", r"B\.S\b", r"M\.S\b",
            r"BSc\b", r"MSc\b", r"MBA\b", r"Ph\.D\b", r"PhD\b",
            r"Bachelor\s+of\s+[A-Za-z\s]+", r"Master\s+of\s+[A-Za-z\s]+",
            r"Bachelor's\b", r"Master's\b"
        ]
        found_edu = []
        for pattern in degree_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for m in matches:
                # Clean up punctuation spacing
                cleaned = re.sub(r"\s+", " ", m).strip()
                if cleaned not in found_edu:
                    found_edu.append(cleaned)
                    
        # Check institution names in lines
        inst_matches = re.findall(r"([^\n,]+(?:University|College|Institute|School)[^\n,]*)", text, re.IGNORECASE)
        for inst in inst_matches[:3]:
            cleaned_inst = inst.strip()
            if len(cleaned_inst) > 5 and cleaned_inst not in found_edu:
                found_edu.append(cleaned_inst)
                
        return found_edu[:5]

    def _extract_projects(self, text: str) -> List[str]:
        # Find sections that contain bullet points under a "Projects" or "Work Experience" header
        project_sections = re.findall(r"(?:projects?|academic projects?|key projects?)\s*[:\-]?\s*(.*?)(?=\n\s*(?:skills|education|experience|certifications|languages|activities|publications|$))", text, re.IGNORECASE | re.DOTALL)
        if project_sections:
            content = project_sections[0]
            # Split by lines and search for lines that start with bullet points or have bold markers
            lines = [l.strip() for l in content.split("\n") if l.strip()]
            bullets = [l.lstrip("•*- ") for l in lines if l.startswith(("•", "*", "-", "1.", "2.", "3."))]
            if bullets:
                return bullets[:5]
            return lines[:4]
            
        # Fallback regex search for project mentions
        project_matches = re.findall(r"(?:project|developed|built)\s+([^\n]+)", text, re.IGNORECASE)
        return [p.strip() for p in project_matches[:4] if len(p.strip()) > 10]

    def _extract_certifications(self, text: str) -> List[str]:
        # Find certifications
        cert_patterns = [
            r"AWS Certified\s+[A-Za-z\s]+", r"Google Cloud\s+[A-Za-z\s]+",
            r"Microsoft Certified\s+[A-Za-z\s]+", r"Azure\s+[A-Za-z\s]+",
            r"Docker Certified\s+[A-Za-z\s]+", r"Kubernetes\s+[A-Za-z\s]+",
            r"Oracle Certified\s+[A-Za-z\s]+", r"Cisco Certified\s+[A-Za-z\s]+"
        ]
        found_certs = []
        for pattern in cert_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for m in matches:
                cleaned = m.strip()
                if cleaned not in found_certs:
                    found_certs.append(cleaned)
                    
        # Check standard headers
        cert_sections = re.findall(r"(?:certifications?|licenses?|professional certifications?)\s*[:\-]?\s*(.*?)(?=\n\s*(?:education|experience|skills|projects|languages|$))", text, re.IGNORECASE | re.DOTALL)
        if cert_sections:
            lines = [l.strip().lstrip("•*- ") for l in cert_sections[0].split("\n") if l.strip()]
            for line in lines[:4]:
                if len(line) > 5 and line not in found_certs:
                    found_certs.append(line)
                    
        return found_certs[:5]
