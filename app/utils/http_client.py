import os
import aiohttp
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from app.utils.context import get_request_token

load_dotenv()

Base_Url = os.getenv("Banked_URL")


class HttpClient:
    """异步 HTTP 客户端封装"""

    def __init__(self, base_url: str = Base_Url, timeout: int = 10):
        self.base_url = base_url
        self.timeout = aiohttp.ClientTimeout(total=timeout)

    def _prepare_headers(
        self, headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, str]:
        """
        准备请求头，自动添加 token

        Args:
            headers: 用户传入的额外请求头

        Returns:
            合并后的请求头字典
        """
        # 从上下文中获取 token
        token = get_request_token()

        # 初始化请求头
        final_headers = headers.copy() if headers else {}

        # 如果有 token，添加到请求头
        if token:
            final_headers["Authorization"] = f"Bearer {token}"

        return final_headers

    async def get(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Any:
        """
        发送 GET 请求

        Args:
            endpoint: API 端点，如 '/api/bills'
            params: 查询参数字典
            headers: 请求头字典

        Returns:
            解析后的 JSON 数据
        """
        url = f"{self.base_url}{endpoint}"
        final_headers = self._prepare_headers(headers)

        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            async with session.get(
                url, params=params, headers=final_headers
            ) as response:
                response.raise_for_status()  # 如果状态码不是 2xx，抛出异常
                return await response.json()

    async def post(
        self,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Any:
        """
        发送 POST 请求

        Args:
            endpoint: API 端点，如 '/api/bills'
            data: 表单数据
            json_data: JSON 数据
            headers: 请求头字典

        Returns:
            解析后的 JSON 数据
        """
        url = f"{self.base_url}{endpoint}"
        final_headers = self._prepare_headers(headers)

        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            async with session.post(
                url, data=data, json=json_data, headers=final_headers
            ) as response:
                response.raise_for_status()
                return await response.json()

    async def put(
        self,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Any:
        """发送 PUT 请求"""
        url = f"{self.base_url}{endpoint}"
        final_headers = self._prepare_headers(headers)

        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            async with session.put(
                url, data=data, json=json_data, headers=final_headers
            ) as response:
                response.raise_for_status()
                return await response.json()

    async def delete(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Any:
        """发送 DELETE 请求"""
        url = f"{self.base_url}{endpoint}"
        final_headers = self._prepare_headers(headers)

        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            async with session.delete(
                url, params=params, headers=final_headers
            ) as response:
                response.raise_for_status()
                return await response.json()


# 创建全局实例
http_client = HttpClient()
