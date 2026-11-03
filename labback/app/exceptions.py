#统一业务异常与错误码
class ErrorCode:
    OK = 200
    PARAM_ERROR = 400       #通用业务错误
    UNAUTHORIZED = 401      #未登录/凭证失效
    FORBIDDEN = 403         #无权限
    NOT_FOUND = 404         #资源不存在
    SYSTEM_ERROR = 500      #系统内部错误


class BizError(Exception):
    """业务异常：可预期的失败，由全局异常处理器统一转换为 Result 格式"""
    http_status: int = 400  #对应的 HTTP 状态码

    def __init__(self, code: int = ErrorCode.PARAM_ERROR, message: str = "业务处理失败"):
        self.code = code
        self.message = message
        super().__init__(message)


class UnauthorizedError(BizError):
    """未登录/登录过期，HTTP 状态码返回 401"""
    http_status = 401
