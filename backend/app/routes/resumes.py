import json
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
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
    job_description: str | None = Form(None),
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
    ai_service = AIService()
    ai_result = ai_service.process_resume(filepath, job_description=job_description)
    
    parsed = ai_result.get("parsed", {})
    features = ai_result.get("features", {})
    fraud = ai_result.get("fraud_report", {})
    bias = ai_result.get("bias_report", {})
    summary = ai_result.get("summary", {})

    resume = Resume(
        candidate_id=candidate.id,
        filename=filename,
        filepath=filepath,
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
    return ResumeResponse(
        success=True,
        message="Resume uploaded",
        data=resume,
        ai_analysis={
            "ats_score": ai_result["ats_score"],
            "match_percentage": ai_result["match_percentage"],
            "summary": summary,
            "features": features,
            "explanation": ai_result["explanation"],
            "fraud_report": fraud,
            "bias_report": bias,
        },
    )


@router.post("/rank", summary="Rank a resume against a job description")
async def rank_resume(payload: dict[str, str], db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> dict[str, object]:
    resume = db.query(Resume).filter(Resume.candidate_id == current_user.id).order_by(Resume.uploaded_at.desc()).first()
    if not resume:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No resume found")

    ai_service = AIService()
    ai_result = ai_service.process_resume(resume.filepath, job_description=payload.get("job_description", ""))
    
    # Save the updated match percentage
    resume.match_percentage = ai_result["match_percentage"]
    db.commit()
    
    return {
        "success": True,
        "message": "Resume ranked",
        "data": {
            "resume_id": resume.id,
            "ats_score": ai_result["ats_score"],
            "match_percentage": ai_result["match_percentage"],
            "features": ai_result["features"],
            "explanation": ai_result["explanation"],
            "fraud_report": ai_result["fraud_report"],
            "bias_report": ai_result["bias_report"],
        },
    }


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
