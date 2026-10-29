"""
CVlect AI — Resume Parser Pipeline
Extracts structured data from PDF and DOCX resumes using PyMuPDF, python-docx,
spaCy NER, and robust regex/rule-based heuristics.
"""

import re
import os
from datetime import datetime
from typing import Optional, Any
from app.config import settings
from app.utils import get_logger

logger = get_logger(__name__)

# Lazy spaCy model loader
_nlp = None
_spacy_attempted = False


def get_spacy_nlp():
    """Lazily load spaCy model or fall back to None if unavailable."""
    global _nlp, _spacy_attempted
    if not _spacy_attempted:
        _spacy_attempted = True
        try:
            import spacy
            _nlp = spacy.load(settings.spacy_model)
            logger.info(f"Loaded spaCy model '{settings.spacy_model}'")
        except Exception as e:
            logger.warning(
                f"Could not load spaCy model '{settings.spacy_model}' ({e}). Falling back to pattern-based extraction."
            )
            _nlp = None
    return _nlp


# =============================================================================
# Skill Dictionaries & Taxonomies
# =============================================================================

TECHNICAL_SKILLS_TAXONOMY: dict[str, list[str]] = {
    "languages": [
        "python", "javascript", "typescript", "java", "c++", "c#", "c", "go", "golang",
        "rust", "ruby", "php", "swift", "kotlin", "scala", "r", "matlab", "dart",
        "bash", "shell", "powershell", "perl", "sql", "html", "html5", "css", "css3", "sass", "scss",
    ],
    "frameworks_and_libraries": [
        "react", "react.js", "reactjs", "angular", "vue", "vue.js", "vuejs", "next.js", "nextjs",
        "nuxt", "node.js", "nodejs", "express", "express.js", "fastapi", "django", "flask",
        "spring", "spring boot", "asp.net", ".net", "dotnet", "laravel", "ruby on rails", "rails",
        "pytorch", "tensorflow", "keras", "scikit-learn", "sklearn", "pandas", "numpy", "scipy",
        "huggingface", "opencv", "nltk", "spacy", "langchain", "llamaindex", "celery",
        "graphql", "rest", "restful api", "grpc", "redux", "tailwind", "tailwindcss", "bootstrap",
    ],
    "cloud_and_devops": [
        "aws", "amazon web services", "azure", "microsoft azure", "gcp", "google cloud", "google cloud platform",
        "docker", "kubernetes", "k8s", "terraform", "ansible", "jenkins", "gitlab ci", "github actions",
        "ci/cd", "prometheus", "grafana", "helm", "circleci", "linux", "ubuntu", "nginx", "apache",
        "serverless", "lambda", "ecs", "eks", "cloudformation", "argo cd",
    ],
    "databases_and_storage": [
        "postgresql", "postgres", "mysql", "mongodb", "redis", "elasticsearch", "sqlite",
        "cassandra", "dynamodb", "oracle", "mariadb", "neo4j", "snowflake", "bigquery",
        "clickhouse", "firestore", "supabase", "kafka", "rabbitmq",
    ],
    "ai_and_data": [
        "machine learning", "deep learning", "natural language processing", "nlp", "computer vision",
        "data engineering", "data analysis", "data science", "etl", "spark", "apache spark",
        "hadoop", "airflow", "tableau", "power bi", "large language models", "llm", "rag",
        "vector databases", "fine-tuning", "prompt engineering", "neural networks", "reinforcement learning",
    ],
    "tools_and_methods": [
        "git", "github", "gitlab", "bitbucket", "jira", "confluence", "trello",
        "agile", "scrum", "kanban", "tdd", "unit testing", "pytest", "jest", "postman",
        "microservices", "system design", "distributed systems", "oop", "design patterns",
    ],
}

# Flatten technical skills for quick lookup
ALL_TECH_SKILLS = set()
for category_skills in TECHNICAL_SKILLS_TAXONOMY.values():
    for skill in category_skills:
        ALL_TECH_SKILLS.add(skill.lower())

