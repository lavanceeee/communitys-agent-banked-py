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
    try:
        data = await http_client.get("/api/notification/list", params={"pageNum": pageNum, "pageSize": pageSize})
        return json.dumps(data, ensure_ascii=False)
    except Exception as e:
        # 返回更明确的错误信息，告诉 Agent 不要重试
        error_msg = {
            "success": False,
            "error": "服务暂时不可用",
            "message": "抱歉，通知服务当前无法访问，请稍后再试。",
            "detail": str(e)
        }
        return json.dumps(error_msg, ensure_ascii=False)


@tool
async def read_notification(notificationId: str) -> str:
    """
    标记已读。
    如果用户已读消息则标记
    参数: notificationId: 通知ID
    """
    data = await http_client.post(f"/api/notification/{notificationId}/read")
    return json.dumps(data, ensure_ascii=False)