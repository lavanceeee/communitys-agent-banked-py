from fastapi import APIRouter, Depends, Query
from app.utils.JWTutils.authentication import verify_token
from app.database import crud

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
