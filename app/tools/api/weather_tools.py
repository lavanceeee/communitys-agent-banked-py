import json
import aiohttp
from langchain_core.tools import tool
from uvicorn.main import logger
from app.utils.http_client import http_client


async def _external_get(url: str) -> dict:
    """发送外部 GET 请求（不带 base_url）"""
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            response.raise_for_status()
            return await response.json()


@tool
async def get_weather(city: str = "") -> str:
    """获取城市天气，参数: city: 城市,参数city为空时默认查询当前ip地址的城市天气"""
    # 内部 API 调用，使用 http_client
    if city == "":
        ip_address_data = await http_client.get("/api/user/ip")

        logger.info(f"ip_address_data: {ip_address_data}")
        ip_address = ip_address_data.get("data")

        logger.info(f"ip_address_data: {ip_address_data}")
        logger.info(f"ip_address: {ip_address}")

        # 外部 API 调用，使用 _external_get
        city_data = await _external_get(f"https://api.52vmy.cn/api/query/itad?ip={ip_address}")

        logger.info(f"city_data: {city_data}")

        # 取空格前字符串
        logger.info(f"city_data.get('data').get('address'): {city_data.get('data').get('address')}")
        city = city_data.get("data").get("address").split(" ")[0]

        # 外部 API 调用，使用 _external_get
        data = await _external_get(f"https://api.52vmy.cn/api/query/tian?city={city}")
    

        logger.info(f"data: {data}")

    else:
        data = await _external_get(f"https://api.52vmy.cn/api/query/tian?city={city}")
    return json.dumps(data, ensure_ascii=False)