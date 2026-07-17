from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, require_roles
from app.models.candidate import Candidate
from app.models.user import User
from app.schemas.candidate import CandidateCreate, CandidateOut, CandidateResponse, CandidateUpdate

router = APIRouter(prefix="/candidates", tags=["Candidates"])


@router.get("", response_model=list[CandidateOut], summary="List candidates")
async def list_candidates(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("Admin", "Recruiter", "Candidate")),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    search: str | None = None,
):
    query = db.query(Candidate)
    if search:
        query = query.filter(Candidate.skills.ilike(f"%{search}%"))
    return query.offset(skip).limit(limit).all()


@router.get("/{candidate_id}", response_model=CandidateResponse, summary="Get candidate by id")
async def get_candidate(candidate_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> CandidateResponse:
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate not found")
    return CandidateResponse(success=True, message="Candidate fetched", data=candidate)


@router.post("", response_model=CandidateResponse, summary="Create candidate profile")
async def create_candidate(payload: CandidateCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> CandidateResponse:
    candidate = Candidate(user_id=current_user.id, **payload.model_dump())
    db.add(candidate)
    db.commit()
    db.refresh(candidate)
    return CandidateResponse(success=True, message="Candidate created", data=candidate)


@router.put("/{candidate_id}", response_model=CandidateResponse, summary="Update candidate profile")
async def update_candidate(candidate_id: str, payload: CandidateUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> CandidateResponse:
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate not found")
    if candidate.user_id != current_user.id and current_user.role != "Admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")

    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(candidate, key, value)
    db.commit()
    db.refresh(candidate)
    return CandidateResponse(success=True, message="Candidate updated", data=candidate)


@router.delete("/{candidate_id}", response_model=CandidateResponse, summary="Delete candidate profile")
async def delete_candidate(candidate_id: str, db: Session = Depends(get_db), current_user: User = Depends(require_roles("Admin"))) -> CandidateResponse:
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate not found")
    db.delete(candidate)
    db.commit()
    return CandidateResponse(success=True, message="Candidate deleted", data=None)
