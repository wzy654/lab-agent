from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
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

logger = get_logger()

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
                    temperature=0.3 ).bind_tools(tools)#温度 0 时重试输出几乎不变，留一点随机性让重试有意义

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


def _extract_reply(result)->str | None:
    """从图的最终状态里提取要返回给用户的文字；拿不到有效回答时返回 None

    结果 messages 里混着 system/human/ai/tool 多种消息；
    LangChain 消息没有 .role 属性（会 AttributeError），判断类型必须用 isinstance；
    带 tool_calls 的 AIMessage 是「过渡语」（模型调工具前说的话），不能当最终回答
    """
    messages = result.get("messages") or []
    for message in reversed(messages):
        if isinstance(message, AIMessage) and not message.tool_calls:
            content = message.content
            if isinstance(content, list):
                # 多模态返回时 content 是分段列表，拼接出纯文本部分
                content = "".join(
                    part.get("text","") if isinstance(part,dict) else str(part)
                    for part in content
                )
            if not content or not content.strip():
                logger.warning(f"跳过空 content 的 AIMessage，tool_calls={bool(message.tool_calls)}")
                continue
            text=content.strip()
            # 有些模型（尤其经 Qwen 系模板的中转）偶发把工具调用以标签文本写在
            # content 里而不是走原生 tool_calls 通道——这不是给用户看的答案
            if "<tool_call>" in text or "<function=" in text:
                # 记录被过滤的内容摘要，便于从日志判断模型是否又在「文本模仿」工具调用
                logger.warning(f"过滤伪工具调用文本输出: {text[:200]}")
                return None
            return text
    logger.warning("最终状态中未找到可用的 AIMessage 文字回复")
    return None

def run_agent(db:Session,user:User,data:ChatRequest ):
    if not data.messages:
        raise BizError(message="messages is empty")
    history = []
    for message in data.messages:
        # 只放行合法角色（user/assistant）且内容非空的消息；条件是「合法才加入」，别写反
        if message.role == "user" and message.content.strip():
            history.append(HumanMessage(content=message.content.strip()))
        elif message.role == "assistant" and message.content.strip():
            history.append(AIMessage(content=message.content.strip()))
    if not history:
        raise BizError(message="请输入问题")

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
            reply=_extract_reply(result)
            if reply is not None:
                return reply
        # 兜底：重试后仍没有可用的文字回复，显式报错而不是隐式返回 None
        raise BizError(message="智能体未能生成回答，请稍后重试")
    except BizError:
        raise  # 业务异常直接往外抛，不能被下面的兜底覆盖成「运行智能体失败」
    except Exception as e:
        # 完整堆栈进日志，简要原因带回前端，方便排查模型配置/网络/配额问题
        logger.exception(f"运行智能体失败: {e}")
        raise BizError(message=f"运行智能体失败: {e}") from e







