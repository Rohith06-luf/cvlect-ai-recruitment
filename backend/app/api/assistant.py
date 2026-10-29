"""
CVlect AI — Conversational Assistant API Endpoints
Interactive AI chat powered by NVIDIA NIM and grounded RAG context retrieval.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.models import User
from app.schemas.schemas import ChatRequest, ChatResponse
from app.services.auth_service import get_current_user
from app.services.assistant_service import assistant_service
from app.utils import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/assistant", tags=["AI Assistant"])


@router.post("/chat", response_model=ChatResponse)
def chat_with_assistant(
    chat_request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Send a message to the CVlect AI assistant.
    Retrieves authorized resume and job context depending on the user's role.
    """
    logger.info(f"Chat request from user {current_user.id} ({current_user.role})")

    response = assistant_service.chat(
        user_id=current_user.id,
        role=current_user.role,
        message=chat_request.message,
        context=chat_request.context,
        db=db,
    )
    return response
