from app.database.client import supabase


# 插入一条新消息
def save_message(session_id: int, role: str, content: str):
    """插入一条消息"""
    return (
        supabase.table("messages")
        .insert({"session_id": session_id, "role": role, "content": content})
        .execute()
    )


# 获取历史聊天记录
def get_messages(session_id: int):
    return (
        supabase.table("messages")
        .select("*")
        .eq("session_id", session_id)
        .order("created_at", desc=False)
        .execute()
    )


# 删除session_id的所有消息
def delete_messages(session_id: int):
    return supabase.table("messages").delete().eq("session_id", session_id).execute()
