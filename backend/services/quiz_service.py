import json
import uuid
from datetime import datetime
from sqlalchemy.orm import Session
from backend.database import Quiz, QuizResult
from backend.services.rag_service import rag_service

class QuizService:
    def create_quiz(self, subject_id: str, num_questions: int, difficulty: str, db: Session) -> dict:
        questions = rag_service.generate_quiz(
            subject_id=subject_id, 
            num_questions=num_questions, 
            difficulty=difficulty
        )
        
        if not questions:
            raise Exception("Failed to generate questions. Make sure documents are uploaded for this subject.")
            
        quiz = Quiz(
            id=uuid.uuid4().hex,
            subject_id=subject_id,
            title=f"{difficulty.capitalize()} Quiz",
            questions=json.dumps(questions),
            total_marks=len(questions)
        )
        
        db.add(quiz)
        db.commit()
        db.refresh(quiz)
        
        return {
            "id": quiz.id,
            "title": quiz.title,
            "questions": questions,
            "total_marks": quiz.total_marks
        }

    def submit_quiz(self, user_id: str, quiz_id: str, answers: dict, db: Session) -> dict:
        quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
        if not quiz:
            raise Exception("Quiz not found")
            
        score = 0
        results_per_question = []
        
        # Parse questions from JSON string
        questions = json.loads(quiz.questions) if isinstance(quiz.questions, str) else quiz.questions
        
        for i, q in enumerate(questions):
            q_id = str(i)
            correct = q.get("correct_answer", "")
            user_ans = answers.get(q_id, "")
            
            is_correct = str(user_ans).strip().lower() == str(correct).strip().lower()
            if is_correct:
                score += 1
                
            results_per_question.append({
                "question_id": q_id,
                "question_text": q.get("question", ""),
                "user_answer": user_ans,
                "correct_answer": correct,
                "is_correct": is_correct
            })
            
        total = quiz.total_marks
        percentage = (score / total) * 100 if total > 0 else 0
        
        quiz_result = QuizResult(
            id=uuid.uuid4().hex,
            user_id=user_id,
            quiz_id=quiz_id,
            score=score,
            answers=json.dumps(answers),
            submitted_at=datetime.utcnow()
        )
        
        db.add(quiz_result)
        db.commit()
        db.refresh(quiz_result)
        
        return {
            "result_id": quiz_result.id,
            "score": score,
            "total": total,
            "percentage": percentage,
            "results_per_question": results_per_question
        }

    def get_user_quiz_history(self, user_id: str, db: Session) -> list:
        results = db.query(QuizResult, Quiz.title, Quiz.subject_id)\
            .join(Quiz, QuizResult.quiz_id == Quiz.id)\
            .filter(QuizResult.user_id == user_id)\
            .order_by(QuizResult.submitted_at.desc())\
            .all()
            
        history = []
        for r, title, subject_id in results:
            history.append({
                "id": r.id,
                "quiz_id": r.quiz_id,
                "title": title,
                "subject_id": subject_id,
                "score": r.score,
                "submitted_at": r.submitted_at.isoformat()
            })
            
        return history

quiz_service = QuizService()
