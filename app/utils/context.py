"""
上下文管理器 - 用于在异步调用链中传递请求上下文信息（如 token）
"""

from contextvars import ContextVar
from typing import Optional

# 创建上下文变量来存储 token
request_token: ContextVar[Optional[str]] = ContextVar("request_token", default=None)


def set_request_token(token: str):
    """设置当前请求的 token"""
    request_token.set(token)


def get_request_token() -> Optional[str]:
    """获取当前请求的 token"""
    print(f"-----当前的token是{request_token.get()}-----")
    return request_token.get()
