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
