from fastapi import APIRouter, Depends, Query
from app.utils.JWTutils.authentication import verify_token
from app.database import crud
from app.database.service.session import create_session
from app.services.title_generator import generate_title
from pydantic import BaseModel

router = APIRouter(tags=["会话"])


@router.get("/sessions")
async def get_session_history(
    user_id: str = Depends(verify_token),
    page: int = Query(1, ge=1, description="当前页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页条数"),
):
    """获取聊天历史"""

    print(f"用户 ID: {user_id}")

    try:
        result = crud.get_sessions_paginated(user_id, page, page_size)

        print(f"---获取历史记录成功，{result}----")

        # RestFul API
        return {
            "code": 200,
            "message": "获取成功",
            "data": {
                "items": result.data,  # 具体的会话列表
                "total": result.count,  # 总条数
                "page": page,
                "page_size": page_size,
            },
        }
    except Exception as e:
        return {
            "code": 500,
            "message": f"获取失败，{e}",
            "data": None,
        }


class NewSessionRequest(BaseModel):
    content: str  # 用户发的第一句话
    title: str = "新对话"  # 默认标题


@router.post("/create_new_session")
async def create_new_session(
    data: NewSessionRequest, user_id: int = Depends(verify_token)
):
    """
    新建会话接口：
    1. 在 sessions 表创建一个新 ID
    2. 在 messages 表存入用户的第一条消息
    """
    try:
        # 生成标题
        title = await generate_title(data.content)

        # 1. 创建 Session 记录
        session_res = create_session(user_id, title)

        if not session_res.data:
            return {"code": 500, "message": "创建会话记录失败", "data": None}

        new_session_id = session_res.data[0]["id"]

        # 3. 返回给前端
        return {
            "code": 200,
            "message": "会话创建成功",
            "data": {
                "sessionId": new_session_id,
                "title": title,
            },
        }

    except Exception as e:
        return {"code": 500, "message": f"服务器内部错误: {str(e)}", "data": None}
