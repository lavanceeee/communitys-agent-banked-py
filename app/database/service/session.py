from app.database.client import supabase


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
