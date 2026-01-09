import json
from langchain_core.tools import tool
from app.utils.http_client import http_client





@tool
async def get_user_notifications(pageNum: int = 0, pageSize: int = 10) -> str:
    """
    查询用户当前所有的通知记录。
    参数: pageNum: 页码
    参数: pageSize: 每页条数
    """

    data = await http_client.get("/api/notification/list", params={"pageNum": pageNum, "pageSize": pageSize})
    return json.dumps(data, ensure_ascii=False)


@tool
async def read_notification(notificationId: str) -> str:
    """
    标记已读。
    如果用户已读消息则标记
    参数: notificationId: 通知ID
    """
    data = await http_client.post(f"/api/notification/{notificationId}/read")
    return json.dumps(data, ensure_ascii=False)