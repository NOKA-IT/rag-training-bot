"""RAG chatbot endpoint."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User
from ..schemas import ChatRequest, ChatResponse
from ..deps import get_current_user
from ..services import rag

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
def chat(payload: ChatRequest,
         db: Session = Depends(get_db),
         current: User = Depends(get_current_user)):
    if not payload.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    try:
        result = rag.answer_question(
            user=current,
            question=payload.question,
            department_id=payload.department_id,
            category_ids=payload.category_ids,
        )
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    return ChatResponse(**result)
