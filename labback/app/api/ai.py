import json

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.User import User
from app.schemas.ai import ChatRequest
from app.schemas.response import Result
from app.services import agent_service

ai_router: APIRouter = APIRouter(prefix="/ai",tags=["ai相关"])
@ai_router.post("/chat")
def chat(data: ChatRequest,
         current_user: User = Depends(get_current_user),  # 注意：传函数本身，不能加括号调用
         db: Session = Depends(get_db)):
    # 走 LangGraph agent（含查询/预约/知识库/日期工具）；db 和当前用户用于工具闭包，身份不经过模型
    message = agent_service.run_agent(db, current_user, data)
    return Result.success(data=message)

@ai_router.post("/chat/stream")
def chat_stream(data: ChatRequest,
                current_user: User = Depends(get_current_user),
                db: Session = Depends(get_db)):
    """流式对话接口（SSE）
    把 service 生成器产出的每个事件 dict 包成 SSE 帧：
    格式固定为 "data: {json}\\n\\n"（data: 前缀 + 空行结尾），前端按空行切帧解析
    """
    def sse():
        for event in agent_service.stream_agent(db, current_user, data):
            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
    # media_type 必须是 text/event-stream，浏览器/前端才知道这是 SSE 流
    return StreamingResponse(sse(), media_type="text/event-stream")
