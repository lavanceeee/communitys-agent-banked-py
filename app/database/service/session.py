from app.database.client import supabase


# 分页查询用户的会话历史
def get_sessions_paginated(user_id: str, page: int = 1, page_size: int = 10):
    # 计算分页的起始和结束索引
    # 例如：page=1, page_size=10 -> range(0, 9)
    #      page=2, page_size=10 -> range(10, 19)
    start = (page - 1) * page_size
    end = start + page_size - 1

    return (
        supabase.table("sessions")
        .select(
            "*", count="exact"
        )  # count="exact" 可以返回总共有多少条数据，方便前端做分页器
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .range(start, end)
        .execute()
    )


def create_session(user_id: int, title: str):
    return (
        supabase.table("sessions")
        .insert({"user_id": user_id, "title": title})
        .execute()
    )


def update_session_title(session_id: int, title: str):
    """更新会话标题"""
    return (
        supabase.table("sessions")
        .update({"title": title})
        .eq("id", session_id)
        .execute()
    )


def check_session_owner(session_id: int, user_id: str):
    """检查会话是否属于用户"""
    res = (
        supabase.table("sessions")
        .select("id")
        .eq("id", session_id)
        .eq("user_id", user_id)
        .execute()
    )
    return len(res.data) > 0


# 删除会话
def delete_session_service(session_id: int):
    res = supabase.table("sessions").delete().eq("id", session_id).execute()

    return len(res.data) > 0
