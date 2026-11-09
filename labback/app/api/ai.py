from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.User import User
from app.schemas.ai import ChatRequest
from app.schemas.response import Result
from app.services import ai_service

ai_router: APIRouter = APIRouter(prefix="/ai",tags=["ai相关"])
@ai_router.post("/chat")
def chat(data: ChatRequest,
         current_user: User = Depends(get_current_user),  # 注意：传函数本身，不能加括号调用
         db: Session = Depends(get_db)):
    message = ai_service.chat(data)
    return Result.success(data=message)
