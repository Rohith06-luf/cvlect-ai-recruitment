"""
CVlect AI — Database Seed Script
Populates the database with realistic sample candidates, recruiters, resumes, and job postings.
Can be run via: python -m sample_data.seed_db
"""

import json
import os
import sys
from pathlib import Path

# Ensure backend root is on sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.database import SessionLocal, init_db
from app.models.models import User, Resume, ExtractedResumeData, Job
from app.services.auth_service import hash_password
from app.utils import get_logger

logger = get_logger("seed_db")


def load_json_file(filename: str):
    """Load JSON from sample_data directory."""
    current_dir = Path(__file__).resolve().parent
    file_path = current_dir / filename
    if not file_path.exists():
        logger.error(f"Sample data file not found: {file_path}")
        return []
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def seed_database():
    """Seed users, resumes, and jobs into database idempotently."""
    logger.info("Initializing database tables...")
    init_db()

    db = SessionLocal()
    try:
        # ---------------------------------------------------------------------
        # 1. Seed Users
        # ---------------------------------------------------------------------
        logger.info("Seeding sample users...")

        sample_candidates_data = load_json_file("sample_resumes.json")
        sample_jobs_data = load_json_file("sample_jobs.json")

        users_to_create = [
            # Candidates
            {
                "email": "avery.sterling@example.com",
                "password": "Password123!",
                "full_name": "Avery Sterling",
                "role": "candidate",
            },
            {
                "email": "maya.linnea@example.com",
                "password": "Password123!",
                "full_name": "Maya Linnea",
                "role": "candidate",
            },
            {
                "email": "devon.vance@example.com",
                "password": "Password123!",
                "full_name": "Devon Vance",
                "role": "candidate",
            },
            # Recruiters
            {
                "email": "recruiter@example.com",
                "password": "Password123!",
                "full_name": "Sarah Jenkins",
                "role": "recruiter",
            },
            {
                "email": "techrecruiter@example.com",
                "password": "Password123!",
                "full_name": "Marcus Vance",
                "role": "recruiter",
            },
        ]

        created_users = {}
        for u_data in users_to_create:
            existing_user = db.query(User).filter(User.email == u_data["email"]).first()
            if not existing_user:
                new_user = User(
                    email=u_data["email"],
                    password_hash=hash_password(u_data["password"]),
                    full_name=u_data["full_name"],
                    role=u_data["role"],
                    is_active=True,
                )
                db.add(new_user)
                db.flush()
                created_users[u_data["email"]] = new_user
                logger.info(f"Created user: {u_data['email']} ({u_data['role']})")
            else:
                created_users[u_data["email"]] = existing_user
                logger.info(f"User already exists: {u_data['email']}")

        # ---------------------------------------------------------------------
        # 2. Seed Resumes
        # ---------------------------------------------------------------------
        logger.info("Seeding sample resumes...")
        candidate_emails = [
            "avery.sterling@example.com",
            "maya.linnea@example.com",
            "devon.vance@example.com",
        ]

        # Try to import embedding functions if available
        generate_embedding = None
        embedding_to_bytes = None
        try:
            from app.services.embedding_service import generate_embedding as gen_emb, embedding_to_bytes as emb_bytes
            generate_embedding = gen_emb
            embedding_to_bytes = emb_bytes
        except Exception:
            logger.debug("Embedding service optional during seeding.")

        for i, resume_data in enumerate(sample_candidates_data):
            if i >= len(candidate_emails):
                break
            cand_user = created_users.get(candidate_emails[i])
            if not cand_user:
                continue

            existing_resume = db.query(Resume).filter(Resume.user_id == cand_user.id).first()
            if not existing_resume:
                filename = f"{cand_user.full_name.lower().replace(' ', '_')}_resume.pdf"
                resume = Resume(
                    user_id=cand_user.id,
                    filename=filename,
                    file_path=f"./uploads/{filename}",
                    file_type="pdf",
                    file_size=1024 * 150,
                    is_analyzed=True,
                )
                db.add(resume)
                db.flush()

                # Build raw text representation
                raw_text_parts = [
                    f"Name: {resume_data['contact_info'].get('name')}",
                    f"Email: {resume_data['contact_info'].get('email')}",
                    f"Summary: {resume_data.get('summary')}",
                    f"Skills: {', '.join(resume_data.get('skills', []))}",
                ]
                for exp in resume_data.get("experience", []):
                    raw_text_parts.append(
                        f"{exp.get('title')} at {exp.get('company')} ({exp.get('start_date')}-{exp.get('end_date')}): {exp.get('description')}"
                    )
                for edu in resume_data.get("education", []):
                    raw_text_parts.append(
                        f"{edu.get('degree')} in {edu.get('field')} from {edu.get('institution')} ({edu.get('year')})"
                    )
                raw_text = "\n\n".join(raw_text_parts)

                # Compute embedding if model is available
                emb_bytes_data = None
                if generate_embedding and embedding_to_bytes:
                    emb = generate_embedding(raw_text[:2000])
                    if emb is not None:
                        emb_bytes_data = embedding_to_bytes(emb)

                # Estimate total years from experience
                total_years = 0.0
                for exp in resume_data.get("experience", []):
                    s = exp.get("start_date", "")
                    e = exp.get("end_date", "")
                    if s and (e == "Present" or e.isdigit()):
                        total_years += 2.5
                total_years = max(total_years, 2.0)

                extracted = ExtractedResumeData(
                    resume_id=resume.id,
                    raw_text=raw_text,
                    contact_info=resume_data.get("contact_info"),
                    skills=resume_data.get("skills"),
                    technical_skills=resume_data.get("technical_skills"),
                    soft_skills=resume_data.get("soft_skills"),
                    education=resume_data.get("education"),
                    experience=resume_data.get("experience"),
                    certifications=resume_data.get("certifications"),
                    projects=resume_data.get("projects"),
                    keywords=resume_data.get("keywords"),
                    domain_knowledge=["cloud", "saas", "fintech"],
                    summary=resume_data.get("summary"),
                    total_experience_years=total_years,
                    confidence_scores={
                        "contact_info": 0.95,
                        "skills": 0.90,
                        "education": 0.88,
                        "experience": 0.85,
                    },
                    missing_fields=[],
                    quality_score=92.0,
                    quality_suggestions=["Profile is comprehensive and well structured."],
                    embedding=emb_bytes_data,
                )
                db.add(extracted)
                logger.info(f"Created resume and extracted data for: {cand_user.email}")
            else:
                logger.info(f"Resume already exists for: {cand_user.email}")

        # ---------------------------------------------------------------------
        # 3. Seed Jobs
        # ---------------------------------------------------------------------
        logger.info("Seeding sample jobs...")
        recruiter = created_users.get("recruiter@example.com")
        if recruiter:
            for job_data in sample_jobs_data:
                existing_job = db.query(Job).filter(
                    Job.recruiter_id == recruiter.id,
                    Job.title == job_data["title"],
                ).first()
                if not existing_job:
                    # Compute embedding if model is available
                    job_emb_bytes = None
                    if generate_embedding and embedding_to_bytes:
                        job_text = f"{job_data['title']} {job_data['description']} {' '.join(job_data.get('required_skills', []))}"
                        j_emb = generate_embedding(job_text[:2000])
                        if j_emb is not None:
                            job_emb_bytes = embedding_to_bytes(j_emb)

                    job = Job(
                        recruiter_id=recruiter.id,
                        title=job_data["title"],
                        company=job_data["company"],
                        description=job_data["description"],
                        location=job_data.get("location"),
                        work_mode=job_data.get("work_mode", "onsite"),
                        experience_min=job_data.get("experience_min", 0),
                        experience_max=job_data.get("experience_max", 99),
                        salary_min=110000,
                        salary_max=165000,
                        required_skills=job_data.get("required_skills"),
                        preferred_skills=job_data.get("preferred_skills"),
                        education_requirements=job_data.get("education_requirements"),
                        certifications=[],
                        responsibilities=job_data.get("responsibilities"),
                        technologies=job_data.get("technologies"),
                        seniority=job_data.get("seniority"),
                        category=job_data.get("category"),
                        status="active",
                        embedding=job_emb_bytes,
                    )
                    db.add(job)
                    logger.info(f"Created job: '{job_data['title']}' at '{job_data['company']}'")
                else:
                    logger.info(f"Job already exists: '{job_data['title']}'")

        db.commit()
        logger.info("Database seeding completed successfully!")
    except Exception as e:
        db.rollback()
        logger.error(f"Database seeding failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
