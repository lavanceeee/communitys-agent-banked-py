"""
WebSocket 路由处理器
"""

from fastapi import WebSocket, WebSocketDisconnect, Query
from app.websocket.manager import manager
from app.services.agent_stream import get_agent_response_stream
from app.database.service.session import create_session, update_session_title
from app.services.title_generator import generate_title
import json
import asyncio


async def websocket_chat_handler(
    websocket: WebSocket,
    user_id: str,
    session_id: int | None = Query(None),
    already_accepted: bool = False,
):
    """
    WebSocket 聊天处理器

    Args:
        websocket: WebSocket 连接
        user_id: 已验证的用户 ID
        session_id: 会话 ID (URL 参数传入)
        already_accepted: 是否已经 accept 过连接
    """
    # 建立连接
    if not already_accepted:
        await manager.connect(websocket, user_id)
    else:
        manager.active_connections[user_id] = websocket

    try:
        while True:
            # 接收消息
            data = await websocket.receive_text()
            message = json.loads(data)

            query = message.get("query", "")
            # 优先使用消息里的 sessionId，其次使用 URL 参数的
            current_session_id = message.get("sessionId") or session_id

            if query:
                # 1. 自动创建会话逻辑 (如果没传 sessionId)
                if not current_session_id:
                    # ✅ 1.1 极速创建会话 (先用默认标题，ms级)
                    session_res = create_session(user_id, "新对话")

                    if session_res.data:
                        current_session_id = session_res.data[0]["id"]

                        # ✅ 1.2 立即通知前端 (前端拿到 ID 可以更新 URL)
                        await manager.send_message(
                            user_id,
                            {
                                "type": "session_created",
                                "data": {
                                    "sessionId": current_session_id,
                                    "title": "新对话",
                                },
                            },
                        )

                        # ✅ 1.3 后台异步生成真正标题 (不阻塞回复)
                        asyncio.create_task(
                            _bg_generate_title(current_session_id, query, user_id)
                        )
                    else:
                        await manager.send_error(user_id, "创建会话失败")
                        continue

                # ✅ 2. 立即开始流式响应 (此时已有 sessionId)
                await get_agent_response_stream(user_id, current_session_id, query)

    except WebSocketDisconnect:
        manager.disconnect(user_id)
    except Exception as e:
        print(f"[WebSocket Error] {e}")
        await manager.send_error(user_id, f"错误: {str(e)}")
        manager.disconnect(user_id)


async def _bg_generate_title(session_id: int, content: str, user_id: str):
    """后台任务：生成并更新标题"""
    try:
        # 调用 LLM 生成标题
        new_title = await generate_title(content)

        # 更新数据库
        update_session_title(session_id, new_title)

        # 再次通知前端更新标题
        await manager.send_message(
            user_id,
            {
                "type": "session_updated",
                "data": {"sessionId": session_id, "title": new_title},
            },
        )
    except Exception as e:
        print(f"后台生成标题失败: {e}")
