import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.database import init_db
from backend.config import settings

app = FastAPI(
    title="EduGenius API",
    description="Backend API for EduGenius AI Education Platform",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    init_db()
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

try:
    from backend.routers.auth_router import router as auth_router
    from backend.routers.tutor_router import router as tutor_router
    from backend.routers.planner_router import router as planner_router
    from backend.routers.progress_router import router as progress_router
    from backend.routers.document_router import router as document_router
    app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
    app.include_router(tutor_router, prefix="/api/tutor", tags=["tutor"])
    app.include_router(planner_router, prefix="/api/planner", tags=["planner"])
    app.include_router(progress_router, prefix="/api/progress", tags=["progress"])
    app.include_router(document_router, prefix="/api/documents", tags=["documents"])
except ImportError as e:
    print(f"Warning: Some routers not available yet. {e}")

@app.get("/")
def read_root():
    return {"message": "EduGenius API", "version": "1.0.0"}
