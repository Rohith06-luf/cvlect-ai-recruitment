from datetime import datetime, timezone
from uuid import uuid4
from sqlalchemy import DateTime, ForeignKey, String, Text, Float, Boolean, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

class Application(Base):
    __tablename__ = "applications"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: str(uuid4()))
    candidate_id: Mapped[str] = mapped_column(String(64), ForeignKey("candidates.id"), nullable=False, index=True)
    job_id: Mapped[str] = mapped_column(String(64), ForeignKey("jobs.id"), nullable=False, index=True)
    
    status: Mapped[str] = mapped_column(String(50), default="applied")  # applied, shortlisted, rejected
    score: Mapped[int] = mapped_column(Integer, default=0)              # Overall rank/match score (0-100)
    rank: Mapped[int | None] = mapped_column(Integer, nullable=True)     # Assigned relative rank in pipeline
    top_match: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Explainable AI & Matching Outputs
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)      # AI Summary explanation
    matched_skills: Mapped[str | None] = mapped_column(Text, nullable=True) # JSON list
    missing_skills: Mapped[str | None] = mapped_column(Text, nullable=True) # JSON list
    
    # SHAP & Features
    shap_values: Mapped[str | None] = mapped_column(Text, nullable=True)   # JSON mapping of weights
    semantic_similarity: Mapped[float] = mapped_column(Float, default=0.0)
    
    # Recommendations
    recommended_courses: Mapped[str | None] = mapped_column(Text, nullable=True) # JSON list
    recommended_certs: Mapped[str | None] = mapped_column(Text, nullable=True)   # JSON list
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    candidate = relationship("Candidate")
    job = relationship("Job")
