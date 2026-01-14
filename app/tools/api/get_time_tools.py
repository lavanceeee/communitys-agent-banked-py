import json
import aiohttp
from langchain_core.tools import tool
from uvicorn.main import logger
from app.utils.http_client import http_client
from datetime import datetime

@tool
async def get_time() -> str:
    """获取当前时间"""
    return json.dumps(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), ensure_ascii=False)