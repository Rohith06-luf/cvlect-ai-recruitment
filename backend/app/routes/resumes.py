from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.candidate import Candidate
from app.models.resume import Resume
from app.models.user import User
from app.schemas.resume import ResumeOut, ResumeResponse
from app.services.ai_service import AIService
from app.utils.file_handler import FileHandler

router = APIRouter(prefix="/resume", tags=["Resumes"])


@router.post("/upload", response_model=ResumeResponse, summary="Upload a candidate resume")
async def upload_resume(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ResumeResponse:
    FileHandler.validate_upload(file)
    candidate = db.query(Candidate).filter(Candidate.user_id == current_user.id).first()
    if not candidate:
        candidate = Candidate(user_id=current_user.id)
        db.add(candidate)
        db.commit()
        db.refresh(candidate)

    filename, filepath = FileHandler.save_upload(file)
    ai_result = AIService.process_resume(filepath)
    resume = Resume(
        candidate_id=candidate.id,
        filename=filename,
        filepath=filepath,
        ats_score=ai_result["ats_score"],
        match_percentage=ai_result["match_percentage"],
        status="uploaded",
    )
    db.add(resume)
    db.commit()
    db.refresh(resume)
    return ResumeResponse(success=True, message="Resume uploaded", data=resume)


@router.get("", response_model=list[ResumeOut], summary="List resumes")
async def list_resumes(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> list[ResumeOut]:
    candidate = db.query(Candidate).filter(Candidate.user_id == current_user.id).first()
    if not candidate:
        return []
    return db.query(Resume).filter(Resume.candidate_id == candidate.id).all()


@router.get("/{resume_id}", response_model=ResumeResponse, summary="Get resume metadata")
async def get_resume(resume_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> ResumeResponse:
    resume = db.query(Resume).filter(Resume.id == resume_id).first()
    if not resume:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found")
    return ResumeResponse(success=True, message="Resume fetched", data=resume)


@router.delete("/{resume_id}", response_model=ResumeResponse, summary="Delete a resume")
async def delete_resume(resume_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> ResumeResponse:
    resume = db.query(Resume).filter(Resume.id == resume_id).first()
    if not resume:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found")
    db.delete(resume)
    db.commit()
    return ResumeResponse(success=True, message="Resume deleted", data=None)
