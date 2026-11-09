from openai import OpenAI

from app.config import settings
from app.exceptions import BizError
from app.schemas.ai import ChatRequest
from app.utils.logger import get_logger

logger = get_logger()

SYSTEM_PROMPT=("你是一个专业的实验室预约助手，"
               "你的任务是根据用户的问题，预约实验室的资源。但是现在你无法查看数据，所以可以提示用户到实验室预约功能查看")
def get_client():
    """获取AI客户端"""
    if not settings.LLM_API_KEY:
        raise BizError(message="LLM_API_KEY is not error")
    if not settings.LLM_API_URL:
        raise BizError(message="LLM_API_URL is not error")
    return OpenAI(
        api_key=settings.LLM_API_KEY,
        base_url=settings.LLM_API_URL,
    )

def chat(data:ChatRequest):
    if not data.messages:
        raise BizError(message="messages is empty")
    history = []
    for message in data.messages:
        # 只放行合法角色（user/assistant）且内容非空的消息；条件是「合法才加入」，别写反
        if message.role in ["user", "assistant"] and message.content.strip():
            history.append(message.model_dump())

    if not history:
        raise BizError(message="请输入问题")
    client = get_client()
    try:
        response = client.chat.completions.create(
            # 模型名统一从 settings 读取（pydantic-settings 读 .env，不会注入 os.environ，getenv 取不到）
            model=settings.LLM_API_MODEL,
            # 系统提示词用 role="system"；messages 必须是一个完整列表，不能再用 *history 位置解包
            messages=[{"role": "system", "content": SYSTEM_PROMPT}] + history,
        )
        # 从响应里取第一条回复的 message 对象（变量名别和返回值弄混，之前写成 message 导致 NameError）
        reply = response.choices[0].message
        if not reply or not reply.content:
            raise BizError(message="大模型未返回内容")
        return reply.content.strip()
    except BizError:
        raise  # 业务异常直接往外抛，不能被下面的兜底 except 覆盖成 chat error
    except Exception as e:
        # 记录完整异常到后端日志，并把简要原因带回给前端，方便排查配置/网络问题
        logger.exception(f"AI 服务调用失败: {e}")
        raise BizError(message=f"AI 服务调用失败: {e}") from e
