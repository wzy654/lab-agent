from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.api import api
from app.database import Base, engine
from app.exceptions import BizError, ErrorCode
from app.utils.logger import get_logger

#fastapi 应用实例
app = FastAPI()
app.include_router(api)

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
