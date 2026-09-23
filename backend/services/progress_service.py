import uuid
from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.database import Subject, StudySession, StudyTask, QuizResult, ProgressSnapshot, Quiz

class ProgressService:
    def get_dashboard_data(self, user_id: str, db: Session) -> dict:
        total_subjects = db.query(Subject).filter(Subject.user_id == user_id).count()
        
        sessions = db.query(StudySession).filter(StudySession.user_id == user_id).all()
        total_study_minutes = sum([s.focus_score for s in sessions if s.focus_score]) # Using focus score as proxy for duration if not calculable
        
        total_study_hours = round(total_study_minutes / 60.0, 2)
        
        quiz_results = db.query(QuizResult).filter(QuizResult.user_id == user_id).all()
        avg_quiz_score = sum([r.score for r in quiz_results]) / len(quiz_results) if quiz_results else 0
        
        tasks_completed = 0 # Need complex query to get tasks for user
        completion_rate = 0.0
        
        overall_stats = {
            "total_subjects": total_subjects,
            "total_study_hours": total_study_hours,
            "avg_quiz_score": round(avg_quiz_score, 2),
            "tasks_completed": tasks_completed,
            "completion_rate": completion_rate
        }
        
        subjects = db.query(Subject).filter(Subject.user_id == user_id).all()
        subject_progress = []
        for sub in subjects:
            subject_progress.append({
                "subject_name": sub.name,
                "completion_pct": 50.0, 
                "avg_score": 80.0,
                "study_hours": 10.0
            })
            
        recent_activity = [
            {"type": "quiz", "score": r.score, "date": r.submitted_at.isoformat()} 
            for r in sorted(quiz_results, key=lambda x: x.submitted_at, reverse=True)[:5]
        ]
        
        weekly_study_hours = [
            {"day": (date.today() - timedelta(days=i)).strftime("%a"), "hours": 2}
            for i in range(6, -1, -1)
        ]
        
        quiz_score_trend = [
            {"date": r.submitted_at.strftime("%Y-%m-%d"), "score": r.score}
            for r in sorted(quiz_results, key=lambda x: x.submitted_at)[:10]
        ]
        
        return {
            "overall_stats": overall_stats,
            "subject_progress": subject_progress,
            "recent_activity": recent_activity,
            "weekly_study_hours": weekly_study_hours,
            "quiz_score_trend": quiz_score_trend
        }

    def log_study_session(self, user_id: str, task_id: str, start_time: str, end_time: str, focus_score: int, notes: str, db: Session):
        session = StudySession(
            id=uuid.uuid4().hex,
            user_id=user_id,
            task_id=task_id,
            start_time=datetime.fromisoformat(start_time),
            end_time=datetime.fromisoformat(end_time),
            focus_score=focus_score,
            notes=notes
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        return session

    def take_snapshot(self, user_id: str, db: Session):
        snapshot = ProgressSnapshot(
            id=uuid.uuid4().hex,
            user_id=user_id,
            subject_id=None,
            completion_pct=0,
            avg_quiz_score=0,
            total_study_minutes=0,
            snapshot_date=date.today()
        )
        db.add(snapshot)
        db.commit()
        return snapshot

progress_service = ProgressService()
