from fastapi import APIRouter

from app.api.auth import auth_router
from app.api.user import user_router

api = APIRouter(prefix="/api")
api.include_router(auth_router)
api.include_router(user_router)
