from fastapi import FastAPI, Header, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from dotenv import load_dotenv
from app.services.agent import get_agent_response
from app.utils.context import set_request_token
from app.websocket import websocket_chat_handler

load_dotenv()
app = FastAPI()

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    user_id: str
    query: str


@app.post("/chat")
async def chat_endpoint(req: ChatRequest, authorization: Optional[str] = Header(None)):
    print("进来了")

    """
    HTTP 聊天端点（非流式）

    Args:
        req: 请求体，包含 user_id 和 query
        authorization: 请求头中的 Authorization token
    """
    # 提取 token（去掉 "Bearer " 前缀）
    token = None
    if authorization:
        # 支持 "Bearer xxx" 和直接传 "xxx" 两种格式
        if authorization.startswith("Bearer "):
            token = authorization[7:]  # 去掉 "Bearer " 前缀
        else:
            token = authorization
    else:
        print("authoation为空")

    # 将 token 设置到上下文中
    if token:
        set_request_token(token)
    else:
        print("token是空")

    # 调用业务逻辑
    answer = await get_agent_response(req.user_id, req.query)
    print(answer)
    return {"response": answer}


@app.websocket("/ws/chat/{user_id}")
async def websocket_chat_endpoint(websocket: WebSocket, user_id: str):
    """
    WebSocket 聊天端点（流式，打字机效果）

    Args:
        websocket: WebSocket 连接对象
        user_id: 用户 ID（从路径参数获取）

    消息格式:
        发送: {"query": "你的问题", "token": "your-token"}
        接收:
            - {"type": "chunk", "content": "文本片段", "is_final": false}
            - {"type": "status", "status": "thinking", "data": {...}}
            - {"type": "error", "content": "错误信息"}
    """
    await websocket_chat_handler(websocket, user_id)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
