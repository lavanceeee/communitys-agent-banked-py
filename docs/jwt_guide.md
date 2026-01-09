# JWT Token 解析教程 🔐

## 1. 安装依赖

```bash
pip install pyjwt
```

---

## 2. JWT 工具类

### 文件：`app/utils/jwt_helper.py`

```python
"""
JWT Token 解析工具
"""
import jwt
from typing import Optional, Dict
from fastapi import HTTPException, status


class JWTHelper:
    """JWT Token 处理工具类"""
    
    def __init__(self, secret_key: str = None, algorithm: str = "HS256"):
        """
        初始化 JWT Helper
        
        Args:
            secret_key: JWT 密钥（如果验证签名需要）
            algorithm: 加密算法
        """
        self.secret_key = secret_key
        self.algorithm = algorithm
    
    def decode_token(self, token: str, verify: bool = False) -> Dict:
        """
        解码 JWT Token
        
        Args:
            token: JWT token 字符串
            verify: 是否验证签名（需要 secret_key）
        
        Returns:
            解码后的 payload 字典
        
        Raises:
            HTTPException: Token 无效或过期
        """
        try:
            if verify and not self.secret_key:
                raise ValueError("验证签名需要提供 secret_key")
            
            # 解码 token
            options = {"verify_signature": verify}
            payload = jwt.decode(
                token,
                self.secret_key if verify else None,
                algorithms=[self.algorithm],
                options=options
            )
            
            return payload
            
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token 已过期"
            )
        except jwt.InvalidTokenError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"无效的 Token: {str(e)}"
            )
    
    def get_user_id(self, token: str, user_id_field: str = "sub") -> str:
        """
        从 Token 中提取用户 ID
        
        Args:
            token: JWT token 字符串
            user_id_field: 用户 ID 在 payload 中的字段名
                          常见值: "sub", "user_id", "id", "userId"
        
        Returns:
            用户 ID
        """
        payload = self.decode_token(token, verify=False)
        
        # 尝试多个可能的字段名
        possible_fields = [user_id_field, "sub", "user_id", "id", "userId"]
        
        for field in possible_fields:
            if field in payload:
                return str(payload[field])
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token 中未找到用户 ID（尝试的字段: {possible_fields}）"
        )
    
    def get_payload_field(self, token: str, field: str, default=None):
        """
        从 Token 中获取指定字段
        
        Args:
            token: JWT token 字符串
            field: 字段名
            default: 默认值
        
        Returns:
            字段值或默认值
        """
        payload = self.decode_token(token, verify=False)
        return payload.get(field, default)


# 创建全局实例（不验证签名）
jwt_helper = JWTHelper()

# 如果需要验证签名，使用这个（需要配置 JWT_SECRET）
# from dotenv import load_dotenv
# import os
# load_dotenv()
# jwt_helper_verified = JWTHelper(secret_key=os.getenv("JWT_SECRET"))
```

---

## 3. 更新 main.py - 自动从 Token 提取用户 ID

```python
from fastapi import FastAPI, Header, WebSocket, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from dotenv import load_dotenv
from app.services.agent import get_agent_response
from app.utils.context import set_request_token
from app.utils.jwt_helper import jwt_helper
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
    query: str
    # user_id 不再需要从前端传，从 token 中提取


def get_current_user_id(authorization: Optional[str] = Header(None)) -> str:
    """
    依赖注入：从 Authorization header 中提取用户 ID
    
    Args:
        authorization: Authorization header
    
    Returns:
        用户 ID
    
    Raises:
        HTTPException: 如果 token 无效或缺失
    """
    if not authorization:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="缺少 Authorization header"
        )
    
    # 去掉 "Bearer " 前缀
    token = authorization
    if authorization.startswith("Bearer "):
        token = authorization[7:]
    
    # 从 token 中提取用户 ID
    user_id = jwt_helper.get_user_id(token)
    
    # 同时设置 token 到上下文（用于后续 API 调用）
    set_request_token(token)
    
    return user_id


@app.post("/chat")
async def chat_endpoint(
    req: ChatRequest,
    user_id: str = Depends(get_current_user_id)
):
    """
    HTTP 聊天端点（非流式）
    
    用户 ID 自动从 JWT token 中提取，前端不需要传递
    """
    # 调用业务逻辑
    answer = await get_agent_response(user_id, req.query)
    return {"response": answer, "user_id": user_id}


@app.get("/me")
async def get_current_user(user_id: str = Depends(get_current_user_id)):
    """
    获取当前用户信息（测试端点）
    """
    return {"user_id": user_id, "message": "Token 解析成功"}


@app.websocket("/ws/chat")
async def websocket_chat_endpoint(websocket: WebSocket):
    """
    WebSocket 聊天端点
    
    注意：WebSocket 的 token 需要在连接后通过消息传递
    """
    await websocket.accept()
    
    try:
        # 第一条消息应该包含 token
        data = await websocket.receive_json()
        token = data.get("token")
        
        if not token:
            await websocket.send_json({
                "type": "error",
                "content": "缺少 token"
            })
            await websocket.close()
            return
        
        # 从 token 中提取用户 ID
        try:
            user_id = jwt_helper.get_user_id(token)
            set_request_token(token)
        except Exception as e:
            await websocket.send_json({
                "type": "error",
                "content": f"Token 无效: {str(e)}"
            })
            await websocket.close()
            return
        
        # 发送欢迎消息
        await websocket.send_json({
            "type": "status",
            "status": "connected",
            "data": {"user_id": user_id, "message": "连接成功"}
        })
        
        # 处理后续消息
        await websocket_chat_handler(websocket, user_id)
        
    except Exception as e:
        print(f"WebSocket 错误: {e}")
        await websocket.close()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
```

