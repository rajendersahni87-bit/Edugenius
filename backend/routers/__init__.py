from fastapi import APIRouter
from .auth_router import router as auth_router
from .document_router import router as document_router
from .tutor_router import router as tutor_router
from .planner_router import router as planner_router
from .progress_router import router as progress_router

__all__ = [
    "auth_router",
    "document_router",
    "tutor_router",
    "planner_router",
    "progress_router"
]
