import json
import uuid
from typing import List, Dict, Any
from datetime import datetime, date
from sqlalchemy.orm import Session
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage
from backend.config import settings
from backend.database import StudyPlan, StudyTask
from backend.prompts.planner_prompt import PLANNER_SYSTEM_PROMPT, PLANNER_TEMPLATE

class PlannerService:
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(model='gemini-3.6-flash', google_api_key=settings.GOOGLE_API_KEY)
        
    def generate_plan(self, user_id: str, subjects: list, deadlines: dict, study_hours: int, weak_topics: list, start_date: str, end_date: str, db: Session) -> dict:
        try:
            prompt = PLANNER_TEMPLATE.format(
                subjects=json.dumps(subjects),
                deadlines=json.dumps(deadlines),
                study_hours=study_hours,
                weak_topics=json.dumps(weak_topics),
                start_date=start_date,
                end_date=end_date
            )
            
            response = self.llm.invoke([
                SystemMessage(content=PLANNER_SYSTEM_PROMPT),
                HumanMessage(content=prompt)
            ])
            
            content = response.content
            if isinstance(content, list):
                content = " ".join(
                    part.get("text", str(part)) if isinstance(part, dict) else str(part)
                    for part in content
                )
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].strip()
                
            plan_data = json.loads(content)
            
            # Handle both flat array and {tasks: [...]} format from LLM
            if isinstance(plan_data, list):
                tasks_list = plan_data
                plan_data = {"tasks": tasks_list}
            else:
                tasks_list = plan_data.get("tasks", [])
            
            plan = StudyPlan(
                id=uuid.uuid4().hex,
                user_id=user_id,
                subject_id=subjects[0] if subjects else None,
                title=f"Study Plan from {start_date} to {end_date}",
                start_date=datetime.strptime(start_date, "%Y-%m-%d").date(),
                end_date=datetime.strptime(end_date, "%Y-%m-%d").date(),
                schedule=json.dumps(plan_data),
                status="active"
            )
            db.add(plan)
            
            tasks = tasks_list
            for t in tasks:
                task = StudyTask(
                    id=uuid.uuid4().hex,
                    plan_id=plan.id,
                    subject_id=t.get("subject_id") or (subjects[0] if subjects else None),
                    title=t.get("title", "Study Task"),
                    description=t.get("description", ""),
                    due_date=datetime.strptime(t.get("date", end_date), "%Y-%m-%d").date() if t.get("date") else None,
                    priority=t.get("priority", "medium"),
                    status="pending",
                    estimated_minutes=t.get("estimated_minutes", 60),
                    actual_minutes=0
                )
                db.add(task)
            
            db.commit()
            db.refresh(plan)
            return {"plan_id": plan.id, "message": "Plan created successfully", "tasks_created": len(tasks)}
        except Exception as e:
            db.rollback()
            raise Exception(f"Failed to generate plan: {str(e)}")

    def get_user_plans(self, user_id: str, db: Session) -> list:
        plans = db.query(StudyPlan).filter(StudyPlan.user_id == user_id).all()
        return [{"id": p.id, "title": p.title, "status": p.status, "start_date": p.start_date.isoformat(), "end_date": p.end_date.isoformat()} for p in plans]
        
    def update_task_status(self, task_id: str, status: str, actual_minutes: int, db: Session):
        task = db.query(StudyTask).filter(StudyTask.id == task_id).first()
        if task:
            task.status = status
            task.actual_minutes = actual_minutes
            db.commit()
            return True
        return False
        
    def get_today_tasks(self, user_id: str, db: Session) -> list:
        today = date.today()
        plan_ids = [p.id for p in db.query(StudyPlan.id).filter(StudyPlan.user_id == user_id).all()]
        if not plan_ids:
            return []
            
        tasks = db.query(StudyTask).filter(StudyTask.plan_id.in_(plan_ids), StudyTask.due_date == today).all()
        return [{"id": t.id, "title": t.title, "status": t.status, "estimated_minutes": t.estimated_minutes, "subject_id": t.subject_id} for t in tasks]

planner_service = PlannerService()