SOFT_SKILLS_LIST = [
    "leadership", "communication", "teamwork", "collaboration", "problem solving",
    "critical thinking", "adaptability", "flexibility", "time management",
    "project management", "decision making", "creativity", "interpersonal skills",
    "mentorship", "coaching", "presentation", "negotiation", "conflict resolution",
    "work ethic", "attention to detail", "emotional intelligence", "strategic thinking",
    "customer focus", "ownership", "multitasking", "active listening",
]


# =============================================================================
# Document Text Extraction
# =============================================================================

def extract_text_from_pdf(file_path: str) -> str:
    """Extract clean raw text from a PDF file using PyMuPDF (fitz)."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"PDF file not found: {file_path}")

    text_parts = []
    try:
        import fitz  # PyMuPDF
        with fitz.open(file_path) as doc:
            for page_num in range(len(doc)):
                page = doc[page_num]
                page_text = page.get_text("text")
                if page_text:
                    text_parts.append(page_text)
    except ImportError:
        logger.error("PyMuPDF (fitz) is not installed.")
        raise RuntimeError("PyMuPDF is required for PDF parsing.")
    except Exception as e:
        logger.error(f"Failed to extract text from PDF '{file_path}': {e}")
        raise

    full_text = "\n".join(text_parts).strip()
    return clean_text(full_text)


def extract_text_from_docx(file_path: str) -> str:
    """Extract clean raw text from a DOCX file using python-docx."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"DOCX file not found: {file_path}")

    text_parts = []
    try:
        import docx
        doc = docx.Document(file_path)
        for para in doc.paragraphs:
            if para.text.strip():
                text_parts.append(para.text.strip())
        for table in doc.tables:
            for row in table.rows:
                row_text = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                if row_text:
                    text_parts.append(" | ".join(row_text))
    except ImportError:
        logger.error("python-docx is not installed.")
        raise RuntimeError("python-docx is required for DOCX parsing.")
    except Exception as e:
        logger.error(f"Failed to extract text from DOCX '{file_path}': {e}")
        raise

    full_text = "\n".join(text_parts).strip()
    return clean_text(full_text)


def clean_text(text: str) -> str:
    """Normalize whitespace and control characters."""
    if not text:
        return ""
    # Replace non-breaking spaces and unusual whitespace
    text = text.replace("\xa0", " ").replace("\r\n", "\n").replace("\r", "\n")
    # Collapse multiple blank lines
    text = re.sub(r'\n{3,}', '\n\n', text)
    # Collapse consecutive spaces
    text = re.sub(r'[ \t]+', ' ', text)
    return text.strip()


# =============================================================================
# Information Extraction Routines
# =============================================================================

