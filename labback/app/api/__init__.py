from fastapi import APIRouter

from app.api.auth import auth_router
from app.api.files import file_router
from app.api.lab import lab_router
from app.api.user import user_router

api = APIRouter(prefix="/api")
api.include_router(auth_router)
api.include_router(user_router)
api.include_router(file_router)
api.include_router(lab_router)
