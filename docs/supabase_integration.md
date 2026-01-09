# Supabase 集成完整教程 🚀

## 📋 目录
1. [安装依赖](#1-安装依赖)
2. [数据库表设计](#2-数据库表设计)
3. [创建 Supabase 客户端](#3-创建-supabase-客户端)
4. [保存聊天记录](#4-保存聊天记录)
5. [查询历史记录](#5-查询历史记录)
6. [完整示例](#6-完整示例)

---

## 1. 安装依赖

```bash
pip install supabase
```

---

## 2. 数据库表设计

### 在 Supabase 控制台创建表

登录 Supabase Dashboard → SQL Editor → 执行以下 SQL：

```sql
-- 创建聊天记录表
CREATE TABLE chat_messages (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL,  -- 'user' 或 'assistant'
    content TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB  -- 存储额外信息（如 token 使用量等）
);

-- 创建索引以提高查询性能
CREATE INDEX idx_chat_messages_user_id ON chat_messages(user_id);
CREATE INDEX idx_chat_messages_created_at ON chat_messages(created_at DESC);

-- 创建用户会话表（可选）
CREATE TABLE chat_sessions (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    session_name VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 添加会话 ID 到消息表（可选）
ALTER TABLE chat_messages ADD COLUMN session_id UUID REFERENCES chat_sessions(id);
```

---

## 3. 创建 Supabase 客户端

### 文件：`app/database/supabase_client.py`

```python
"""
Supabase 数据库客户端
"""
import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")


class SupabaseClient:
    """Supabase 数据库客户端封装"""
    
    def __init__(self):
        if not SUPABASE_URL or not SUPABASE_KEY:
            raise ValueError("缺少 SUPABASE_URL 或 SUPABASE_KEY 环境变量")
        
        self.client: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    async def save_message(
        self, 
        user_id: str, 
        role: str, 
        content: str,
        session_id: str = None,
        metadata: dict = None
    ):
        """
        保存聊天消息
        
        Args:
            user_id: 用户 ID
            role: 角色 ('user' 或 'assistant')
            content: 消息内容
            session_id: 会话 ID（可选）
            metadata: 额外元数据（可选）
        
        Returns:
            保存的消息记录
        """
        data = {
            "user_id": user_id,
            "role": role,
            "content": content,
        }
        
        if session_id:
            data["session_id"] = session_id
        
        if metadata:
            data["metadata"] = metadata
        
        result = self.client.table("chat_messages").insert(data).execute()
        return result.data[0] if result.data else None
    
    async def get_user_messages(
        self, 
        user_id: str, 
        limit: int = 50,
        session_id: str = None
    ):
        """
        获取用户的聊天历史
        
        Args:
            user_id: 用户 ID
            limit: 返回消息数量限制
            session_id: 会话 ID（可选）
        
        Returns:
            消息列表
        """
        query = self.client.table("chat_messages").select("*").eq("user_id", user_id)
        
        if session_id:
            query = query.eq("session_id", session_id)
        
        result = query.order("created_at", desc=False).limit(limit).execute()
        return result.data
    
    async def create_session(self, user_id: str, session_name: str = None):
        """
        创建新的聊天会话
        
        Args:
            user_id: 用户 ID
            session_name: 会话名称
        
        Returns:
            会话记录
        """
        data = {
            "user_id": user_id,
            "session_name": session_name or f"会话 {user_id}"
        }
        
        result = self.client.table("chat_sessions").insert(data).execute()
        return result.data[0] if result.data else None
    
    async def get_user_sessions(self, user_id: str):
        """
        获取用户的所有会话
        
        Args:
            user_id: 用户 ID
        
        Returns:
            会话列表
        """
        result = self.client.table("chat_sessions").select("*").eq("user_id", user_id).order("updated_at", desc=True).execute()
        return result.data
    
    async def delete_message(self, message_id: str):
        """删除消息"""
        result = self.client.table("chat_messages").delete().eq("id", message_id).execute()
        return result.data
    
    async def clear_user_history(self, user_id: str):
        """清空用户的所有聊天记录"""
        result = self.client.table("chat_messages").delete().eq("user_id", user_id).execute()
        return result.data


# 创建全局实例
supabase_client = SupabaseClient()
```

---

## 4. 保存聊天记录

### 文件：`app/services/chat_service.py`

```python
"""
聊天服务 - 处理消息保存和检索
"""
from app.database.supabase_client import supabase_client
from app.services.agent import get_agent_response


async def chat_with_history(user_id: str, query: str, session_id: str = None):
    """
    带历史记录的聊天
    
    Args:
        user_id: 用户 ID
        query: 用户问题
        session_id: 会话 ID（可选）
    
    Returns:
        AI 的回答
    """
    # 1. 保存用户消息
    await supabase_client.save_message(
        user_id=user_id,
        role="user",
        content=query,
        session_id=session_id
    )
    
    # 2. 获取 AI 回答
    answer = await get_agent_response(user_id, query)
    
    # 3. 保存 AI 回答
    await supabase_client.save_message(
        user_id=user_id,
        role="assistant",
        content=answer,
        session_id=session_id
    )
    
    return answer


async def get_chat_history(user_id: str, limit: int = 50, session_id: str = None):
    """
    获取聊天历史
    
    Args:
        user_id: 用户 ID
        limit: 返回消息数量
        session_id: 会话 ID（可选）
    
    Returns:
        消息列表
    """
    messages = await supabase_client.get_user_messages(
        user_id=user_id,
        limit=limit,
        session_id=session_id
    )
    
    return messages
```

---

## 5. 更新 main.py

### 添加历史记录端点

```python
from fastapi import FastAPI, Header, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from dotenv import load_dotenv
from app.services.chat_service import chat_with_history, get_chat_history
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
    session_id: Optional[str] = None


@app.post("/chat")
async def chat_endpoint(req: ChatRequest, authorization: Optional[str] = Header(None)):
    """
    HTTP 聊天端点（非流式，带历史记录）
    """
    # 提取 token
    token = None
    if authorization:
        if authorization.startswith("Bearer "):
            token = authorization[7:]
        else:
            token = authorization

    # 将 token 设置到上下文中
    if token:
        set_request_token(token)

    # 调用业务逻辑（自动保存到数据库）
    answer = await chat_with_history(req.user_id, req.query, req.session_id)
    return {"response": answer}


@app.get("/chat/history/{user_id}")
async def get_history_endpoint(
    user_id: str,
    limit: int = 50,
    session_id: Optional[str] = None,
    authorization: Optional[str] = Header(None)
):
    """
    获取用户聊天历史
    
    Args:
        user_id: 用户 ID
        limit: 返回消息数量（默认 50）
        session_id: 会话 ID（可选）
    """
    messages = await get_chat_history(user_id, limit, session_id)
    return {"messages": messages}


@app.websocket("/ws/chat/{user_id}")
async def websocket_chat_endpoint(websocket: WebSocket, user_id: str):
    """WebSocket 聊天端点（流式，打字机效果）"""
    await websocket_chat_handler(websocket, user_id)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
```

---

## 6. 完整示例

### 前端调用示例

```javascript
// 1. 发送消息（自动保存到数据库）
const response = await fetch('http://localhost:8001/chat', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer your-token'
    },
    body: JSON.stringify({
        user_id: 'user123',
        query: '查询我的物业费账单',
        session_id: 'optional-session-id'  // 可选
    })
})

const data = await response.json()
console.log('AI 回答:', data.response)

// 2. 获取聊天历史
const historyResponse = await fetch('http://localhost:8001/chat/history/user123?limit=50', {
    headers: {
        'Authorization': 'Bearer your-token'
    }
})

const history = await historyResponse.json()
console.log('聊天历史:', history.messages)
```

### Vue 3 示例

```vue
<template>
  <div>
    <!-- 聊天历史 -->
    <div v-for="msg in messages" :key="msg.id" :class="msg.role">
      <strong>{{ msg.role === 'user' ? '你' : 'AI' }}:</strong>
      {{ msg.content }}
      <small>{{ formatTime(msg.created_at) }}</small>
    </div>
    
    <!-- 输入框 -->
    <input v-model="input" @keyup.enter="sendMessage">
    <button @click="sendMessage">发送</button>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const messages = ref([])
const input = ref('')
const userId = 'user123'

// 加载历史记录
onMounted(async () => {
  const response = await fetch(`http://localhost:8001/chat/history/${userId}`)
  const data = await response.json()
  messages.value = data.messages
})

// 发送消息
async function sendMessage() {
  if (!input.value.trim()) return
  
  const response = await fetch('http://localhost:8001/chat', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${localStorage.getItem('token')}`
    },
    body: JSON.stringify({
      user_id: userId,
      query: input.value
    })
  })
  
  const data = await response.json()
  
  // 添加到本地显示（也可以重新获取历史）
  messages.value.push({
    id: Date.now(),
    role: 'user',
    content: input.value,
    created_at: new Date().toISOString()
  })
  
  messages.value.push({
    id: Date.now() + 1,
    role: 'assistant',
    content: data.response,
    created_at: new Date().toISOString()
  })
  
  input.value = ''
}

function formatTime(timestamp) {
  return new Date(timestamp).toLocaleString('zh-CN')
}
</script>
```

---

## 7. 测试

### 测试脚本：`test/test_supabase.py`

```python
import asyncio
from app.database.supabase_client import supabase_client


async def test_supabase():
    """测试 Supabase 连接和操作"""
    
    # 1. 保存消息
    print("1. 保存用户消息...")
    user_msg = await supabase_client.save_message(
        user_id="test_user_123",
        role="user",
        content="你好，这是一条测试消息"
    )
    print(f"✅ 保存成功: {user_msg}")
    
    # 2. 保存 AI 回复
    print("\n2. 保存 AI 回复...")
    ai_msg = await supabase_client.save_message(
        user_id="test_user_123",
        role="assistant",
        content="你好！我是 AI 助手，很高兴为你服务。"
    )
    print(f"✅ 保存成功: {ai_msg}")
    
    # 3. 获取历史记录
    print("\n3. 获取聊天历史...")
    messages = await supabase_client.get_user_messages("test_user_123")
    print(f"✅ 找到 {len(messages)} 条消息:")
    for msg in messages:
        print(f"  - [{msg['role']}] {msg['content'][:50]}...")
    
    # 4. 创建会话
    print("\n4. 创建新会话...")
    session = await supabase_client.create_session(
        user_id="test_user_123",
        session_name="测试会话"
    )
    print(f"✅ 会话创建成功: {session}")
    
    print("\n🎉 所有测试通过！")


if __name__ == "__main__":
    asyncio.run(test_supabase())
```

运行测试：
```bash
python test/test_supabase.py
```

---

## 8. 高级功能

### 8.1 添加消息搜索

```python
async def search_messages(user_id: str, keyword: str):
    """搜索用户的消息"""
    result = supabase_client.client.table("chat_messages")\
        .select("*")\
        .eq("user_id", user_id)\
        .ilike("content", f"%{keyword}%")\
        .execute()
    return result.data
```

### 8.2 统计用户消息数量

```python
async def get_message_count(user_id: str):
    """获取用户的消息总数"""
    result = supabase_client.client.table("chat_messages")\
        .select("id", count="exact")\
        .eq("user_id", user_id)\
        .execute()
    return result.count
```

---

## 🎉 完成！

现在你已经有了：
- ✅ Supabase 数据库连接
- ✅ 自动保存聊天记录
- ✅ 查询历史记录
- ✅ 会话管理
- ✅ 完整的 API 端点

所有用户的聊天记录都会自动保存到 Supabase！🚀
