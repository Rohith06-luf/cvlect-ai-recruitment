from typing import Generator

from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings

connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(settings.DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    from app.core.security import create_password_hash
    from app.models.candidate import Candidate  # noqa: F401
    from app.models.job import Job  # noqa: F401
    from app.models.resume import Resume  # noqa: F401
    from app.models.application import Application  # noqa: F401
    from app.models.user import User

    Base.metadata.create_all(bind=engine)
    
    # Self-healing migrations: add missing columns for evolved profile and resume data
    inspector = inspect(engine)
    if inspector.has_table("resumes"):
        existing_cols = {col["name"] for col in inspector.get_columns("resumes")}
        new_cols = {
            "raw_text": "TEXT",
            "skills_list": "TEXT",
            "experience_years": "INTEGER",
            "parsed_education": "TEXT",
            "parsed_projects": "TEXT",
            "parsed_certifications": "TEXT",
            "summary": "TEXT",
            "fraud_score": "FLOAT",
            "fraud_warnings": "TEXT",
            "bias_score": "FLOAT",
            "bias_flagged_terms": "TEXT"
        }

        with engine.begin() as conn:
            for col_name, col_type in new_cols.items():
                if col_name not in existing_cols:
                    try:
                        conn.execute(text(f"ALTER TABLE resumes ADD COLUMN {col_name} {col_type}"))
                        print(f"Added column {col_name} ({col_type}) to resumes table.")
                    except Exception as e:
                        print(f"Error adding column {col_name}: {e}")

    if inspector.has_table("users"):
        existing_user_cols = {col["name"] for col in inspector.get_columns("users")}
        user_cols = {
            "phone": "VARCHAR(30)",
            "location": "VARCHAR(200)",
            "company": "VARCHAR(200)",
            "job_title": "VARCHAR(200)",
            "team": "VARCHAR(200)",
            "about": "TEXT",
        }
        with engine.begin() as conn:
            for col_name, col_type in user_cols.items():
                if col_name not in existing_user_cols:
                    try:
                        conn.execute(text(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}"))
                        print(f"Added column {col_name} ({col_type}) to users table.")
                    except Exception as e:
                        print(f"Error adding column {col_name}: {e}")

    if inspector.has_table("candidates"):
        existing_candidate_cols = {col["name"] for col in inspector.get_columns("candidates")}
        candidate_cols = {"summary": "TEXT"}
        with engine.begin() as conn:
            for col_name, col_type in candidate_cols.items():
                if col_name not in existing_candidate_cols:
                    try:
                        conn.execute(text(f"ALTER TABLE candidates ADD COLUMN {col_name} {col_type}"))
                        print(f"Added column {col_name} ({col_type}) to candidates table.")
                    except Exception as e:
                        print(f"Error adding column {col_name}: {e}")

    with SessionLocal() as db:
        admin_email = "admin@example.com"
        existing_admin = db.query(User).filter(User.email == admin_email).first()
        if not existing_admin:
            admin = User(
                name="Admin User",
                email=admin_email,
                hashed_password=create_password_hash("admin123"),
                role="Admin",
            )
            db.add(admin)
            db.commit()