def extract_contact_info(text: str) -> dict[str, Optional[str]]:
    """Extract email, phone, links, name, and location from resume text."""
    contact = {
        "name": None,
        "email": None,
        "phone": None,
        "location": None,
        "linkedin": None,
        "github": None,
    }

    # 1. Email
    email_match = re.search(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', text)
    if email_match:
        contact["email"] = email_match.group(0).lower().rstrip('.')

    # 2. Phone
    phone_pattern = r'(?:\+?\d{1,3}[\s.-]?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}'
    phone_match = re.search(phone_pattern, text)
    if phone_match:
        contact["phone"] = phone_match.group(0).strip()

    # 3. LinkedIn
    linkedin_match = re.search(
        r'(?:https?:\/\/)?(?:www\.)?linkedin\.com\/in\/([a-zA-Z0-9_-]+)',
        text,
        re.IGNORECASE,
    )
    if linkedin_match:
        contact["linkedin"] = f"https://linkedin.com/in/{linkedin_match.group(1)}"

    # 4. GitHub
    github_match = re.search(
        r'(?:https?:\/\/)?(?:www\.)?github\.com\/([a-zA-Z0-9_-]+)',
        text,
        re.IGNORECASE,
    )
    if github_match:
        username = github_match.group(1)
        if username.lower() not in ["features", "explore", "topics", "pulls", "issues", "marketplace"]:
            contact["github"] = f"https://github.com/{username}"

    # 5. Candidate Name Extraction
    nlp = get_spacy_nlp()
    first_lines = [line.strip() for line in text.split("\n")[:10] if line.strip()]

    if nlp and first_lines:
        top_snippet = "\n".join(first_lines[:4])
        doc = nlp(top_snippet)
        for ent in doc.ents:
            if ent.label_ == "PERSON" and len(ent.text.split()) in [2, 3, 4]:
                # Exclude strings containing digits or contact keywords
                if not any(char.isdigit() for char in ent.text) and "@" not in ent.text:
                    contact["name"] = ent.text.strip()
                    break

    # Fallback to first non-empty header line if spaCy didn't catch name
    if not contact["name"] and first_lines:
        for candidate_line in first_lines[:3]:
            cleaned_line = re.sub(r'[^a-zA-Z\s]', '', candidate_line).strip()
            words = cleaned_line.split()
            if 2 <= len(words) <= 4 and all(w[0].isupper() for w in words if len(w) > 1):
                contact["name"] = cleaned_line
                break

    # 6. Location Detection
    location_pattern = r'\b([A-Z][a-zA-Z]+(?:[\s-][A-Z][a-zA-Z]+)*),\s*([A-Z]{2}|[A-Z][a-zA-Z]+)\b'
    loc_match = re.search(location_pattern, "\n".join(first_lines[:8]))
    if loc_match:
        contact["location"] = loc_match.group(0).strip()
    elif nlp:
        top_doc = nlp("\n".join(first_lines[:6]))
        for ent in top_doc.ents:
            if ent.label_ == "GPE":
                contact["location"] = ent.text.strip()
                break

    return contact


def extract_skills(text: str) -> tuple[list[str], list[str], list[str]]:
    """
    Extract skills from text, dividing them into all skills, technical skills, and soft skills.
    Returns: (all_skills, technical_skills, soft_skills)
    """
    text_lower = " " + text.lower() + " "
    matched_tech = set()
    matched_soft = set()

    # Search technical skills with word-boundary awareness
    for skill in ALL_TECH_SKILLS:
        # For short skills like c, r, go, use explicit boundary
        if len(skill) <= 2 or skill in ["c", "r", "go", "c++", "c#", ".net"]:
            escaped = re.escape(skill)
            pattern = rf'(?:^|[\s,;/()\-]){escaped}(?:$|[\s,;/()\-])'
            if re.search(pattern, text_lower):
                matched_tech.add(skill)
        else:
            escaped = re.escape(skill)
            pattern = rf'\b{escaped}\b'
            if re.search(pattern, text_lower):
                matched_tech.add(skill)

    # Search soft skills
    for skill in SOFT_SKILLS_LIST:
        escaped = re.escape(skill)
        if re.search(rf'\b{escaped}\b', text_lower):
            matched_soft.add(skill)

    tech_list = sorted(list(matched_tech))
    soft_list = sorted(list(matched_soft))
    all_skills = sorted(list(matched_tech | matched_soft))

    return all_skills, tech_list, soft_list


def extract_education(text: str) -> list[dict[str, Any]]:
    """Extract education history: degree, institution, field, year, GPA."""
    education_entries = []

    degree_patterns = [
        (r'\b(Ph\.?D\.?|Doctor of Philosophy|Doctorate)\b', "Ph.D."),
        (r'\b(Master of Science|M\.?S\.?|Master of Arts|M\.?A\.?|M\.?Tech|MBA|Master\'s)\b', "Master's"),
        (r'\b(Bachelor of Science|B\.?S\.?|Bachelor of Arts|B\.?A\.?|B\.?Tech|B\.?E\.?|Bachelor\'s)\b', "Bachelor's"),
        (r'\b(Associate of Science|Associate of Arts|Associate\'s Degree|Associate)\b', "Associate's"),
        (r'\b(Diploma|High School Diploma)\b', "Diploma"),
    ]

    field_keywords = [
        "Computer Science", "Software Engineering", "Information Technology", "Data Science",
        "Artificial Intelligence", "Electrical Engineering", "Mechanical Engineering",
        "Computer Engineering", "Mathematics", "Statistics", "Physics", "Business Administration",
        "Economics", "Cybersecurity", "Bioinformatics", "Information Systems",
    ]

    # Find education section lines
    lines = text.split("\n")
    edu_section = False
    edu_lines = []

    for line in lines:
        stripped = line.strip()
        if re.match(r'^(?:EDUCATION|ACADEMIC BACKGROUND|ACADEMIC QUALIFICATIONS)\b', stripped, re.IGNORECASE):
            edu_section = True
            continue
        elif edu_section and re.match(r'^(?:EXPERIENCE|WORK EXPERIENCE|SKILLS|PROJECTS|CERTIFICATIONS|PUBLICATIONS)\b', stripped, re.IGNORECASE):
            edu_section = False
            break
        elif edu_section:
            edu_lines.append(stripped)

    # If education header not found, scan whole text
    search_text = "\n".join(edu_lines) if edu_lines else text

    # Extract entries based on degree patterns
    for deg_regex, norm_degree in degree_patterns:
        for match in re.finditer(deg_regex, search_text, re.IGNORECASE):
            start = max(0, match.start() - 100)
            end = min(len(search_text), match.end() + 200)
            context = search_text[start:end]

            # Institution heuristics
            inst_match = re.search(
                r'\b([A-Z][a-zA-Z\s&]+(?:University|Institute|College|Academy|School of [A-Za-z]+))\b',
                context,
            )
            institution = inst_match.group(1).strip() if inst_match else None

            # Year extraction
            year_match = re.search(r'\b(19\d{2}|20\d{2})\b', context)
            year = year_match.group(1) if year_match else None

            # Field extraction
            field = None
            for fk in field_keywords:
                if re.search(rf'\b{re.escape(fk)}\b', context, re.IGNORECASE):
                    field = fk
                    break

            # GPA
            gpa_match = re.search(r'\b(?:GPA|CGPA)[:\s]*([0-4]\.\d{1,2}|[0-9]\.\d{1,2}\s*/\s*10|[0-9]\.\d{1,2})', context, re.IGNORECASE)
            gpa = gpa_match.group(1) if gpa_match else None

            entry = {
                "degree": norm_degree,
                "institution": institution,
                "field": field,
                "year": year,
                "gpa": gpa,
            }
            # Deduplicate by degree + institution
            if not any(e["degree"] == entry["degree"] and e["institution"] == entry["institution"] for e in education_entries):
                education_entries.append(entry)

    return education_entries


def extract_experience(text: str) -> tuple[list[dict[str, Any]], float]:
    """
    Extract work experience items and calculate total estimated years.
    Returns: (experience_entries, total_experience_years)
    """
    experience_entries = []

    # Identify Experience section
    lines = text.split("\n")
    exp_section = False
    exp_lines = []

    for line in lines:
        stripped = line.strip()
        if re.match(r'^(?:WORK EXPERIENCE|EXPERIENCE|EMPLOYMENT HISTORY|PROFESSIONAL EXPERIENCE)\b', stripped, re.IGNORECASE):
            exp_section = True
            continue
        elif exp_section and re.match(r'^(?:EDUCATION|SKILLS|PROJECTS|CERTIFICATIONS|PUBLICATIONS|INTERESTS)\b', stripped, re.IGNORECASE):
            exp_section = False
            break
        elif exp_section:
            exp_lines.append(stripped)

    working_text = "\n".join(exp_lines) if exp_lines else text

    date_range_pattern = r'((?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?|\d{2}/\d{4}|\d{4})\s*(?:-|–|to)\s*(?:Present|Current|Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?|\d{2}/\d{4}|\d{4}))'

    matches = list(re.finditer(date_range_pattern, working_text, re.IGNORECASE))
    total_months = 0

    common_titles = [
        "Software Engineer", "Senior Software Engineer", "Full Stack Developer", "Backend Developer",
        "Frontend Developer", "Data Scientist", "Machine Learning Engineer", "DevOps Engineer",
        "Cloud Architect", "Product Manager", "Project Manager", "Data Analyst", "Systems Architect",
        "QA Engineer", "Security Engineer", "Engineering Manager", "Technical Lead", "Intern",
    ]

    for i, match in enumerate(matches):
        date_str = match.group(1).strip()
        start_pos = match.start()
        end_pos = matches[i + 1].start() if i + 1 < len(matches) else min(len(working_text), start_pos + 600)
        snippet = working_text[max(0, start_pos - 150):end_pos].strip()

        # Extract title
        title = None
        for t in common_titles:
            if re.search(rf'\b{re.escape(t)}\b', snippet, re.IGNORECASE):
                title = t
                break

        # Extract company heuristics
        comp_match = re.search(r'\b(?:at|@|,)\s*([A-Z][a-zA-Z0-9\s&]+(?:Inc|LLC|Ltd|Technologies|Solutions|Corp|Labs|Systems)?)\b', snippet)
        company = comp_match.group(1).strip() if comp_match else None

        # Extract technologies used in this role
        role_skills, _, _ = extract_skills(snippet)

        # Estimate duration in months
        months = parse_date_range_duration(date_str)
        total_months += months

        dates = date_str.split("-") if "-" in date_str else date_str.split("–") if "–" in date_str else date_str.split("to")
        start_date = dates[0].strip() if dates else None
        end_date = dates[1].strip() if len(dates) > 1 else "Present"

        entry = {
            "title": title or "Professional Role",
            "company": company,
            "start_date": start_date,
            "end_date": end_date,
            "description": snippet[:350].strip(),
            "technologies": role_skills[:8],
        }
        experience_entries.append(entry)

    # Fallback year calculation: parse distinct year spans
    if total_months == 0:
        years_found = [int(y) for y in re.findall(r'\b(19\d{2}|20\d{2})\b', working_text)]
        if years_found:
            curr_year = datetime.now().year
            valid_years = [y for y in years_found if 1980 <= y <= curr_year]
            if valid_years:
                span = max(valid_years) - min(valid_years)
                total_years = min(float(span), 30.0)
            else:
                total_years = 0.0
        else:
            total_years = 0.0
    else:
        total_years = round(total_months / 12.0, 1)

    return experience_entries, total_years


def parse_date_range_duration(date_str: str) -> int:
    """Helper to convert a date range string into approximate months."""
    curr_year = datetime.now().year
    years = [int(y) for y in re.findall(r'\b(19\d{2}|20\d{2})\b', date_str)]
    if not years:
        return 0
    if len(years) == 1:
        if re.search(r'present|current', date_str, re.IGNORECASE):
            return max(1, (curr_year - years[0]) * 12)
        return 12  # default 1 year
    start_year, end_year = years[0], years[1]
    return max(1, (end_year - start_year) * 12)


def extract_certifications(text: str) -> list[dict[str, Any]]:
    """Extract recognized industry certifications."""
    certs = []
    cert_patterns = [
        (r'\b(AWS Certified [A-Za-z\s]+)\b', "Amazon Web Services"),
        (r'\b(Microsoft Certified:? [A-Za-z\s]+|Azure Fundamentals|Azure Administrator)\b', "Microsoft"),
        (r'\b(Google Cloud Certified [A-Za-z\s]+)\b', "Google Cloud"),
        (r'\b(Certified Kubernetes Administrator|CKA|CKAD)\b', "Cloud Native Computing Foundation"),
        (r'\b(Certified Information Systems Security Professional|CISSP)\b', "ISC2"),
        (r'\b(Project Management Professional|PMP)\b', "Project Management Institute"),
        (r'\b(Certified Scrum Master|CSM)\b', "Scrum Alliance"),
        (r'\b(CompTIA (?:Security\+|Network\+|A\+))\b', "CompTIA"),
        (r'\b(TensorFlow Developer Certificate)\b', "Google"),
    ]

    for pattern, issuer in cert_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            cert_name = match.group(0).strip()
            certs.append({
                "name": cert_name,
                "issuer": issuer,
                "year": None,
            })
    return certs


def extract_projects(text: str) -> list[dict[str, Any]]:
    """Extract project names and descriptions from project section."""
    projects = []
    lines = text.split("\n")
    proj_section = False
    proj_lines = []

    for line in lines:
        stripped = line.strip()
        if re.match(r'^(?:PROJECTS|PERSONAL PROJECTS|ACADEMIC PROJECTS|KEY PROJECTS)\b', stripped, re.IGNORECASE):
            proj_section = True
            continue
        elif proj_section and re.match(r'^(?:EXPERIENCE|EDUCATION|SKILLS|CERTIFICATIONS|ACHIEVEMENTS)\b', stripped, re.IGNORECASE):
            proj_section = False
            break
        elif proj_section:
            proj_lines.append(stripped)

    content = "\n".join(proj_lines)
    if content:
        # Split projects by bullet points or headers
        blocks = re.split(r'\n(?=[A-Z][a-zA-Z0-9\s-]{2,40}(?::|\s-\s|\n))', content)
        for block in blocks[:6]:
            if len(block.strip()) < 15:
                continue
            first_line = block.strip().split("\n")[0]
            name = re.sub(r'[:|].*', '', first_line).strip()
            techs, _, _ = extract_skills(block)
            projects.append({
                "name": name[:60],
                "description": block.strip()[:300],
                "technologies": techs[:6],
                "url": None,
            })

    return projects


def extract_keywords_and_domains(text: str) -> tuple[list[str], list[str]]:
    """Extract domain keywords and concepts."""
    domains = [
        "fintech", "healthcare", "e-commerce", "edtech", "automotive",
        "biotech", "cybersecurity", "telecommunications", "gaming", "aerospace",
        "banking", "insurance", "logistics", "supply chain", "social media",
    ]
    text_lower = text.lower()
    found_domains = [d for d in domains if re.search(rf'\b{re.escape(d)}\b', text_lower)]

    # Keywords: key concepts extracted from resume
    concept_list = [
        "scalable architecture", "rest api", "ci/cd pipeline", "microservices",
        "distributed systems", "cloud native", "data pipeline", "database indexing",
        "test automation", "code review", "agile development", "performance optimization",
    ]
    found_concepts = [c for c in concept_list if c in text_lower]

    return found_concepts, found_domains


# =============================================================================
# Quality Evaluation & Suggestions
# =============================================================================

def calculate_quality_metrics(
    contact: dict,
    skills: list[str],
    education: list[dict],
    experience: list[dict],
    projects: list[dict],
    certifications: list[dict],
    text_length: int,
) -> tuple[float, dict[str, float], list[str], list[str]]:
    """
    Score the completeness and quality of the resume.
    Returns: (quality_score, confidence_scores, missing_fields, suggestions)
    """
    score = 0.0
    missing_fields = []
    suggestions = []

    # Confidence per section
    confidence_scores = {
        "contact_info": 0.0,
        "skills": 0.0,
        "education": 0.0,
        "experience": 0.0,
        "projects": 0.0,
    }

    # 1. Contact Info (max 20 pts)
    contact_pts = 0.0
    if contact.get("email"):
        contact_pts += 8.0
    else:
        missing_fields.append("email")
        suggestions.append("Provide a professional email address.")

    if contact.get("phone"):
        contact_pts += 6.0
    else:
        missing_fields.append("phone")
        suggestions.append("Add a contact phone number.")

    if contact.get("linkedin"):
        contact_pts += 3.0
    else:
        suggestions.append("Include a LinkedIn profile link for recruiter visibility.")

    if contact.get("github"):
        contact_pts += 3.0

    confidence_scores["contact_info"] = round(contact_pts / 20.0, 2)
    score += contact_pts

    # 2. Skills (max 25 pts)
    if len(skills) >= 10:
        score += 25.0
        confidence_scores["skills"] = 0.95
    elif len(skills) >= 5:
        score += 18.0
        confidence_scores["skills"] = 0.80
    elif len(skills) >= 1:
        score += 10.0
        confidence_scores["skills"] = 0.50
        suggestions.append("Highlight more specific technical skills and tools.")
    else:
        missing_fields.append("skills")
        suggestions.append("Add a dedicated Skills section covering your core technologies.")

    # 3. Experience (max 25 pts)
    if len(experience) >= 2:
        score += 25.0
        confidence_scores["experience"] = 0.90
    elif len(experience) == 1:
        score += 15.0
        confidence_scores["experience"] = 0.70
        suggestions.append("Provide more detail or metrics for your professional experience.")
    else:
        missing_fields.append("experience")
        confidence_scores["experience"] = 0.20
        suggestions.append("Detail your past employment, responsibilities, and key achievements.")

    # 4. Education (max 15 pts)
    if education:
        score += 15.0
        confidence_scores["education"] = 0.90
    else:
        missing_fields.append("education")
        confidence_scores["education"] = 0.10
        suggestions.append("Add your educational background, including degree and institution.")

    # 5. Projects & Certifications (max 15 pts)
    bonus_pts = 0.0
    if projects:
        bonus_pts += 8.0
        confidence_scores["projects"] = 0.85
    else:
        suggestions.append("Include key portfolio projects to demonstrate practical abilities.")

    if certifications:
        bonus_pts += 7.0
    else:
        missing_fields.append("certifications")

    score += bonus_pts

    # Length sanity check
    if text_length < 200:
        score = min(score, 30.0)
        suggestions.append("Resume content appears very short. Ensure all relevant experience is included.")

    quality_score = round(min(100.0, score), 1)

    return quality_score, confidence_scores, missing_fields, suggestions


# =============================================================================
# Main Entry Point
# =============================================================================

def parse_resume(text: str) -> dict[str, Any]:
    """
    Parse a resume's text content into a fully structured dictionary.
    Guaranteed to extract only factual information from the text.
    """
    cleaned = clean_text(text)
    if not cleaned:
        return {
            "contact_info": {},
            "skills": [],
            "technical_skills": [],
            "soft_skills": [],
            "education": [],
            "experience": [],
            "certifications": [],
            "projects": [],
            "keywords": [],
            "domain_knowledge": [],
            "total_experience_years": 0.0,
            "confidence_scores": {},
            "missing_fields": ["all"],
            "quality_score": 0.0,
            "quality_suggestions": ["Document is empty or unreadable."],
        }

    contact = extract_contact_info(cleaned)
    all_skills, tech_skills, soft_skills = extract_skills(cleaned)
    education = extract_education(cleaned)
    experience, total_years = extract_experience(cleaned)
    certifications = extract_certifications(cleaned)
    projects = extract_projects(cleaned)
    keywords, domains = extract_keywords_and_domains(cleaned)

    quality_score, confidence_scores, missing_fields, suggestions = calculate_quality_metrics(
        contact=contact,
        skills=all_skills,
        education=education,
        experience=experience,
        projects=projects,
        certifications=certifications,
        text_length=len(cleaned),
    )

    return {
        "contact_info": contact,
        "skills": all_skills,
        "technical_skills": tech_skills,
        "soft_skills": soft_skills,
        "education": education,
        "experience": experience,
        "certifications": certifications,
        "projects": projects,
        "keywords": keywords,
        "domain_knowledge": domains,
        "total_experience_years": total_years,
        "confidence_scores": confidence_scores,
        "missing_fields": missing_fields,
        "quality_score": quality_score,
        "quality_suggestions": suggestions,
    }
