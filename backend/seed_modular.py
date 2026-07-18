import json
import sys
import shutil
from pathlib import Path
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine, Base
from app.core.security import create_password_hash
from app.models.user import User
from app.models.candidate import Candidate
from app.models.job import Job
from app.models.resume import Resume
from app.models.application import Application
from app.services.ai_service import AIService

def seed():
    # Make sure tables exist
    Base.metadata.create_all(bind=engine)

    db: Session = SessionLocal()
    try:
        # Clear existing data to avoid conflicts on reseeding
        db.query(Application).delete()
        db.query(Resume).delete()
        db.query(Job).delete()
        db.query(Candidate).delete()
        db.query(User).delete()
        db.commit()
        print("[seed_modular] Cleared existing tables.")

        # ---------- USERS ----------
        # Recruiter: Alex Reed
        alex = User(
            name="Alex Reed",
            email="alex.reed@cvlect.com",
            hashed_password=create_password_hash("recruiter123"),
            role="Recruiter"
        )
        db.add(alex)

        # Candidate: Priya Sharma
        priya = User(
            name="Priya Sharma",
            email="priya.sharma@example.com",
            hashed_password=create_password_hash("candidate123"),
            role="Candidate"
        )
        db.add(priya)

        # Candidate: Marcus Weiss
        marcus = User(
            name="Marcus Weiss",
            email="marcus.weiss@example.com",
            hashed_password=create_password_hash("candidate123"),
            role="Candidate"
        )
        db.add(marcus)

        # Candidate: Amelia Chen
        amelia = User(
            name="Amelia Chen",
            email="amelia.chen@example.com",
            hashed_password=create_password_hash("candidate123"),
            role="Candidate"
        )
        db.add(amelia)

        # Admin User
        admin = db.query(User).filter(User.email == "admin@example.com").first()
        if not admin:
            admin = User(
                name="Admin User",
                email="admin@example.com",
                hashed_password=create_password_hash("admin123"),
                role="Admin"
            )
            db.add(admin)
        else:
            admin.name = "Admin User"
            admin.hashed_password = create_password_hash("admin123")
            admin.role = "Admin"

        db.commit()
        print("[seed_modular] Users created.")

        # Refresh to get IDs
        db.refresh(alex)
        db.refresh(priya)
        db.refresh(marcus)
        db.refresh(amelia)

        # ---------- CANDIDATES ----------
        c_priya = Candidate(
            user_id=priya.id,
            phone="+91 98765 43210",
            experience="6 years",
            education="B.Tech Computer Science",
            skills="React, TypeScript, Design Systems, Accessibility",
            location="Bengaluru, IN"
        )
        db.add(c_priya)

        c_marcus = Candidate(
            user_id=marcus.id,
            phone="+49 30 123456",
            experience="4 years",
            education="B.S. Computer Science",
            skills="React, TypeScript, Performance",
            location="Berlin, DE"
        )
        db.add(c_marcus)

        c_amelia = Candidate(
            user_id=amelia.id,
            phone="+1 (416) 555-0199",
            experience="5 years",
            education="Master of Computer Science",
            skills="React, Node.js, TypeScript",
            location="Toronto, CA"
        )
        db.add(c_amelia)

        db.commit()
        print("[seed_modular] Candidate profiles created.")

        # Refresh to get Candidate IDs
        db.refresh(c_priya)
        db.refresh(c_marcus)
        db.refresh(c_amelia)

        # ---------- JOBS ----------
        job_cvlect = Job(
            recruiter_id=alex.id,
            title="Senior Frontend Engineer",
            description="Senior Frontend Engineer — React, TypeScript, design systems, accessibility. Ship product surfaces with a small, senior team.",
            required_skills="React, TypeScript, Design Systems, Accessibility",
            experience_required="5 years"
        )
        db.add(job_cvlect)

        job_linear = Job(
            recruiter_id=alex.id,
            title="Senior Product Engineer",
            description="Senior product engineer role with focus on Linear UI and design system interaction.",
            required_skills="React, TypeScript",
            experience_required="5 years"
        )
        db.add(job_linear)

        job_vercel = Job(
            recruiter_id=alex.id,
            title="Frontend Platform Engineer",
            description="Frontend platform role focused on Next.js, deployment pipelines, and UI framework optimization.",
            required_skills="React, TypeScript",
            experience_required="4 years"
        )
        db.add(job_vercel)

        job_stripe = Job(
            recruiter_id=alex.id,
            title="UI Engineer, Dashboard",
            description="UI engineer for Stripe dashboard surfaces. Requires deep knowledge of charts, animations, and dashboard grids.",
            required_skills="React, TypeScript",
            experience_required="3 years"
        )
        db.add(job_stripe)

        job_figma = Job(
            recruiter_id=alex.id,
            title="Product Engineer",
            description="Product engineer role developing state-of-the-art vector manipulation tools and canvas elements.",
            required_skills="React",
            experience_required="4 years"
        )
        db.add(job_figma)

        job_github = Job(
            recruiter_id=alex.id,
            title="Frontend Engineer",
            description="Frontend engineer role working on repository collaboration features and user profiles.",
            required_skills="React, TypeScript",
            experience_required="3 years"
        )
        db.add(job_github)

        db.commit()
        print("[seed_modular] Jobs created.")

        # Refresh to get Job IDs
        db.refresh(job_cvlect)
        db.refresh(job_linear)
        db.refresh(job_vercel)
        db.refresh(job_stripe)
        db.refresh(job_figma)
        db.refresh(job_github)

        # ---------- RESUMES ----------
        r_priya = Resume(
            candidate_id=c_priya.id,
            filename="Priya_Sharma_Resume.pdf",
            filepath="app/uploads/resumes/priya_sharma.pdf",
            ats_score=92,
            match_percentage=94,
            status="uploaded",
            raw_text="Priya Sharma, Senior Frontend Engineer. Skills: React, TypeScript, Design Systems, Accessibility. 6 years experience. B.Tech Computer Science.",
            skills_list=json.dumps(["React", "TypeScript", "Design Systems", "Accessibility"]),
            experience_years=6,
            parsed_education=json.dumps(["B.Tech Computer Science"]),
            parsed_projects=json.dumps(["SmartResume AI", "DataPipeline"]),
            parsed_certifications=json.dumps(["AWS Certified Solutions Architect"]),
            summary="Product-focused engineer with deep React + design systems experience across two YC startups.",
            fraud_score=0.05,
            fraud_warnings=json.dumps([]),
            bias_score=0.1,
            bias_flagged_terms=json.dumps(["she", "her"])
        )
        db.add(r_priya)

        r_marcus = Resume(
            candidate_id=c_marcus.id,
            filename="Marcus_Weiss_Resume.pdf",
            filepath="app/uploads/resumes/marcus_weiss.pdf",
            ats_score=88,
            match_percentage=88,
            status="uploaded",
            raw_text="Marcus Weiss, Frontend Engineer. Skills: React, TypeScript, Performance. 4 years experience. B.S. Computer Science.",
            skills_list=json.dumps(["React", "TypeScript", "Performance"]),
            experience_years=4,
            parsed_education=json.dumps(["B.S. Computer Science"]),
            parsed_projects=json.dumps(["Performance Optimizer"]),
            parsed_certifications=json.dumps([]),
            summary="Performance-obsessed engineer, contributed to core web vitals improvements at a fintech.",
            fraud_score=0.05,
            fraud_warnings=json.dumps([]),
            bias_score=0.15,
            bias_flagged_terms=json.dumps(["he", "his"])
        )
        db.add(r_marcus)

        r_amelia = Resume(
            candidate_id=c_amelia.id,
            filename="Amelia_Chen_Resume.pdf",
            filepath="app/uploads/resumes/amelia_chen.pdf",
            ats_score=82,
            match_percentage=82,
            status="uploaded",
            raw_text="Amelia Chen, Full-stack Engineer. Skills: React, Node.js, TypeScript. 5 years experience. Master of Computer Science.",
            skills_list=json.dumps(["React", "Node.js", "TypeScript"]),
            experience_years=5,
            parsed_education=json.dumps(["Master of Computer Science"]),
            parsed_projects=json.dumps(["Platform API"]),
            parsed_certifications=json.dumps([]),
            summary="Full-stack engineer with Node + React, led a small platform team of three.",
            fraud_score=0.08,
            fraud_warnings=json.dumps([]),
            bias_score=0.0,
            bias_flagged_terms=json.dumps([])
        )
        db.add(r_amelia)

        db.commit()
        print("[seed_modular] Resumes created.")

        # ---------- APPLICATIONS & PIPELINE ----------
        # Priya applied to the main job
        app_priya_main = Application(
            candidate_id=c_priya.id,
            job_id=job_cvlect.id,
            status="applied",
            score=94,
            rank=1,
            top_match=True,
            reason="Strong React, TypeScript, design system authorship; ships accessible, tested UI.",
            matched_skills=json.dumps(["React", "TypeScript", "Design Systems", "Accessibility"]),
            missing_skills=json.dumps(["GraphQL"]),
            shap_values=json.dumps({
                "semantic_similarity": 0.4,
                "experience_years": 0.2,
                "education_score": 0.1,
                "skill_overlap": 0.15,
                "projects_score": 0.08,
                "certifications_score": 0.07
            }),
            semantic_similarity=0.85,
            recommended_courses=json.dumps(["GraphQL Fundamentals (Udemy)", "Advanced Web Accessibility"]),
            recommended_certs=json.dumps(["AWS Certified Developer - Associate"])
        )
        db.add(app_priya_main)

        # Marcus applied to the main job
        app_marcus_main = Application(
            candidate_id=c_marcus.id,
            job_id=job_cvlect.id,
            status="applied",
            score=88,
            rank=2,
            top_match=False,
            reason="Solid React, strong performance work, modest testing coverage on prior repos.",
            matched_skills=json.dumps(["React", "TypeScript"]),
            missing_skills=json.dumps(["Design Systems", "Accessibility", "GraphQL"]),
            shap_values=json.dumps({
                "semantic_similarity": 0.35,
                "experience_years": 0.15,
                "education_score": 0.08,
                "skill_overlap": 0.12,
                "projects_score": 0.06,
                "certifications_score": 0.05
            }),
            semantic_similarity=0.78,
            recommended_courses=json.dumps(["System Design & Microservices Architecture"]),
            recommended_certs=json.dumps(["AWS Certified Cloud Practitioner"])
        )
        db.add(app_marcus_main)

        # Amelia applied to the main job
        app_amelia_main = Application(
            candidate_id=c_amelia.id,
            job_id=job_cvlect.id,
            status="applied",
            score=82,
            rank=3,
            top_match=False,
            reason="Good breadth; frontend depth is lighter than the top match.",
            matched_skills=json.dumps(["React", "TypeScript"]),
            missing_skills=json.dumps(["Design Systems", "Accessibility", "GraphQL"]),
            shap_values=json.dumps({
                "semantic_similarity": 0.32,
                "experience_years": 0.18,
                "education_score": 0.1,
                "skill_overlap": 0.1,
                "projects_score": 0.05,
                "certifications_score": 0.04
            }),
            semantic_similarity=0.72,
            recommended_courses=json.dumps(["System Design & Microservices Architecture"]),
            recommended_certs=json.dumps(["AWS Certified Cloud Practitioner"])
        )
        db.add(app_amelia_main)

        # Other mock applications for Priya
        db.add(Application(candidate_id=c_priya.id, job_id=job_linear.id, status="applied", score=96))
        db.add(Application(candidate_id=c_priya.id, job_id=job_vercel.id, status="interview", score=91))
        db.add(Application(candidate_id=c_priya.id, job_id=job_stripe.id, status="applied", score=87))
        db.add(Application(candidate_id=c_priya.id, job_id=job_figma.id, status="applied", score=82))
        db.add(Application(candidate_id=c_priya.id, job_id=job_github.id, status="rejected", score=65))

        db.commit()
        print("[seed_modular] Applications and pipeline entries seeded.")

        # Ingest actual resumes from the Resume folder
        try:
            resume_dir = Path(__file__).resolve().parent.parent / "Resume"
            upload_dir = Path(__file__).resolve().parent / "app" / "uploads" / "resumes"
            upload_dir.mkdir(parents=True, exist_ok=True)

            if resume_dir.exists():
                ai_service = AIService()
                files = list(resume_dir.glob("*.pdf"))
                print(f"[seed_modular] Found {len(files)} actual resumes in Resume folder. Importing...")
                
                for idx, file_path in enumerate(files):
                    dest_filename = f"seeded_{file_path.name}"
                    dest_path = upload_dir / dest_filename
                    shutil.copy(file_path, dest_path)

                    try:
                        print(f"[seed_modular] Processing {file_path.name}...")
                        ai_result = ai_service.process_resume(str(dest_path))
                        parsed = ai_result.get("parsed", {})
                        
                        cand_name = parsed.get("name") or file_path.stem.replace("_", " ").replace("-", " ")
                        email_name = "".join(c for c in cand_name.lower() if c.isalnum() or c == " ").replace(" ", ".")
                        email = f"{email_name}@example.com"
                        
                        # Handle email collision
                        existing = db.query(User).filter(User.email == email).first()
                        if existing:
                            email = f"{email_name}{idx}@example.com"

                        user = User(
                            name=cand_name,
                            email=email,
                            hashed_password=create_password_hash("candidate123"),
                            role="Candidate"
                        )
                        db.add(user)
                        db.commit()
                        db.refresh(user)

                        candidate = Candidate(
                            user_id=user.id,
                            experience=f"{parsed.get('experience_years', 0)} years",
                            skills=", ".join(parsed.get("skills", [])),
                            education=", ".join(parsed.get("education", [])) if parsed.get("education") else None,
                            location=parsed.get("location")
                        )
                        db.add(candidate)
                        db.commit()
                        db.refresh(candidate)

                        fraud = ai_result.get("fraud_report", {})
                        bias = ai_result.get("bias_report", {})
                        summary = ai_result.get("summary", {})
                        
                        resume = Resume(
                            candidate_id=candidate.id,
                            filename=dest_filename,
                            filepath=f"app/uploads/resumes/{dest_filename}",
                            ats_score=ai_result["ats_score"],
                            match_percentage=ai_result["match_percentage"],
                            status="uploaded",
                            raw_text=ai_result.get("text"),
                            skills_list=json.dumps(parsed.get("skills", [])),
                            experience_years=parsed.get("experience_years", 0),
                            parsed_education=json.dumps(parsed.get("education", [])),
                            parsed_projects=json.dumps(parsed.get("projects", [])),
                            parsed_certifications=json.dumps(parsed.get("certifications", [])),
                            summary=summary.get("summary"),
                            fraud_score=fraud.get("risk_score"),
                            fraud_warnings=json.dumps(fraud.get("warnings", [])),
                            bias_score=bias.get("bias_score"),
                            bias_flagged_terms=json.dumps(bias.get("flagged_terms", []))
                        )
                        db.add(resume)
                        db.commit()
                        db.refresh(resume)

                        # Match against main job (Senior Frontend Engineer)
                        app_result = ai_service.score_candidate(ai_result.get("text", "") or "", job_cvlect.description)
                        skills_set = {s.lower() for s in parsed.get("skills", [])}
                        matched_s = list(skills_set & {"react", "typescript", "design systems", "accessibility"})
                        missing_s = list({"react", "typescript", "design systems", "accessibility"} - skills_set)

                        app = Application(
                            candidate_id=candidate.id,
                            job_id=job_cvlect.id,
                            status="applied",
                            score=app_result.get("match_percentage", 80),
                            reason=app_result.get("summary", {}).get("summary", "Resume matched from seed import."),
                            matched_skills=json.dumps(matched_s),
                            missing_skills=json.dumps(missing_s),
                            shap_values=json.dumps(app_result.get("explanation", {}).get("shap_values", {})),
                            semantic_similarity=float(app_result.get("features", {}).get("semantic_similarity", 0.0))
                        )
                        db.add(app)
                        db.commit()
                        print(f"[seed_modular] Ingested candidate {cand_name} ({email}) from {file_path.name}")
                    except Exception as child_ex:
                        db.rollback()
                        print(f"[seed_modular] Failed to ingest resume {file_path.name}: {child_ex}")
            else:
                print(f"[seed_modular] Resume directory not found at {resume_dir}")
        except Exception as ex:
            print(f"[seed_modular] Error during folder resumes ingestion: {ex}")

        print("[seed_modular] Database seeded successfully.")
        print("       Recruiter login:  alex.reed@cvlect.com / recruiter123")
        print("       Candidate login:  priya.sharma@example.com / candidate123")

    except Exception as e:
        db.rollback()
        print(f"[seed_modular] Error occurred: {e}", file=sys.stderr)
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    seed()
