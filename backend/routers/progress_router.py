from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Dict, Any

from backend.database import get_db, User
from backend.auth import get_current_user
from backend.services.progress_service import progress_service
from backend.services.quiz_service import quiz_service

router = APIRouter(tags=["progress"])

class SessionLogReq(BaseModel):
    task_id: str
    start_time: str
    end_time: str
    focus_score: int
    notes: str = ""

class QuizGenerateReq(BaseModel):
    subject_id: str
    num_questions: int = 5
    difficulty: str = "medium"

class QuizSubmitReq(BaseModel):
    quiz_id: str
    answers: Dict[str, str]

@router.get("/dashboard")
def get_dashboard(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return progress_service.get_dashboard_data(current_user.id, db)

@router.post("/session")
def log_session(req: SessionLogReq, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    session = progress_service.log_study_session(
        user_id=current_user.id,
        task_id=req.task_id,
        start_time=req.start_time,
        end_time=req.end_time,
        focus_score=req.focus_score,
        notes=req.notes,
        db=db
    )
    return {"message": "Session logged", "session_id": session.id}

@router.get("/quiz-history")
def get_quiz_history(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return quiz_service.get_user_quiz_history(current_user.id, db)

@router.post("/quiz/generate")
def generate_quiz(req: QuizGenerateReq, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        quiz = quiz_service.create_quiz(req.subject_id, req.num_questions, req.difficulty, db)
        return quiz
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/quiz/submit")
def submit_quiz(req: QuizSubmitReq, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        result = quiz_service.submit_quiz(current_user.id, req.quiz_id, req.answers, db)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
