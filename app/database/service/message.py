from app.database.client import supabase


# 插入一条新消息
def save_message(session_id: int, role: str, content: str):
    """插入一条消息"""
    return (
        supabase.table("messages")
        .insert({"session_id": session_id, "role": role, "content": content})
        .execute()
    )
