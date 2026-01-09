# Token 传递流程说明

## 📋 完整流程

```
前端请求
  ↓
  Headers: { Authorization: "Bearer xxx" }
  Body: { user_id: "123", query: "查询账单" }
  ↓
FastAPI 端点 (main.py)
  ↓
  提取 Authorization header
  ↓
  调用 set_request_token(token)
  ↓
  存储到 ContextVar (线程安全)
  ↓
Agent Service (agent.py)
  ↓
  调用 LangChain Tools
  ↓
Bills Tool (bills_tools.py)
  ↓
  调用 http_client.get()
  ↓
HttpClient (http_client.py)
  ↓
  调用 get_request_token() 从上下文获取 token
  ↓
  自动添加到请求头: { Authorization: "Bearer xxx" }
  ↓
发送到后端 API
  ↓
后端 API 验证 token 并返回数据
```

## 🔑 关键组件

### 1. Context Manager (`app/utils/context.py`)
- 使用 `contextvars.ContextVar` 存储 token
- 线程安全，支持异步
- 每个请求有独立的上下文

### 2. HTTP Client (`app/utils/http_client.py`)
- `_prepare_headers()` 方法自动从上下文获取 token
- 所有 HTTP 方法（GET/POST/PUT/DELETE）都自动添加 token
- 支持手动传入额外的 headers

### 3. FastAPI 端点 (`main.py`)
- 使用 `Header` 依赖注入获取 Authorization
- 支持两种格式：
  - `Bearer xxx`（标准格式）
  - `xxx`（直接传 token）
- 在调用 agent 前设置到上下文

## 💡 使用示例

### 前端发送请求

```javascript
// 方式 1: 标准 Bearer 格式
fetch('http://localhost:8001/chat', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...'
  },
  body: JSON.stringify({
    user_id: 'user123',
    query: '查询我的物业费账单'
  })
})

// 方式 2: 直接传 token
fetch('http://localhost:8001/chat', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...'
  },
  body: JSON.stringify({
    user_id: 'user123',
    query: '查询我的物业费账单'
  })
})
```

### Tool 中使用（自动添加 token）

```python
from app.utils.http_client import http_client

@tool
async def query_unpaid_bills(userId: str):
    # http_client 会自动从上下文获取 token 并添加到请求头
    data = await http_client.get("/api/property-fee/bills", params={"userId": userId})
    return json.dumps(data, ensure_ascii=False)
```

## 🎯 优势

1. **自动化**: Tool 开发者无需手动处理 token
2. **安全**: 使用 ContextVar，每个请求的 token 相互隔离
3. **灵活**: 支持多种 token 格式
4. **简洁**: 一行代码即可发送带认证的请求

## 🔍 调试技巧

### 查看 token 是否正确传递

在 `http_client.py` 的 `_prepare_headers` 方法中添加日志：

```python
def _prepare_headers(self, headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    token = get_request_token()
    print(f"[DEBUG] Token from context: {token}")  # 调试日志
    
    final_headers = headers.copy() if headers else {}
    if token:
        final_headers['Authorization'] = f'Bearer {token}'
        print(f"[DEBUG] Final headers: {final_headers}")  # 调试日志
    
    return final_headers
```

## ⚠️ 注意事项

1. **Token 格式**: 后端 API 需要支持 `Bearer xxx` 格式的 Authorization header
2. **上下文生命周期**: ContextVar 的值在请求结束后会被清理
3. **错误处理**: 如果后端返回 401，说明 token 无效或已过期
