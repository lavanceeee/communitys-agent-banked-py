"""
WebSocket 路由处理器
"""

from fastapi import WebSocket, WebSocketDisconnect
from app.websocket.manager import manager
from app.services.agent_stream import get_agent_response_stream
from app.utils.context import set_request_token
import json


async def websocket_chat_handler(websocket: WebSocket, user_id: str):
    """
    WebSocket 聊天处理器

    Args:
        websocket: WebSocket 连接
        user_id: 用户 ID（从路径参数获取）
    """
    # 接受连接
    await manager.connect(websocket, user_id)

    try:
        while True:
            # 接收消息
            data = await websocket.receive_text()
            message = json.loads(data)

            # 提取消息内容
            query = message.get("query", "")
            token = message.get("token", "")

            # 设置 token 到上下文
            if token:
                set_request_token(token)

            # 处理消息
            if query:
                # 流式处理并发送响应
                await get_agent_response_stream(user_id, query)
            else:
                await manager.send_error(user_id, "查询内容不能为空")

    except WebSocketDisconnect:
        print(f"[WebSocket] User {user_id} disconnected")
        manager.disconnect(user_id)
    except Exception as e:
        print(f"[WebSocket Error] {e}")
        await manager.send_error(user_id, f"服务器错误: {str(e)}")
        manager.disconnect(user_id)
