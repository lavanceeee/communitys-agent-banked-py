from fastapi import APIRouter, WebSocket
from app.websocket import websocket_chat_handler
from app.utils.JWTutils.jwt_helper import get_user_id
import json

router = APIRouter(tags=["对话"])


@router.websocket("/ws/chat")
async def websocket_chat_endpoint(websocket: WebSocket):
    """
    WebSocket 聊天端点

    前端发送: { type: 'auth', token: 'xxx' }
    """
    await websocket.accept()

    try:
        # 接收第一条消息（认证消息）
        data = await websocket.receive_text()
        message = json.loads(data)

        # 提取 token
        token = message.get("token", "")

        if not token:
            await websocket.send_json({"type": "error", "content": "缺少 token"})
            await websocket.close()
            return

        # 验证 token
        try:
            user_id = get_user_id(token)
            # 设置 token 到上下文（供 http_client 使用）
            from app.utils.context import set_request_token

            set_request_token(token)
        except Exception as e:
            print(f"验证失败: {e}")
            await websocket.send_json(
                {"type": "error", "content": f"Token 验证失败: {str(e)}"}
            )
            await websocket.close()
            return

        # 验证成功
        await websocket.send_json({"type": "auth_success", "user_id": user_id})

        # 处理后续消息（已经 accept 过了）
        await websocket_chat_handler(websocket, user_id, already_accepted=True)

    except Exception as e:
        print(f"WebSocket 错误: {e}")
        try:
            await websocket.close()
        except:
            pass
