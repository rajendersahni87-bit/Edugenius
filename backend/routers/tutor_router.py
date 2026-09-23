import json as json_lib
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
import uuid
from datetime import datetime

from backend.database import get_db, ChatHistory, User
from backend.auth import get_current_user
from backend.services.rag_service import rag_service

router = APIRouter(tags=["tutor"])

class ChatRequest(BaseModel):
    subject_id: str
    message: str
    mode: str = "direct"

@router.post("/chat")
def chat(req: ChatRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    history = db.query(ChatHistory)\
        .filter(ChatHistory.user_id == current_user.id, ChatHistory.subject_id == req.subject_id)\
        .order_by(ChatHistory.timestamp.asc())\
        .all()
        
    history_dicts = [{"role": h.role, "message": h.message} for h in history]
    
    # Save user message
    user_msg = ChatHistory(
        id=uuid.uuid4().hex,
        user_id=current_user.id,
        subject_id=req.subject_id,
        role="user",
        message=req.message,
        sources=json_lib.dumps([]),
        timestamp=datetime.utcnow()
    )
    db.add(user_msg)
    
    # Get response from RAG
    response = rag_service.query(req.message, req.subject_id, history_dicts, req.mode)
    
    # Save AI response
    ai_msg = ChatHistory(
        id=uuid.uuid4().hex,
        user_id=current_user.id,
        subject_id=req.subject_id,
        role="assistant",
        message=response["answer"],
        sources=json_lib.dumps(response["sources"]),
        timestamp=datetime.utcnow()
    )
    db.add(ai_msg)
    db.commit()
    
    return {"answer": response["answer"], "sources": response["sources"]}

@router.get("/history/{subject_id}")
def get_history(subject_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(ChatHistory)\
        .filter(ChatHistory.user_id == current_user.id, ChatHistory.subject_id == subject_id)\
        .order_by(ChatHistory.timestamp.asc())\
        .all()

@router.delete("/history/{subject_id}")
def clear_history(subject_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db.query(ChatHistory).filter(ChatHistory.user_id == current_user.id, ChatHistory.subject_id == subject_id).delete()
    db.commit()
    return {"message": "Chat history cleared"}
