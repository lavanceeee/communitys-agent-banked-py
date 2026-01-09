from fastapi import APIRouter, Depends
from app.utils.JWTutils.authentication import verify_token

router = APIRouter(prefix="/session", tags=["会话"])


@router.post("/history")
async def get_session_history(user_id: str = Depends(verify_token)):
    """获取聊天历史"""

    # user_id 已经从 token 中提取了
    print(f"用户 ID: {user_id}")

    return {"code": 200, "message": "获取成功", "data": {"user_id": user_id}}
