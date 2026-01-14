import sqlite3
from langgraph.checkpoint.sqlite import SqliteSaver
import os

# SQLite 数据库文件路径
DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "checkpoints.db"
)

# 创建连接 (check_same_thread=False 允许跨线程使用，适配 FastAPI)
conn = sqlite3.connect(DB_PATH, check_same_thread=False)

# 使用同步 SqliteSaver (最稳定方案)
checkpointer = SqliteSaver(conn)


async def init_checkpointer():
    """兼容性占位符"""
    return checkpointer


async def close_checkpointer():
    """关闭数据库连接"""
    conn.close()
