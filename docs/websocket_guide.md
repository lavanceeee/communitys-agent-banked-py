# WebSocket 极简使用教程 🚀

## 📝 3 步快速开始

### 1️⃣ 启动服务器

```bash
python main.py
```

服务器会在 `http://localhost:8001` 启动

### 2️⃣ 打开测试页面

直接用浏览器打开：
```
test/websocket_test.html
```

### 3️⃣ 开始聊天！

输入问题，按回车或点击发送，就能看到打字机效果了！✨

---

## 💻 前端代码示例

### 最简单的 JavaScript 代码（20 行）

```javascript
// 1. 连接 WebSocket
const ws = new WebSocket('ws://localhost:8001/ws/chat/user123');

// 2. 监听消息
ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    
    if (data.type === 'chunk') {
        // 打字机效果：逐字显示
        console.log(data.content);
    }
};

// 3. 发送消息
function sendMessage(text) {
    ws.send(JSON.stringify({
        query: text,
        token: 'your-token-here'  // 可选
    }));
}

// 使用
sendMessage('查询我的物业费账单');
```

---

## 🔌 WebSocket 地址格式

```
ws://localhost:8001/ws/chat/{user_id}
```

- `user_id`: 用户 ID（路径参数）

---

## 📤 发送消息格式

```json
{
    "query": "你的问题",
    "token": "your-token-here"
}
```

---

## 📥 接收消息格式

### 1. 文本片段（打字机效果）
```json
{
    "type": "chunk",
    "content": "这是一段文本",
    "is_final": false
}
```

### 2. 状态消息
```json
{
    "type": "status",
    "status": "thinking",
    "data": {
        "message": "正在思考..."
    }
}
```

状态类型：
- `thinking` - 正在思考
- `tool_calling` - 正在调用工具
- `tool_completed` - 工具执行完成
- `completed` - 回答完成

### 3. 错误消息
```json
{
    "type": "error",
    "content": "错误信息"
}
```

---

## 🎯 Vue 3 示例

```vue
<template>
  <div>
    <div v-for="msg in messages" :key="msg.id">
      {{ msg.content }}
    </div>
    <input v-model="input" @keyup.enter="send">
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const ws = ref(null)
const messages = ref([])
const input = ref('')
let currentMessage = null

onMounted(() => {
  // 连接
  ws.value = new WebSocket('ws://localhost:8001/ws/chat/user123')
  
  // 接收消息
  ws.value.onmessage = (event) => {
    const data = JSON.parse(event.data)
    
    if (data.type === 'chunk') {
      if (!currentMessage) {
        currentMessage = { id: Date.now(), content: '' }
        messages.value.push(currentMessage)
      }
      currentMessage.content += data.content
      
      if (data.is_final) {
        currentMessage = null
      }
    }
  }
})

function send() {
  ws.value.send(JSON.stringify({
    query: input.value,
    token: localStorage.getItem('token')
  }))
  input.value = ''
}
</script>
```

---

## 🎨 React 示例

```jsx
import { useState, useEffect, useRef } from 'react'

function Chat() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const ws = useRef(null)
  const currentMsg = useRef(null)

  useEffect(() => {
    // 连接
    ws.current = new WebSocket('ws://localhost:8001/ws/chat/user123')
    
    // 接收消息
    ws.current.onmessage = (event) => {
      const data = JSON.parse(event.data)
      
      if (data.type === 'chunk') {
        if (!currentMsg.current) {
          currentMsg.current = { id: Date.now(), content: '' }
          setMessages(prev => [...prev, currentMsg.current])
        }
        
        currentMsg.current.content += data.content
        setMessages(prev => [...prev])
        
        if (data.is_final) {
          currentMsg.current = null
        }
      }
    }
  }, [])

  const send = () => {
    ws.current.send(JSON.stringify({
      query: input,
      token: localStorage.getItem('token')
    }))
    setInput('')
  }

  return (
    <div>
      {messages.map(msg => (
        <div key={msg.id}>{msg.content}</div>
      ))}
      <input 
        value={input} 
        onChange={e => setInput(e.target.value)}
        onKeyPress={e => e.key === 'Enter' && send()}
      />
    </div>
  )
}
```

---

## 🐛 调试技巧

### 1. 查看 WebSocket 连接状态
```javascript
console.log(ws.readyState)
// 0: CONNECTING
// 1: OPEN
// 2: CLOSING
// 3: CLOSED
```

### 2. 查看所有消息
```javascript
ws.onmessage = (event) => {
    console.log('收到消息:', event.data)
    const data = JSON.parse(event.data)
    console.log('解析后:', data)
}
```

### 3. 错误处理
```javascript
ws.onerror = (error) => {
    console.error('WebSocket 错误:', error)
}

ws.onclose = () => {
    console.log('连接已关闭')
}
```

---

## ⚡ 常见问题

### Q: 连接失败怎么办？
A: 检查：
1. 后端服务是否启动（`python main.py`）
2. 地址是否正确（`ws://localhost:8001/ws/chat/user123`）
3. 浏览器控制台是否有错误

### Q: 收不到消息？
A: 检查：
1. `ws.onmessage` 是否正确设置
2. 发送的消息格式是否正确
3. 后端是否有报错（查看终端）

### Q: 如何断开重连？
```javascript
function reconnect() {
    if (ws) ws.close()
    ws = new WebSocket('ws://localhost:8001/ws/chat/user123')
}
```

---

## 🎉 完成！

现在你已经掌握了 WebSocket 的基本用法！

试试发送：
- "查询我的物业费账单"
- "帮我查一下停车记录"
- "我想报修"

享受打字机效果吧！✨
