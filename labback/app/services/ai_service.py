import json

from openai import OpenAI
from sqlalchemy.orm import Session

from app.config import settings
from app.exceptions import BizError
from app.schemas.ai import ChatRequest
from app.services import kb_service, lab_service, equipment_service
from app.utils.logger import get_logger

logger = get_logger()

SYSTEM_PROMPT=("你是一个专业的实验室预约助手，"
               "你可以通过提供的工具查询实验室和设备的实时信息，"
               "并根据检索出的资料库，回答用户关于预约规则、开放时间、安全规范、设备使用的问题。"
               "查询实验室后如需了解设备，先拿到实验室 id 再调用设备查询工具。"
               "不明确的问题，你可以提示用户到实验室预约功能查看。"
               "不能回复无关问题")

TOOLS =[
    {
        "type": "function",  # 固定类型
        "function": {
            "name": "get_lab_page",  # 工具名（唯一的）
            "description": "查询当前开放实验室列表，可以按关键字查询",  # 告诉模型什么时候用
            "parameters": {  # JSON Schema
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "搜索关键字，可为空"
                    }
                },
                "required": []  # 必填字段列表
            }
        }
    },

    {
        "type": "function",                          # 固定类型
        "function": {
            "name": "get_equipment_page",                  # 工具名（唯一的）
            "description": "查询某个实验室设备列表，可以按关键字查询",   # 告诉模型什么时候用
            "parameters": {                          # JSON Schema
                "type": "object",
                "properties": {
                    "lab_id": {
                        "type": "integer",
                        "description": "实验室ID"
                    },
                    "keyword": {
                        "type": "string",
                        "description": "实验室设备名称，可为空"
                    }
                },
                "required": []                       # 必填字段列表
            }
        }
    }
]

def run_tool(db:Session,name:str,arguments:str)->str:
    try:
        args=json.loads(arguments or "{}")
    except json.JSONDecodeError:
        return json.dumps({"message":"参数格式错误"},ensure_ascii=False)
    try:
        if name=="get_lab_page":
            # 模型给的 keyword 先去空格，空白则视为未传
            keyword=(args.get("keyword") or "").strip() or None
            page = lab_service.get_lab_page(db, page=1, page_size=10, name=keyword, status=1)
            rows=[
                {"id":item.id,
                 "name":item.name,
                 "location":item.location,
                 "capacity":item.capacity,
                 "open_time":item.open_time,
                 "close_time":item.close_time,
                 }
                for item in page.list
            ]
            return json.dumps({"total":page.total,"labs":rows},ensure_ascii=False)
        if name == "get_equipment_page":
            lab_id = args.get("lab_id")
            # 模型给的参数不可信：lab_id 缺失或不是数字都直接把错误文本返回给模型，让它自行调整
            try:
                lab_id = int(lab_id)
            except (TypeError, ValueError):
                return json.dumps({"message": "参数格式错误，lab_id 必须是数字"}, ensure_ascii=False)
            keyword = (args.get("keyword") or "").strip() or None
            page = equipment_service.get_equipment_page(db, page=1, page_size=10,
                                               name=keyword,lab_id=lab_id)
            rows = [
                {"id": item.id,
                 "name": item.name,
                 'lab_id': item.lab_id,
                 "lab_name": item.lab_name,
                 "quantity": item.quantity,
                 "spec": item.spec,
                 "status": item.status,
                 }
                for item in page.list
            ]
            return json.dumps({"total": page.total, "equipments": rows}, ensure_ascii=False)
    except BizError as e:
        return json.dumps({"message": f"我们无法执行{name}工具，{e.message}"}, ensure_ascii=False)
    # 模型可能幻觉出不存在的工具名；两个 if 都没命中时返回 None 会导致 API 报错，必须兜底
    return json.dumps({"message": f"未知工具 {name}"}, ensure_ascii=False)


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

def chat(db:Session,data:ChatRequest):
    if not data.messages:
        raise BizError(message="messages is empty")
    history = []
    for message in data.messages:
        # 只放行合法角色（user/assistant）且内容非空的消息；条件是「合法才加入」，别写反
        if message.role in ["user", "assistant"] and message.content.strip():
            history.append(message.model_dump())

    if not history:
        raise BizError(message="请输入问题")

    # history 里是 model_dump() 转出的字典，取字段要用 ["role"] 而不是 .role（.role 会 AttributeError）
    question = next((item["content"] for item in reversed(history) if item["role"] == "user"), "")

    kb_results=kb_service.search(question) if question else ""
    system_prompt=SYSTEM_PROMPT
    if kb_results:
        system_prompt += f"\n以下是检索出的资料：\n\n{kb_results}"
    client = get_client()
    try:
        # 上下文从「系统提示词 + 完整历史」开始，工具循环往这个列表里追加消息
        messages = [{"role": "system", "content": system_prompt}] + history
        # 工具循环：模型请求工具 → 执行 → 结果以 role=tool 追加 → 再次请求，直到给出纯文字回复。
        # 必须设最大轮数，防止模型陷入「无限调工具」的循环烧配额
        for _ in range(5):
            response = client.chat.completions.create(
                # 模型名统一从 settings 读取（pydantic-settings 读 .env，不会注入 os.environ，getenv 取不到）
                model=settings.LLM_API_MODEL,
                messages=messages,
                tools=TOOLS,
                tool_choice="auto",
            )
            # 从响应里取第一条回复的 message 对象（变量名别和返回值弄混，之前写成 message 导致 NameError）
            message = response.choices[0].message
            tool_calls = message.tool_calls or []
            if not tool_calls:
                # 无工具调用：模型给出了最终文字回复，直接返回
                content = message.content
                if not content or not content.strip():
                    raise BizError(message="大模型未返回内容")
                return content.strip()

            # 有工具调用：先把模型本轮的 assistant 消息（含 tool_calls）原样加入上下文，
            # 格式固定为 {id, type, function:{name, arguments}}，模型下一轮要靠它对应工具结果
            messages.append({
                "role": "assistant",
                "content": message.content or "",
                "tool_calls": [
                    {
                        "id": tool_call.id,
                        "type": "function",
                        "function": {
                            "name": tool_call.function.name,
                            "arguments": tool_call.function.arguments,
                        },
                    }
                    for tool_call in tool_calls
                ],
            })
            # 逐个执行工具，结果以 role=tool 消息追加；tool_call_id 必须与请求时的 id 一一对应
            for tool_call in tool_calls:
                result = run_tool(db, tool_call.function.name, tool_call.function.arguments)
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result,
                })
        # 连续 5 轮都在调工具仍没有最终回复：主动止损，不让用户干等
        raise BizError(message="AI 处理轮次过多，请稍后重试或换个问法")
    except BizError:
        raise  # 业务异常直接往外抛，不能被下面的兜底 except 覆盖成 chat error
    except Exception as e:
        # 记录完整异常到后端日志，并把简要原因带回给前端，方便排查配置/网络问题
        logger.exception(f"AI 服务调用失败: {e}")
        raise BizError(message=f"AI 服务调用失败: {e}") from e
