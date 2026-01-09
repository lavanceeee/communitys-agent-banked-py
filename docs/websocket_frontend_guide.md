# WebSocket 前端使用指南 🚀

## 核心概念

**WebSocket ≠ HTTP**

- ❌ HTTP: 请求 → 等待 → 一次性返回完整响应
- ✅ WebSocket: 建立连接 → 持续接收数据流 → 打字机效果

---

## 📝 最简单的例子（20行代码）

```javascript
// 1. 建立连接
const ws = new WebSocket('ws://localhost:8001/ws/chat/user123')

// 2. 连接成功
ws.onopen = () => {
    console.log('✅ 连接成功')
    
    // 发送问题
    ws.send(JSON.stringify({
        query: '查询我的物业费账单',
        token: 'your-token-here'
    }))
}

// 3. 接收消息（打字机效果）
let fullResponse = ''

ws.onmessage = (event) => {
    const data = JSON.parse(event.data)
    
    if (data.type === 'chunk') {
        // 逐字追加
        fullResponse += data.content
        console.log('当前内容:', fullResponse)
        
        if (data.is_final) {
            console.log('✅ 完成！最终结果:', fullResponse)
        }
    }
}
```

---

## 🎯 Vue 3 完整示例

```vue
<template>
  <div class="chat-container">
    <!-- 消息显示区 -->
    <div class="messages">
      <div v-for="msg in messages" :key="msg.id" class="message">
        {{ msg.content }}
      </div>
    </div>
    
    <!-- 输入框 -->
    <div class="input-area">
      <input 
        v-model="input" 
        @keyup.enter="sendMessage"
        placeholder="输入你的问题..."
      >
      <button @click="sendMessage">发送</button>
    </div>
    
    <!-- 状态提示 -->
    <div v-if="status" class="status">{{ status }}</div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

const ws = ref(null)
const messages = ref([])
const input = ref('')
const status = ref('')
let currentMessage = null

onMounted(() => {
  // 建立 WebSocket 连接
  ws.value = new WebSocket('ws://localhost:8001/ws/chat/user123')
  
  ws.value.onopen = () => {
    console.log('✅ WebSocket 连接成功')
  }
  
  ws.value.onmessage = (event) => {
    const data = JSON.parse(event.data)
    
    switch(data.type) {
      case 'chunk':
        // 文本片段 - 打字机效果
        if (!currentMessage) {
          currentMessage = { id: Date.now(), content: '' }
          messages.value.push(currentMessage)
        }
        
        currentMessage.content += data.content
        
        if (data.is_final) {
          currentMessage = null
          status.value = ''
        }
        break
        
      case 'status':
        // 状态消息
        status.value = data.data.message || data.status
        break
        
      case 'error':
        // 错误消息
        alert('错误: ' + data.content)
        status.value = ''
        break
    }
  }
  
  ws.value.onerror = (error) => {
    console.error('❌ WebSocket 错误:', error)
  }
  
  ws.value.onclose = () => {
    console.log('🔌 WebSocket 连接已关闭')
  }
})

onUnmounted(() => {
  // 组件销毁时关闭连接
  if (ws.value) {
    ws.value.close()
  }
})

function sendMessage() {
  if (!input.value.trim()) return
  
  // 添加用户消息
  messages.value.push({
    id: Date.now(),
    content: '👤 ' + input.value
  })
  
  // 发送到服务器
  ws.value.send(JSON.stringify({
    query: input.value,
    token: localStorage.getItem('token') || ''
  }))
  
  input.value = ''
}
</script>

<style scoped>
.chat-container {
  max-width: 600px;
  margin: 0 auto;
  padding: 20px;
}

.messages {
  height: 400px;
  overflow-y: auto;
  border: 1px solid #ddd;
  padding: 10px;
  margin-bottom: 10px;
}

.message {
  margin-bottom: 10px;
  padding: 8px;
  background: #f5f5f5;
  border-radius: 5px;
}

.input-area {
  display: flex;
  gap: 10px;
}

input {
  flex: 1;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 5px;
}

button {
  padding: 10px 20px;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 5px;
  cursor: pointer;
}

.status {
  margin-top: 10px;
  padding: 8px;
  background: #fff3cd;
  border-radius: 5px;
  text-align: center;
}
</style>
```

---

## 📊 消息类型详解

### 1. 文本片段（chunk）

```json
{
  "type": "chunk",
  "content": "你好",
  "is_final": false
}
```

**处理方式：**
```javascript
if (data.type === 'chunk') {
    // 追加到当前消息
    currentMessage.content += data.content
    
    if (data.is_final) {
        // 这是最后一个片段
        console.log('回答完成')
    }
}
```

### 2. 状态消息（status）

```json
{
  "type": "status",
  "status": "thinking",
  "data": {
    "message": "正在思考..."
  }
}
```

**状态类型：**
- `thinking` - 正在思考
- `tool_calling` - 正在调用工具
- `tool_completed` - 工具执行完成
- `completed` - 回答完成

### 3. 错误消息（error）

```json
{
  "type": "error",
  "content": "查询失败: 网络错误"
}
```

---

## 🔄 完整的数据流

```
用户输入 "查询账单"
    ↓
前端: ws.send({ query: "查询账单" })
    ↓
后端: 收到请求
    ↓
后端: ws.send({ type: "status", status: "thinking" })
    ↓
前端: 显示 "正在思考..."
    ↓
后端: ws.send({ type: "chunk", content: "你" })
    ↓
前端: 显示 "你"
    ↓
后端: ws.send({ type: "chunk", content: "的" })
    ↓
前端: 显示 "你的"
    ↓
后端: ws.send({ type: "chunk", content: "账单", is_final: true })
    ↓
前端: 显示 "你的账单" + 完成标记
```

---

## ⚠️ 常见错误

### ❌ 错误 1: 期望 return 返回数据

```javascript
// ❌ 错误
const response = await fetch('ws://...')  // WebSocket 不是 HTTP！
```

```javascript
// ✅ 正确
const ws = new WebSocket('ws://...')
ws.onmessage = (event) => {
    // 通过事件接收数据
}
```

### ❌ 错误 2: 不处理分片

```javascript
// ❌ 错误 - 只显示最后一个片段
ws.onmessage = (event) => {
    const data = JSON.parse(event.data)
    display.textContent = data.content  // 会被覆盖！
}
```

```javascript
// ✅ 正确 - 累加所有片段
let fullText = ''
ws.onmessage = (event) => {
    const data = JSON.parse(event.data)
    if (data.type === 'chunk') {
        fullText += data.content  // 累加
        display.textContent = fullText
    }
}
```

---

## 🎉 总结

| 特性 | HTTP | WebSocket |
|------|------|-----------|
| 连接 | 一次性 | 持久连接 |
| 数据流 | 单向（请求→响应） | 双向（实时推送） |
| 接收方式 | `await fetch()` | `ws.onmessage` |
| 适用场景 | 普通请求 | 实时聊天、打字机效果 |

**记住：WebSocket 是通过 `onmessage` 事件接收数据，不是通过 return！** ✨
