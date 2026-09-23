import uuid
from datetime import datetime
from sqlalchemy import create_engine, Column, String, Integer, Float, Date, Text, ForeignKey, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from backend.config import settings

engine = create_engine(settings.DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    Base.metadata.create_all(bind=engine)

def generate_uuid():
    return uuid.uuid4().hex

class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, default="student")
    created_at = Column(DateTime, default=datetime.utcnow)

class Subject(Base):
    __tablename__ = "subjects"
    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False)
    description = Column(String)
    user_id = Column(String, ForeignKey("users.id"))
    
class Document(Base):
    __tablename__ = "documents"
    id = Column(String, primary_key=True, default=generate_uuid)
    subject_id = Column(String, ForeignKey("subjects.id"))
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    chunk_count = Column(Integer, default=0)
    uploaded_at = Column(DateTime, default=datetime.utcnow)

class StudyPlan(Base):
    __tablename__ = "study_plans"
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"))
    subject_id = Column(String, ForeignKey("subjects.id"))
    title = Column(String, nullable=False)
    start_date = Column(Date)
    end_date = Column(Date)
    schedule = Column(Text) # JSON text
    status = Column(String, default="active")
    created_at = Column(DateTime, default=datetime.utcnow)

class StudyTask(Base):
    __tablename__ = "study_tasks"
    id = Column(String, primary_key=True, default=generate_uuid)
    plan_id = Column(String, ForeignKey("study_plans.id"))
    subject_id = Column(String, ForeignKey("subjects.id"))
    title = Column(String, nullable=False)
    description = Column(String)
    due_date = Column(Date)
    priority = Column(String, default="medium")
    status = Column(String, default="pending")
    estimated_minutes = Column(Integer, default=0)
    actual_minutes = Column(Integer, default=0)

class StudySession(Base):
    __tablename__ = "study_sessions"
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"))
    task_id = Column(String, ForeignKey("study_tasks.id"), nullable=True)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=True)
    focus_score = Column(Integer) # 1-10
    notes = Column(Text)

class Quiz(Base):
    __tablename__ = "quizzes"
    id = Column(String, primary_key=True, default=generate_uuid)
    subject_id = Column(String, ForeignKey("subjects.id"))
    title = Column(String, nullable=False)
    questions = Column(Text) # JSON text
    total_marks = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

class QuizResult(Base):
    __tablename__ = "quiz_results"
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"))
    quiz_id = Column(String, ForeignKey("quizzes.id"))
    score = Column(Float, default=0.0)
    answers = Column(Text) # JSON text
    submitted_at = Column(DateTime, default=datetime.utcnow)

class ChatHistory(Base):
    __tablename__ = "chat_history"
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"))
    subject_id = Column(String, ForeignKey("subjects.id"), nullable=True)
    role = Column(String, nullable=False) # user/assistant
    message = Column(Text, nullable=False)
    sources = Column(Text, nullable=True) # JSON text
    timestamp = Column(DateTime, default=datetime.utcnow)

class ProgressSnapshot(Base):
    __tablename__ = "progress_snapshots"
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"))
    subject_id = Column(String, ForeignKey("subjects.id"))
    completion_pct = Column(Float, default=0.0)
    avg_quiz_score = Column(Float, default=0.0)
    total_study_minutes = Column(Integer, default=0)
    snapshot_date = Column(Date)
