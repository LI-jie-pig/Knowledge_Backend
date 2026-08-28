import traceback
from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from starlette import status

# 开发模式：返回详细错误堆栈；生产改为False
DEBUG_MODE = True


async def http_exception_handler(request: Request, exc: HTTPException):
    """处理 HTTPException 业务异常"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": exc.status_code,
            "message": exc.detail,
            "data": None
        }
    )

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    # 缺 Authorization → 按未登录处理，前端好提示
    for err in errors:
        loc = err.get("loc") or []
        if "Authorization" in loc:
            return JSONResponse(
                status_code=401,
                content={"code": 401, "message": "请先登录", "data": None},
            )
        first = errors[0] if errors else {}
        loc = ".".join(str(x) for x in first.get("loc", []) if x not in ("body", "query", "header"))
        msg = first.get("msg", "请求参数错误")
        message = f"{loc}: {msg}" if loc else msg
        return JSONResponse(
            status_code=422,
            content={"code": 422, "message": message, "data": errors if DEBUG_MODE else None},
        )
async def integrity_error_handler(request: Request, exc: IntegrityError):
    """处理数据库完整性约束错误：唯一索引冲突、外键约束"""
    error_msg = str(exc.orig)
    # 识别不同约束报错
    if "username_UNIQUE" in error_msg or "Duplicate entry" in error_msg:
        detail = "用户名已存在"
    elif "FOREIGN KEY" in error_msg:
        detail = "关联数据不存在"
    else:
        detail = "数据约束冲突，请检查输入"

    error_data = None
    if DEBUG_MODE:
        error_data = {
            "error_type": "IntegrityError",
            "error_detail": error_msg,
            "path": str(request.url)
        }
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "code": 400,
            "message": detail,
            "data": error_data
        }
    )


async def sqlalchemy_error_handler(request: Request, exc: SQLAlchemyError):
    """处理SQLAlchemy通用数据库异常"""
    error_data = None
    if DEBUG_MODE:
        error_data = {
            "error_type": type(exc).__name__,
            "error_detail": str(exc),
            "traceback": traceback.format_exc(),
            "path": str(request.url)
        }
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "code": 500,
            "message": "数据库操作失败，请稍后重试",
            "data": error_data
        }
    )


async def general_exception_handler(request: Request, exc: Exception):
    """捕获所有未处理的未知异常，全局兜底"""
    error_data = None
    if DEBUG_MODE:
        error_data = {
            "error_type": type(exc).__name__,
            "error_detail": str(exc),
            "traceback": traceback.format_exc(),
            "path": str(request.url)
        }
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "code": 500,
            "message": "服务器内部错误，请稍后重试",
            "data": error_data
        }
    )


def register_exception_handlers(app):
    """注册全局异常处理器，注册顺序：具体异常在前，通用兜底放最后""" 
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(IntegrityError, integrity_error_handler)
    app.add_exception_handler(SQLAlchemyError, sqlalchemy_error_handler)
    app.add_exception_handler(Exception, general_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
