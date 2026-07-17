from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, String, Text, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Resume(Base):
    __tablename__ = "resumes"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: str(uuid4()))
    candidate_id: Mapped[str] = mapped_column(String(64), ForeignKey("candidates.id"), nullable=False, index=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    filepath: Mapped[str] = mapped_column(String(500), nullable=False)
    ats_score: Mapped[int | None] = mapped_column(nullable=True)
    match_percentage: Mapped[int | None] = mapped_column(nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="uploaded")
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # AI Parsing & Extraction Columns
    raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    skills_list: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON-serialized or comma-separated list
    experience_years: Mapped[int | None] = mapped_column(nullable=True)
    parsed_education: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON-serialized list
    parsed_projects: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON-serialized list
    parsed_certifications: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON-serialized list
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Fraud & Bias Audit Reports
    fraud_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    fraud_warnings: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON-serialized list
    bias_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    bias_flagged_terms: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON-serialized list

    candidate = relationship("Candidate", back_populates="resumes")
