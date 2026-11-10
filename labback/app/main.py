import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles

from app.api import api
from app.config import UPLOAD_DIR
from app.database import Base, engine
from app.exceptions import BizError, ErrorCode
from app.services import reservation_service
from app.utils.logger import get_logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 应用启动时：拉起「过期预约自动取消」的后台扫描任务（每分钟一次）
    expire_task = asyncio.create_task(reservation_service.run_expire_scan())
    # 预热知识库向量库：加载嵌入模型并完成向量导入，
    # 模型文件缺失时启动阶段立刻报错，避免等到用户提问才失败（静默劣化最难排查）
    try:
        from app.services import kb_service
        kb_service.get_collection()
        logger.info("知识库向量库初始化完成")
    except Exception as e:
        logger.exception(f"知识库初始化失败（检查 labback/models 下的模型文件是否齐全）: {e}")
    yield  # yield 之前是启动阶段，之后是运行阶段；没有 yield 应用无法启动
    # 应用关闭时：取消后台任务，避免事件循环关闭时报错
    expire_task.cancel()


#fastapi 应用实例
app = FastAPI(lifespan=lifespan)
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
app.include_router(api)
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,#允许的来源
    allow_credentials=True,#允许跨域请求携带凭证
    allow_methods=["*"],#允许的请求方法
    allow_headers=["*"],#允许的请求头
)
#挂载文件上传目录
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")
logger = get_logger()




#统一异常处理：所有异常最终都转换为 {code, message, data} 格式
@app.exception_handler(BizError)
async def biz_error_handler(request: Request, exc: BizError):
    #业务失败：HTTP 状态码跟随异常定义（默认400，未登录401）
    logger.info(f"业务异常 {request.url.path}: code={exc.code}, message={exc.message}")
    return JSONResponse(
        status_code=exc.http_status,
        content={"code": exc.code, "message": exc.message, "data": None},
    )

@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    #参数校验失败：只取第一条错误信息，提示更友好
    first = exc.errors()[0]
    field = ".".join(str(loc) for loc in first.get("loc", []) if loc != "body")
    message = f"参数 {field} {first.get('msg', '校验失败')}" if field else first.get("msg", "参数校验失败")
    return JSONResponse(
        status_code=400,
        content={"code": ErrorCode.PARAM_ERROR, "message": message, "data": None},
    )

@app.exception_handler(Exception)
async def unknown_error_handler(request: Request, exc: Exception):
    #系统异常：对内记录完整日志，对外隐藏细节
    logger.exception(f"系统异常 {request.url.path}: {exc}")
    return JSONResponse(
        status_code=500,
        content={"code": ErrorCode.SYSTEM_ERROR, "message": "系统繁忙，请稍后重试", "data": None},
    )

Base.metadata.create_all(bind=engine)

#get方式的请求接口
@app.get("/")
def read_root():
    return {"Hello": "World"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
