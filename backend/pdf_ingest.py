"""
PDF ingestion script.

Extracts candidate data from PDF resumes and inserts it into the database.

Supports two modes:
  1. Single PDF:    python pdf_ingest.py path/to/resume.pdf
  2. Directory:      python pdf_ingest.py path/to/resumes_folder/

The script uses pdfplumber to extract text, then parses common resume fields
(name, email, phone, skills, experience, summary) using simple heuristics.
You can also import `ingest_pdf(path)` from other modules.

Requires: pdfplumber  (pip install pdfplumber)
"""
from __future__ import annotations
import os
import re
import sys
import hashlib
from typing import Optional, List, Dict, Tuple

from db import init_db, get_db


# ---------- PDF text extraction ----------
def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract all text from a PDF using pdfplumber."""
    import pdfplumber  # imported lazily so the module can be imported without the dep

    text_parts: List[str] = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text_parts.append(page.extract_text() or "")
    return "\n".join(text_parts)


# ---------- Heuristic parsing ----------
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE_RE = re.compile(r"(\+?\d[\d\s\-().]{7,}\d)")
KNOWN_SKILLS = [
    "React", "TypeScript", "JavaScript", "Node.js", "Node", "Python", "Java",
    "GraphQL", "Rust", "Go", "C++", "C#", "Ruby", "PHP", "Swift", "Kotlin",
    "HTML", "CSS", "Tailwind", "Sass", "SCSS", "Next.js", "Vue", "Angular",
    "Svelte", "Redux", "Express", "FastAPI", "Flask", "Django", "Spring",
    "PostgreSQL", "MySQL", "SQLite", "MongoDB", "Redis", "Firebase",
    "AWS", "Azure", "GCP", "Docker", "Kubernetes", "CI/CD", "Jenkins",
    "Git", "Linux", "Testing", "Jest", "Cypress", "Playwright", "Vitest",
    "Design Systems", "Accessibility", "Performance", "Figma", "System Design",
    "Microservices", "REST", "API", "GraphQL", "Webpack", "Vite", "Bun",
    "Tailwind CSS", "Storybook", "Lerna", "Nx", "Turborepo",
]


def parse_email(text: str) -> Optional[str]:
    m = EMAIL_RE.search(text)
    return m.group(0) if m else None


def parse_phone(text: str) -> Optional[str]:
    m = PHONE_RE.search(text)
    return m.group(0).strip() if m else None


def parse_name(text: str) -> Optional[str]:
    """The first non-empty line is usually the name on a resume."""
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        # Skip lines that look like contact info
        if EMAIL_RE.search(line) or PHONE_RE.search(line):
            continue
        # Strip leading bullets/numbers
        line = re.sub(r"^[•\-\*\d\.\)\s]+", "", line)
        if 2 <= len(line.split()) <= 5 and len(line) < 60:
            return line
    return None


def parse_skills(text: str) -> List[str]:
    found: List[str] = []
    lower = text.lower()
    for skill in KNOWN_SKILLS:
        if skill.lower() in lower and skill not in found:
            found.append(skill)
    return found


def parse_experience(text: str) -> Optional[str]:
    """Try to find 'X years' or 'X yrs' of experience."""
    m = re.search(r"(\d+)\s*\+?\s*(?:years?|yrs?)\s*(?:of)?\s*experience", text, re.IGNORECASE)
    if m:
        return f"{m.group(1)} yrs"
    m = re.search(r"(\d+)\s*\+?\s*(?:years?|yrs?)", text, re.IGNORECASE)
    if m:
        return f"{m.group(1)} yrs"
    return None


def parse_summary(text: str) -> str:
    """Grab the first 2-3 sentences as a summary."""
    # Remove excessive whitespace
    cleaned = re.sub(r"\s+", " ", text).strip()
    sentences = re.split(r"(?<=[.!?])\s+", cleaned)
    summary = " ".join(sentences[:3])
    return summary[:300] if summary else ""


def parse_location(text: str) -> Optional[str]:
    """Look for a 'City, Country' or 'City, ST' pattern near contact info."""
    m = re.search(r"([A-Z][a-zA-Z]+(?:\s[A-Z][a-zA-Z]+)?,\s*(?:[A-Z]{2}|[A-Z][a-zA-Z]+))", text)
    return m.group(1) if m else None


def parse_resume_pdf(pdf_path: str) -> Dict:
    """Extract structured data from a single PDF resume."""
    text = extract_text_from_pdf(pdf_path)
    name = parse_name(text) or os.path.splitext(os.path.basename(pdf_path))[0]
    email = parse_email(text)
    phone = parse_phone(text)
    skills = parse_skills(text)
    experience = parse_experience(text)
    summary = parse_summary(text)
    location = parse_location(text)

    return {
        "name": name,
        "email": email,
        "phone": phone,
        "skills": skills,
        "experience": experience,
        "summary": summary,
        "location": location,
        "raw_text": text,
    }


# ---------- DB insertion ----------
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def get_or_create_skill(conn, name: str) -> int:
    row = conn.execute("SELECT id FROM skills WHERE name = ?", (name,)).fetchone()
    if row:
        return row["id"]
    cur = conn.execute("INSERT INTO skills (name) VALUES (?)", (name,))
    return cur.lastrowid


def ingest_candidate(data: Dict, recruiter_id: Optional[int] = None, job_id: Optional[int] = None) -> Tuple[int, int]:
    """
    Insert a parsed candidate into the database.

    Returns (user_id, profile_id).
    """
    init_db()
    name = data["name"]
    email = data.get("email") or f"{name.lower().replace(' ', '.')}@imported.local"
    password_hash = hash_password("candidate123")
    initials = "".join([w[0] for w in name.split()[:2]]).upper() if len(name.split()) >= 2 else name[:2].upper()

    with get_db() as conn:
        # Create or fetch user
        existing = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
        if existing:
            user_id = existing["id"]
        else:
            cur = conn.execute(
                "INSERT INTO users (name, email, password_hash, role, avatar_initials, phone, location, verified) "
                "VALUES (?, ?, ?, 'candidate', ?, ?, ?, 1)",
                (name, email, password_hash, initials, data.get("phone"), data.get("location")),
            )
            user_id = cur.lastrowid

        # Create or update profile
        existing_profile = conn.execute(
            "SELECT id FROM candidate_profiles WHERE user_id = ?", (user_id,)
        ).fetchone()
        score = min(95, 60 + len(data.get("skills", [])) * 3)
        if existing_profile:
            pid = existing_profile["id"]
            conn.execute(
                "UPDATE candidate_profiles SET full_name=?, role=?, location=?, experience=?, summary=?, "
                "resume_score=?, ats_score=?, keywords_score=?, experience_match=?, projects_score=?, "
                "education_score=?, achievements_score=?, career_health=? WHERE id=?",
                (
                    name, data.get("role"), data.get("location"), data.get("experience"),
                    data.get("summary"), score, min(100, score + 4), max(0, score - 7),
                    min(100, score - 4), max(0, score - 10), max(0, score - 16),
                    max(0, score - 22), min(100, score + 2), pid,
                ),
            )
        else:
            cur = conn.execute(
                "INSERT INTO candidate_profiles (user_id, full_name, role, location, experience, summary, "
                "resume_score, ats_score, keywords_score, experience_match, projects_score, "
                "education_score, achievements_score, career_health) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    user_id, name, data.get("role"), data.get("location"), data.get("experience"),
                    data.get("summary"), score, min(100, score + 4), max(0, score - 7),
                    min(100, score - 4), max(0, score - 10), max(0, score - 16),
                    max(0, score - 22), min(100, score + 2),
                ),
            )
            pid = cur.lastrowid

        # Insert skills as current
        for s in data.get("skills", []):
            sid = get_or_create_skill(conn, s)
            conn.execute(
                "INSERT OR IGNORE INTO profile_skills (profile_id, skill_id, kind) VALUES (?, ?, 'current')",
                (pid, sid),
            )

        # Add to pipeline if recruiter_id and job_id provided
        if recruiter_id and job_id:
            existing_pipe = conn.execute(
                "SELECT id FROM pipeline WHERE job_id = ? AND candidate_id = ?",
                (job_id, user_id),
            ).fetchone()
            if not existing_pipe:
                # Compute next rank
                rank_row = conn.execute(
                    "SELECT COALESCE(MAX(rank), 0) + 1 AS next_rank FROM pipeline WHERE job_id = ?",
                    (job_id,),
                ).fetchone()
                next_rank = rank_row["next_rank"]
                conn.execute(
                    "INSERT INTO pipeline (recruiter_id, job_id, candidate_id, profile_id, score, rank, top_match, reason, status) "
                    "VALUES (?, ?, ?, ?, ?, ?, 0, ?, 'pending')",
                    (recruiter_id, job_id, user_id, pid, score, next_rank, data.get("summary", "")),
                )
                pipe_id = conn.execute(
                    "SELECT id FROM pipeline WHERE job_id = ? AND candidate_id = ?",
                    (job_id, user_id),
                ).fetchone()["id"]
                for s in data.get("skills", []):
                    sid = get_or_create_skill(conn, s)
                    conn.execute(
                        "INSERT OR IGNORE INTO pipeline_skills (pipeline_id, skill_id, kind) VALUES (?, ?, 'matched')",
                        (pipe_id, sid),
                    )

    print(f"[ingest] {name} -> user_id={user_id}, profile_id={pid}")
    return user_id, pid


def ingest_pdf(pdf_path: str, recruiter_id: Optional[int] = None, job_id: Optional[int] = None) -> Tuple[int, int]:
    """Parse a single PDF and ingest the candidate."""
    data = parse_resume_pdf(pdf_path)
    return ingest_candidate(data, recruiter_id=recruiter_id, job_id=job_id)


def ingest_directory(dir_path: str, recruiter_id: Optional[int] = None, job_id: Optional[int] = None) -> List[Tuple[int, int]]:
    """Ingest all PDFs in a directory."""
    results: List[Tuple[int, int]] = []
    for fname in sorted(os.listdir(dir_path)):
        if fname.lower().endswith(".pdf"):
            pdf_path = os.path.join(dir_path, fname)
            try:
                print(f"[ingest] Processing {fname}...")
                results.append(ingest_pdf(pdf_path, recruiter_id=recruiter_id, job_id=job_id))
            except Exception as e:
                print(f"[ingest] ERROR processing {fname}: {e}")
    return results


def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python pdf_ingest.py <path-to-pdf>           # ingest a single resume PDF")
        print("  python pdf_ingest.py <path-to-folder>        # ingest all PDFs in a folder")
        print()
        print("Optional: --recruiter <id> --job <id>  to also add to a recruiter's pipeline")
        sys.exit(1)

    target = sys.argv[1]
    recruiter_id = None
    job_id = None
    for i, arg in enumerate(sys.argv):
        if arg == "--recruiter" and i + 1 < len(sys.argv):
            recruiter_id = int(sys.argv[i + 1])
        if arg == "--job" and i + 1 < len(sys.argv):
            job_id = int(sys.argv[i + 1])

    if os.path.isfile(target) and target.lower().endswith(".pdf"):
        ingest_pdf(target, recruiter_id=recruiter_id, job_id=job_id)
    elif os.path.isdir(target):
        ingest_directory(target, recruiter_id=recruiter_id, job_id=job_id)
    else:
        print(f"Error: {target} is not a valid PDF file or directory.")
        sys.exit(1)


if __name__ == "__main__":
    main()
