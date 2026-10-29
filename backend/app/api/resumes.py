"""
CVlect AI — Resumes API Endpoints
Upload, analysis, detail inspection, and parsed data retrieval.
"""

import os
import uuid
import shutil
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.models import Resume, ExtractedResumeData, User, Job, Application
from app.schemas.schemas import ResumeResponse, ResumeDetailResponse
from app.services.auth_service import get_current_user, require_candidate
from app.services.resume_parser import (
    extract_text_from_pdf,
    extract_text_from_docx,
    parse_resume,
)
from app.services.embedding_service import generate_embedding, embedding_to_bytes
from app.services.llm_provider import llm_provider
from app.utils import get_logger, safe_filename

logger = get_logger(__name__)

router = APIRouter(prefix="/api/resumes", tags=["Resumes"])


@router.post("/upload", response_model=ResumeResponse, status_code=status.HTTP_201_CREATED)
async def upload_resume(
    file: UploadFile = File(...),
    current_user: User = Depends(require_candidate),
    db: Session = Depends(get_db),
):
    """
    Upload a resume file (PDF or DOCX format).
    Validates file extension, size limit, and persists file securely.
    """
    original_filename = file.filename or "resume.pdf"
    ext = original_filename.split(".")[-1].lower() if "." in original_filename else ""

    if ext not in ["pdf", "docx"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file format. Please upload a PDF or DOCX file.",
        )

    # Sanitize and create unique file path
    clean_name = safe_filename(original_filename)
    unique_name = f"{uuid.uuid4().hex}_{clean_name}"
    save_path = os.path.join(settings.upload_dir, unique_name)

    # Read and validate size
    try:
        content = await file.read()
        file_size = len(content)

        if file_size > settings.max_upload_bytes:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File exceeds maximum allowed size of {settings.max_upload_size_mb} MB.",
            )

        with open(save_path, "wb") as f:
            f.write(content)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to save uploaded file: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not save file to disk.",
        )

    # Create Resume DB record
    resume = Resume(
        user_id=current_user.id,
        filename=original_filename,
        file_path=save_path,
        file_type=ext,
        file_size=file_size,
        is_analyzed=False,
    )
    db.add(resume)
    db.commit()
    db.refresh(resume)

    logger.info(f"Resume {resume.id} uploaded by candidate {current_user.id}")
    return ResumeResponse.model_validate(resume)


@router.get("", response_model=list[ResumeResponse])
@router.get("/", response_model=list[ResumeResponse], include_in_schema=False)
def list_resumes(
    current_user: User = Depends(require_candidate),
    db: Session = Depends(get_db),
):
    """
    List all uploaded resumes belonging to the authenticated candidate.
    """
    resumes = (
        db.query(Resume)
        .filter(Resume.user_id == current_user.id)
        .order_by(Resume.created_at.desc())
        .all()
    )
    return [ResumeResponse.model_validate(r) for r in resumes]


@router.get("/{resume_id}", response_model=ResumeDetailResponse)
def get_resume_detail(
    resume_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Retrieve full resume details including extracted structured data.
    Candidates can only view their own resumes.
    Recruiters can only view resumes of candidates who have applied to one of their jobs.
    """
    resume = db.query(Resume).filter(Resume.id == resume_id).first()
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found.",
        )

    # Permission check
    if current_user.role == "candidate":
        if resume.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to view this resume.",
            )
    elif current_user.role == "recruiter":
        # Check if candidate applied to any job owned by this recruiter
        has_applied = (
            db.query(Application)
            .join(Job, Application.job_id == Job.id)
            .filter(Application.resume_id == resume_id, Job.recruiter_id == current_user.id)
            .first()
        )
        if not has_applied:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only access resumes of candidates who have applied to your job postings.",
            )

    return ResumeDetailResponse.model_validate(resume)


@router.post("/{resume_id}/analyze", response_model=ResumeDetailResponse)
def analyze_resume(
    resume_id: int,
    current_user: User = Depends(require_candidate),
    db: Session = Depends(get_db),
):
    """
    Run complete extraction and parsing pipeline on candidate's uploaded resume:
    Extract text, detect skills and education, calculate experience, generate dense embeddings.
    """
    resume = (
        db.query(Resume)
        .filter(Resume.id == resume_id, Resume.user_id == current_user.id)
        .first()
    )
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found.",
        )

    if not os.path.exists(resume.file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume source file is missing from storage.",
        )

    # 1. Document Extraction
    try:
        if resume.file_type == "pdf":
            raw_text = extract_text_from_pdf(resume.file_path)
        elif resume.file_type == "docx":
            raw_text = extract_text_from_docx(resume.file_path)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type: {resume.file_type}",
            )
    except Exception as e:
        logger.error(f"Text extraction failed for resume {resume_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to extract text from document.",
        )

    # 2. Structured Information Extraction
    parsed = parse_resume(raw_text)

    # 3. Dense Embedding Generation
    embedding_arr = generate_embedding(raw_text[:2500])
    emb_bytes = embedding_to_bytes(embedding_arr)

    # 4. Optional AI Executive Summary
    summary = None
    if llm_provider.is_available:
        summary = llm_provider.generate_resume_summary(parsed)

    # 5. Persist ExtractedResumeData
    extracted = (
        db.query(ExtractedResumeData)
        .filter(ExtractedResumeData.resume_id == resume.id)
        .first()
    )

    if not extracted:
        extracted = ExtractedResumeData(
            resume_id=resume.id,
            raw_text=raw_text,
            contact_info=parsed.get("contact_info"),
            skills=parsed.get("skills"),
            technical_skills=parsed.get("technical_skills"),
            soft_skills=parsed.get("soft_skills"),
            education=parsed.get("education"),
            experience=parsed.get("experience"),
            certifications=parsed.get("certifications"),
            projects=parsed.get("projects"),
            keywords=parsed.get("keywords"),
            domain_knowledge=parsed.get("domain_knowledge"),
            summary=summary,
            total_experience_years=parsed.get("total_experience_years", 0.0),
            confidence_scores=parsed.get("confidence_scores"),
            missing_fields=parsed.get("missing_fields"),
            quality_score=parsed.get("quality_score", 0.0),
            quality_suggestions=parsed.get("quality_suggestions"),
            embedding=emb_bytes,
        )
        db.add(extracted)
    else:
        extracted.raw_text = raw_text
        extracted.contact_info = parsed.get("contact_info")
        extracted.skills = parsed.get("skills")
        extracted.technical_skills = parsed.get("technical_skills")
        extracted.soft_skills = parsed.get("soft_skills")
        extracted.education = parsed.get("education")
        extracted.experience = parsed.get("experience")
        extracted.certifications = parsed.get("certifications")
        extracted.projects = parsed.get("projects")
        extracted.keywords = parsed.get("keywords")
        extracted.domain_knowledge = parsed.get("domain_knowledge")
        extracted.summary = summary or extracted.summary
        extracted.total_experience_years = parsed.get("total_experience_years", 0.0)
        extracted.confidence_scores = parsed.get("confidence_scores")
        extracted.missing_fields = parsed.get("missing_fields")
        extracted.quality_score = parsed.get("quality_score", 0.0)
        extracted.quality_suggestions = parsed.get("quality_suggestions")
        extracted.embedding = emb_bytes

    resume.is_analyzed = True
    db.commit()
    db.refresh(resume)

    logger.info(f"Resume {resume.id} successfully analyzed.")
    return ResumeDetailResponse.model_validate(resume)
