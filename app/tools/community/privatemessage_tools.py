import json
from langchain_core.tools import tool
from app.utils.http_client import http_client




@tool
async def send_private_messages(content: str, toUserId: str) -> str:

    """
    代替用户向其他用户发送私信。
    参数: content: 私信内容
    参数: toUserId: 接收用户ID
    """

    data = await http_client.post("/api/message/send", json_data={"content": content, "toUserId": toUserId})
    return json.dumps(data, ensure_ascii=False)