---

## 4. 前端使用示例

### 4.1 HTTP 请求（不需要传 user_id）

```javascript
// ✅ 新方式：只需要传 token，user_id 自动提取
const response = await fetch('http://localhost:8001/chat', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${yourJwtToken}`  // 👈 只需要这个
    },
    body: JSON.stringify({
        query: '查询我的物业费账单'
        // user_id 不需要传了！
    })
})

const data = await response.json()
console.log('AI 回答:', data.response)
console.log('用户 ID:', data.user_id)  // 后端返回的用户 ID
```

### 4.2 测试 Token 解析

```javascript
// 测试端点：验证 token 是否有效
const response = await fetch('http://localhost:8001/me', {
    headers: {
        'Authorization': `Bearer ${yourJwtToken}`
    }
})

const data = await response.json()
console.log('当前用户:', data.user_id)
```

### 4.3 WebSocket（需要在首次消息中传 token）

```javascript
const ws = new WebSocket('ws://localhost:8001/ws/chat')

ws.onopen = () => {
    // 第一条消息：发送 token
    ws.send(JSON.stringify({
        token: yourJwtToken
    }))
}

ws.onmessage = (event) => {
    const data = JSON.parse(event.data)
    
    if (data.type === 'status' && data.status === 'connected') {
        console.log('✅ 连接成功，用户 ID:', data.data.user_id)
        
        // 现在可以发送查询了
        ws.send(JSON.stringify({
            query: '查询我的物业费账单'
        }))
    }
}
```

---

## 5. JWT Payload 示例

### 常见的 JWT Payload 结构

```json
{
  "sub": "user_123456",          // 标准字段：subject（用户 ID）
  "user_id": "user_123456",      // 自定义字段
  "email": "user@example.com",
  "name": "张三",
  "role": "user",
  "iat": 1704844800,             // issued at（签发时间）
  "exp": 1704931200              // expiration（过期时间）
}
```

### 工具类会自动尝试这些字段：
1. `sub`（JWT 标准字段）
2. `user_id`
3. `id`
4. `userId`

---

## 6. 调试工具

### 查看 Token 内容（不验证签名）

```python
from app.utils.jwt_helper import jwt_helper

# 解码 token 查看内容
token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
payload = jwt_helper.decode_token(token)
print("Token 内容:", payload)

# 提取用户 ID
user_id = jwt_helper.get_user_id(token)
print("用户 ID:", user_id)

# 获取其他字段
email = jwt_helper.get_payload_field(token, "email")
print("邮箱:", email)
```

### 在线 JWT 解码工具
访问 [jwt.io](https://jwt.io) 粘贴你的 token 查看内容

---

## 7. 安全建议

### 7.1 生产环境应该验证签名

```python
# .env 文件
JWT_SECRET=your-secret-key-here

# 使用验证签名的版本
from app.utils.jwt_helper import JWTHelper
import os

jwt_helper_verified = JWTHelper(
    secret_key=os.getenv("JWT_SECRET"),
    algorithm="HS256"
)

# 解码并验证
payload = jwt_helper_verified.decode_token(token, verify=True)
```

### 7.2 处理过期 Token

```python
try:
    user_id = jwt_helper.get_user_id(token)
except HTTPException as e:
    if e.status_code == 401:
        # Token 过期或无效，提示用户重新登录
        return {"error": "请重新登录"}
```

---

## 8. 完整测试

### 测试脚本：`test/test_jwt.py`

```python
"""测试 JWT 解析"""
from app.utils.jwt_helper import jwt_helper

# 示例 token（这是一个示例，实际使用你的真实 token）
sample_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyXzEyMzQ1NiIsImVtYWlsIjoidXNlckBleGFtcGxlLmNvbSIsIm5hbWUiOiLlvKDkuIkiLCJpYXQiOjE3MDQ4NDQ4MDAsImV4cCI6MTcwNDkzMTIwMH0.xyz"

try:
    # 1. 解码 token
    print("1. 解码 Token...")
    payload = jwt_helper.decode_token(sample_token)
    print(f"✅ Payload: {payload}")
    
    # 2. 提取用户 ID
    print("\n2. 提取用户 ID...")
    user_id = jwt_helper.get_user_id(sample_token)
    print(f"✅ 用户 ID: {user_id}")
    
    # 3. 获取其他字段
    print("\n3. 获取其他字段...")
    email = jwt_helper.get_payload_field(sample_token, "email")
    name = jwt_helper.get_payload_field(sample_token, "name")
    print(f"✅ 邮箱: {email}")
    print(f"✅ 姓名: {name}")
    
    print("\n🎉 所有测试通过！")
    
except Exception as e:
    print(f"❌ 错误: {e}")
```

---

## 🎉 总结

现在你可以：
- ✅ 从 JWT token 中自动提取用户 ID
- ✅ 前端不需要传递 `user_id`，更安全
- ✅ 支持多种 JWT payload 格式
- ✅ 自动处理 token 验证和错误

**使用方式：**
```javascript
// 前端只需要传 token
fetch('/chat', {
    headers: { 'Authorization': `Bearer ${token}` },
    body: JSON.stringify({ query: '你的问题' })
})
```

后端自动从 token 中提取 `user_id`！🚀
