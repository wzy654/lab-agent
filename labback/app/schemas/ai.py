from pydantic import BaseModel


class ChatMessage(BaseModel):
    role: str#角色
    content: str#内容

class ChatRequest(BaseModel):
    messages: list[ChatMessage]#消息列表
    
