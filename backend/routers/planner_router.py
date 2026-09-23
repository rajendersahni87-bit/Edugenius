from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Dict, Optional

from backend.database import get_db, User
from backend.auth import get_current_user
from backend.services.planner_service import planner_service

router = APIRouter(tags=["planner"])

class PlanGenerateReq(BaseModel):
    subjects: List[str]
    deadlines: Dict[str, str]
    study_hours_per_day: int
    weak_topics: List[str]
    start_date: str
    end_date: str

class TaskUpdateReq(BaseModel):
    status: str
    actual_minutes: int

@router.post("/generate")
def generate_plan(req: PlanGenerateReq, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        res = planner_service.generate_plan(
            user_id=current_user.id,
            subjects=req.subjects,
            deadlines=req.deadlines,
            study_hours=req.study_hours_per_day,
            weak_topics=req.weak_topics,
            start_date=req.start_date,
            end_date=req.end_date,
            db=db
        )
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/plans")
def get_plans(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return planner_service.get_user_plans(current_user.id, db)

@router.get("/today")
def get_today(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return planner_service.get_today_tasks(current_user.id, db)

@router.patch("/tasks/{task_id}")
def update_task(task_id: str, req: TaskUpdateReq, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    success = planner_service.update_task_status(task_id, req.status, req.actual_minutes, db)
    if not success:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"message": "Task updated"}
