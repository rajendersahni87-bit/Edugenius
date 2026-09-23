from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from pydantic import BaseModel
import uuid
import os
from datetime import datetime

from backend.database import get_db, Subject, Document, User
from backend.auth import get_current_user
from backend.services.rag_service import rag_service
from backend.config import settings

router = APIRouter(tags=["documents"])

class SubjectCreate(BaseModel):
    name: str
    description: str

@router.post("/subjects")
def create_subject(req: SubjectCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    sub = Subject(
        id=uuid.uuid4().hex,
        name=req.name,
        description=req.description,
        user_id=current_user.id
    )
    db.add(sub)
    db.commit()
    db.refresh(sub)
    return sub

@router.get("/subjects")
def get_subjects(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Subject).filter(Subject.user_id == current_user.id).all()

@router.post("/upload")
async def upload_document(
    subject_id: str = Form(...), 
    file: UploadFile = File(...), 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    subject = db.query(Subject).filter(Subject.id == subject_id, Subject.user_id == current_user.id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found or unauthorized")
        
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    file_path = os.path.join(settings.UPLOAD_DIR, f"{uuid.uuid4().hex}_{file.filename}")
    
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)
        
    chunk_count = rag_service.ingest_document(file_path, subject_id)
    
    doc = Document(
        id=uuid.uuid4().hex,
        subject_id=subject_id,
        filename=file.filename,
        file_path=file_path,
        chunk_count=chunk_count,
        uploaded_at=datetime.utcnow()
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    
    return {"message": "Document uploaded and ingested successfully", "document": doc}

@router.get("/list/{subject_id}")
def list_documents(subject_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    subject = db.query(Subject).filter(Subject.id == subject_id, Subject.user_id == current_user.id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found or unauthorized")
    return db.query(Document).filter(Document.subject_id == subject_id).all()
