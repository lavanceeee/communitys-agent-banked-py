import json
from typing import Optional
from langchain_core.tools import tool
from app.utils.http_client import http_client


@tool
async def search_goods(
    keyword: Optional[str] = None,
    category_id: Optional[int] = 0,
    page_num: Optional[int] = 1,
    page_size: Optional[int] = 10,
) -> str:
    """
    搜索商品列表。
    可以根据关键词、分类ID进行筛选，支持分页。
    """
    try:
        print("---进来了----")
        params = {
            "categoryId": category_id,
            "keyword": keyword,
            "pageNum": page_num,
            "pageSize": page_size,
        }

        response = await http_client.post("/api/mall/list", json_data=params)
        print(f"{response}---")
        return json.dumps(response, ensure_ascii=False)
    except Exception as e:
        print(e)
        error_msg = {
            "success": False,
            "error": "服务暂时不可用",
            "message": "抱歉，商品搜索服务当前无法访问，请稍后再试。",
            "detail": str(e),
        }
        return json.dumps(error_msg, ensure_ascii=False)
