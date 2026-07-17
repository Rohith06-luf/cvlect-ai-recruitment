from typing import Generator

from sqlalchemy import create_engine
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
    from app.models.user import User

    Base.metadata.create_all(bind=engine)
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
