# 智能实验室预约系统

基于 **FastAPI + Vue 3** 的实验室预约管理平台，内置 **AI 智能助手**（RAG 知识库 + Function Calling + LangGraph Agent + SSE 流式输出），支持自然语言查询实验室、设备并直接提交预约。

## 功能特性

### 业务功能
- **用户管理**：登录 / 注册 / 个人信息维护，管理员可管理用户角色与启用状态
- **实验室管理**：实验室增删改查、启停控制、图片上传，新增/编辑设备时自动校验实验室容量上限
- **设备管理**：设备与实验室挂载，支持按名称模糊搜索、按实验室过滤分页查询
- **预约管理**：预约状态机（待审核 → 通过 / 拒绝 / 取消），同实验室同设备时间段冲突校验，过期预约后台任务自动处理
- **权限控制**：JWT 鉴权 + 角色菜单分离（管理员 / 学生），登录过期自动跳转登录页

### AI 智能助手
- **RAG 知识库**：基于 chromadb 持久化向量库 + 多语言语义模型，检索实验室规章等文档回答问题
- **Function Calling**：内置查询开放实验室、查询设备、检索知识库、提交预约等工具，用户身份由后端注入、杜绝模型伪造
- **LangGraph Agent**：自建 StateGraph 工具调用循环，最多 5 轮工具调用防无限消耗
- **流式输出**：SSE 流式响应，打字机效果 + 工具调用过程可视化，前端可切换流式 / 非流式模式

## 技术栈

| 层级 | 技术 |
|---|---|
| 后端 | FastAPI · SQLAlchemy · Pydantic · uvicorn |
| 前端 | Vue 3 · Element Plus · Vite · Axios |
| AI | LangChain · LangGraph · langchain-openai（OpenAI 兼容接口） |
| 向量库 | chromadb（持久化） |
| 嵌入模型 | paraphrase-multilingual-MiniLM-L12-v2（本地部署） |

## 项目结构

```
├── labback/                     # 后端
│   ├── app/
│   │   ├── api/                 # 路由层（auth / user / lab / equipment / reservation / ai）
│   │   ├── models/              # SQLAlchemy 模型
│   │   ├── schemas/             # Pydantic 契约
│   │   ├── services/            # 业务逻辑（含 kb_service / agent_service）
│   │   ├── utils/               # 工具（agent_tools 工具定义、日志等）
│   │   └── main.py              # 应用入口（lifespan 预热 + 全局异常处理）
│   ├── data/
│   │   ├── kb/                  # 知识库 Markdown 源文档
│   │   └── chroma/              # 向量库（运行时生成，已 gitignore）
│   ├── models/                  # 本地嵌入模型文件（已 gitignore，见下文部署说明）
│   └── requirements.txt
└── untitled/                    # 前端（Vue 3 + Vite）
    └── src/
        ├── api/                 # 接口封装（含 SSE 流式读取）
        ├── views/               # 页面（含 AI 对话页）
        └── router/              # 路由与角色菜单控制
```

## 快速开始

### 1. 后端

```bash
cd labback
pip install -r requirements.txt

# 配置环境变量（.env）
# LLM_API_URL=OpenAI 兼容接口地址
# LLM_API_KEY=接口密钥
# LLM_API_MODEL=模型名称
# DATABASE_URL=数据库连接串

uvicorn app.main:app --reload
```

### 2. 嵌入模型

向量模型不随仓库分发，需手动下载 paraphrase-multilingual-MiniLM-L12-v2（国内可用 hf-mirror.com 镜像加速），放置到：

```
labback/models/multilingual-minilm-l12/
```

首次启动时若 data/chroma 为空，会自动将 data/kb 下的知识库文档向量化入库；应用启动时会执行向量库预热校验，加载失败将在启动日志中显式报错。

### 3. 前端

```bash
cd untitled
npm install

# .env（Vite 环境变量必须以 VITE_ 开头）
# VITE_API_BASE=后端接口基础地址

npm run dev
```

## AI 助手工作流

```
用户提问
   │
   ▼
LangGraph Agent（system prompt 注入用户身份 + 工具白名单）
   │  bind_tools 绑定原生工具调用
   ▼
┌─ 工具循环（≤5 轮）────────────────────────┐
│  get_today / list_open_labs              │
│  list_lab_equipment / search_lab_docs    │
│  create_lab_reservation                  │
└──────────────────────────────────────────┘
   │
   ▼
最终回答（SSE 流式输出，工具调用过程实时可见）
```

## 说明

- 知识库文档修改后需删除 labback/data/chroma 目录，重启后自动重建向量库
- 业务代码统一通过 BizError 抛出业务异常，由全局异常处理器转换为标准响应格式
- 日志同时输出到控制台与 labback/logs/app.log
