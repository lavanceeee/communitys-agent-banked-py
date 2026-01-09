"""
WebSocket 路由处理器
"""

from fastapi import WebSocket, WebSocketDisconnect
from app.websocket.manager import manager
from app.services.agent_stream import get_agent_response_stream
import json


async def websocket_chat_handler(
    websocket: WebSocket, user_id: str, already_accepted: bool = False
):
    """
    WebSocket 聊天处理器

    Args:
        websocket: WebSocket 连接
        user_id: 已验证的用户 ID
        already_accepted: 是否已经 accept 过连接
    """
    # 建立连接
    if not already_accepted:
        await manager.connect(websocket, user_id)
    else:
        # 已经 accept 过了，只注册连接
        manager.active_connections[user_id] = websocket

    try:
        while True:
            # 接收消息
            data = await websocket.receive_text()
            message = json.loads(data)
            query = message.get("query", "")

            if query:
                await get_agent_response_stream(user_id, query)

    except WebSocketDisconnect:
        manager.disconnect(user_id)
    except Exception as e:
        print(f"[WebSocket Error] {e}")
        await manager.send_error(user_id, f"错误: {str(e)}")
        manager.disconnect(user_id)
