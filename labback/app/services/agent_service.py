from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, AIMessageChunk, ToolMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import MessagesState, StateGraph, START
from langgraph.prebuilt import ToolNode, tools_condition
from sqlalchemy.orm import Session

from app.config import settings
from app.exceptions import BizError
from app.models.User import User
from app.schemas.ai import ChatRequest
from app.utils.agent_tools import build_tools
from app.utils.logger import get_logger

# 工具名 → 前端展示的中文文案：tool_start/tool_end 事件里直接带中文名，
# 文案改动只动这张表，不用碰前端代码
TOOL_LABELS={
    "get_today": "获取当前日期",
    "list_open_labs": "查询开放实验室",
    "list_lab_equipment": "查询实验室设备",
    "search_lab_docs": "检索知识库文档",
    "create_lab_reservation": "提交预约",
}

logger = get_logger()
def build_history(data:ChatRequest):
    """构建langchain消息对象"""
    history = []
    for message in data.messages:
        # 只放行合法角色（user/assistant）且内容非空的消息；条件是「合法才加入」，别写反
        if message.role == "user" and message.content.strip():
            history.append(HumanMessage(content=message.content.strip()))
        elif message.role == "assistant" and message.content.strip():
            history.append(AIMessage(content=message.content.strip()))
    if not history:
        raise BizError(message="请输入问题")
    return history

SYSTEM_PROMPT=("你是一个专业的实验室预约系统agent，回答要简洁明了，"
               "并根据检索出的资料库，回答用户关于预约规则、开放时间、安全规范、设备使用的问题。"
               "你只能使用以下五个工具，禁止编造工具名，工具调用必须走系统提供的函数调用通道，禁止把调用过程以文本形式写出来：\n"
               "1. get_today：获取今天日期\n"
               "2. list_open_labs：查询开放的实验室\n"
               "3. list_lab_equipment：查询某实验室的设备\n"
               "4. search_lab_docs：检索预约规则/开放时间/安全规范/设备使用等知识\n"
               "5. create_lab_reservation：提交预约（提交前需先查询并向用户确认）\n"
               "这些工具都是真实可用的：需要实时信息时必须调用工具获取，"
               "在提交预约前，你需要先查询实验室是否开放，再查询设备是否可用，然后向用户汇报，等用户确认后再提交预约记录。"
               "查询实验室后如需了解设备，先拿到实验室 id 再调用设备查询工具。"
               "所有工具调用完成后，你必须用一段完整的中文文字向用户汇报查询结果或预约进展，禁止只回复空内容。"
               "不明确的问题，你可以提示用户到实验室预约功能查看。"
               "不能回复无关问题")

def build_agent(db:Session,current_user:User):
    tools=build_tools(db,current_user)
    llm = ChatOpenAI(base_url=settings.LLM_API_URL, api_key=settings.LLM_API_KEY, model=settings.LLM_API_MODEL,
                    temperature=0.1, streaming=True,
                    # 模型端点（中转站）偶尔会挂起不响应：不设超时的话 langgraph 会永远等，
                    # 前端流式就表现为「一直转圈不返回」。60s 兜底，超时走 error 事件提示重试
                    timeout=60 ).bind_tools(tools)

    def agent_node(state:MessagesState):
        """工作流节点"""
        response=llm.invoke(state["messages"])
        return {"messages":[response]}

    graph = StateGraph(MessagesState)
    graph.add_node("agent",agent_node)
    graph.add_node("tools",ToolNode(tools))
    graph.add_edge(START,"agent")
    # tools_condition：有 tool_calls 走 "tools" 节点，没有时自己返回 END；
    # 不能再 add_edge("agent", END)，否则有工具调用时两条边同时激活，循环被截断
    graph.add_conditional_edges("agent",tools_condition)
    graph.add_edge("tools","agent")
    return graph.compile()#编译工作流

def stream_agent(db:Session,current_user:User,data:ChatRequest ):
    """流式输出生成器
    事件类型：status/tool_start/tool_end/token/done/error
    """
    try:
       history = build_history(data)
       agent=build_agent(db,current_user)
       # 注意：stream 和 invoke 一样，输入必须是 {"messages": [...]} 字典，
       # 裸列表会被当成 __start__ 节点返回值报 Expected dict, got list
       inputs={"messages":[SystemMessage(content=SYSTEM_PROMPT),*history]}
       yield {"type":"status","message":"正在思考"}

       # 单模式流即可拿到全部事件：messages 模式会流出图里产生的每种消息——
       #   1) 模型回答的 AIMessageChunk（文字 token 或工具调用指令碎片）
       #   2) 工具执行完的 ToolMessage
       # 按消息类型分三种情况处理，一一对应到事件
       for chunk,_meta in agent.stream(inputs,config={"recursion_limit":25},stream_mode="messages"):

           if isinstance(chunk,AIMessageChunk):
               # 模型消息：要么是给用户看的文字 token，要么是工具调用指令
               if chunk.tool_call_chunks:
                   # 工具调用指令碎片：只有首帧带工具名（后续帧 name 为空），
                   # 首帧出现 = 工具开始；指令本身不给用户看
                   name=chunk.tool_call_chunks[0].get("name") or ""
                   if name:
                       yield {"type":"tool_start","name":name,"message":TOOL_LABELS.get(name,name)}
               elif chunk.content:
                   # 正常文字增量 → token
                   yield {"type":"token","content":chunk.content}

           elif isinstance(chunk,ToolMessage):
               # 工具结果消息流出 = 该工具已执行完
               yield {"type":"tool_end","name":chunk.name,"message":TOOL_LABELS.get(chunk.name,chunk.name)}

       # stream 自然走完 = 图跑完了（工具循环也包含在内），收尾
       yield {"type":"done"}


    except BizError as e:
        yield {"type":"error","message":str(e)}
    except Exception as e:
        # 生成器里的异常要记日志再转成 error 事件，否则流静默中断前端只知道「断了」
        logger.exception(f"流式智能体运行失败: {e}")
        yield {"type":"error","message":"智能体运行时出错"}


def run_agent(db:Session,user:User,data:ChatRequest ):
    if not data.messages:
        raise BizError(message="messages is empty")
    history = build_history(data)

    agent=build_agent(db,user)
    try:
        # 自建 StateGraph 的输入必须是符合 state 结构的 dict（{"messages": [...]}）；
        # 传裸列表会被当成 __start__ 节点返回值，报 Expected dict, got list
        # 最多跑两次：模型偶发输出伪 <tool_call> 文本或空内容时，重试一次再放弃
        for _ in range(3):
            result=agent.invoke({"messages":[SystemMessage(content=SYSTEM_PROMPT),*history]},
                            # 预约流程要跑 get_today → 查实验室 →（确认后）建预约 等多轮工具，每轮耗 2 步；
                            # 25 是 langgraph 官方默认值，10 会在多工具流程中途被截断
                            config={"recursion_limit":25},
                            )
        reply = result["messages"][- 1].content

        if reply and reply.strip(): return reply.strip()
        # 兜底：重试后仍没有可用的文字回复，显式报错而不是隐式返回 None
        raise BizError(message="智能体未能生成回答，请稍后重试")
    except BizError:
        raise  # 业务异常直接往外抛，不能被下面的兜底覆盖成「运行智能体失败」
    except Exception as e:
        # 完整堆栈进日志，简要原因带回前端，方便排查模型配置/网络/配额问题
        logger.exception(f"运行智能体失败: {e}")
        raise BizError(message=f"运行智能体失败: {e}") from e







