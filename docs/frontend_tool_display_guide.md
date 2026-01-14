# 前端工具映射显示指南

## 📋 概述

本文档面向前端开发者，说明如何接收和展示 AI Agent 工具调用的友好界面。

后端已实现工具元数据映射系统，当 AI 调用工具时，会通过 WebSocket 发送包含中文名称、图标、分类等信息的消息，前端可以据此展示用户友好的 UI。

---

## 🔌 WebSocket 连接

### 1. 连接地址
```
ws://localhost:8001/ws/chat?session_id=123
```

### 2. 认证流程
```typescript
// 建立连接
const ws = new WebSocket('ws://localhost:8001/ws/chat');

// 连接成功后发送认证消息
ws.onopen = () => {
  ws.send(JSON.stringify({
    type: 'auth',
    token: 'your_jwt_token_here'
  }));
};

// 接收认证结果
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  if (data.type === 'auth_success') {
    console.log('认证成功，用户ID:', data.user_id);
    // 可以开始发送对话消息
  }
};
```

---

## 📨 消息格式

### 发送消息（前端 → 后端）

```typescript
ws.send(JSON.stringify({
  query: "我有哪些待缴费用？",
  sessionId: 123  // 可选，不传则自动创建新会话
}));
```

---

### 接收消息（后端 → 前端）

后端会发送以下 5 种类型的消息：

---

#### 1️⃣ 状态消息 - 思考中
```json
{
  "type": "status",
  "status": "thinking",
  "data": {
    "message": "正在思考..."
  }
}
```

---

#### 2️⃣ 状态消息 - 工具调用开始 ⭐
```json
{
  "type": "status",
  "status": "tool_calling",
  "data": {
    "tool": "query_unpaid_bills",           // 工具函数名（内部标识）
    "display_name": "查询未支付账单",        // 👈 显示这个
    "message": "正在查询未支付的账单",       // 👈 或显示这个
    "icon": "bill",                         // 👈 图标标识
    "category": "bill"                      // 👈 分类
  }
}
```

**前端显示建议：**
```
📄 查询未支付账单
   正在查询未支付的账单... ⏳
```

---

#### 3️⃣ 状态消息 - 工具调用完成 ⭐
```json
{
  "type": "status",
  "status": "tool_completed",
  "data": {
    "tool": "query_unpaid_bills",
    "display_name": "查询未支付账单",
    "message": "查询未支付账单执行完成",
    "icon": "bill",
    "category": "bill"
  }
}
```

**前端显示建议：**
```
📄 查询未支付账单
   执行完成 ✅
```

---

#### 4️⃣ 文本片段 - 流式输出
```json
{
  "type": "chunk",
  "content": "您",                    // 单个字符或词组
  "is_final": false                  // 是否是最后一个片段
}
```

最后一个片段：
```json
{
  "type": "chunk",
  "content": "",
  "is_final": true                   // 标识流式输出结束
}
```

---

#### 5️⃣ 状态消息 - 完成
```json
{
  "type": "status",
  "status": "completed",
  "data": {
    "message": "回答完成"
  }
}
```

---

#### 6️⃣ 错误消息
```json
{
  "type": "error",
  "content": "错误信息描述"
}
```

---

#### 7️⃣ 会话创建通知
```json
{
  "type": "session_created",
  "data": {
    "sessionId": 456,
    "title": "新对话"
  }
}
```

---

#### 8️⃣ 会话标题更新
```json
{
  "type": "session_updated",
  "data": {
    "sessionId": 456,
    "title": "查询账单相关问题"    // AI 自动生成的标题
  }
}
```

---

## 🎨 工具图标映射

### 图标标识对照表

| icon 值 | 含义 | 推荐图标库 |
|---------|------|-----------|
| `notification` | 通知 | 🔔 Bell |
| `bill` | 账单 | 📄 FileText |
| `message` | 消息/私信 | ✉️ Mail |
| `parking` | 停车 | 🚗 Car |
| `repair` | 报修 | 🔧 Wrench |
| `check` | 确认/已读 | ✅ Check |
| `tool` | 通用工具 | 🔨 Tool |

### React + Lucide Icons 示例

```tsx
import { 
  Bell, 
  FileText, 
  Mail, 
  Car, 
  Wrench, 
  Check, 
  Tool 
} from 'lucide-react';

const ICON_MAP = {
  notification: Bell,
  bill: FileText,
  message: Mail,
  parking: Car,
  repair: Wrench,
  check: Check,
  tool: Tool,
};

export const ToolIcon = ({ iconName }: { iconName: string }) => {
  const Icon = ICON_MAP[iconName] || Tool;
  return <Icon className="w-5 h-5" />;
};
```

---

## 💡 React 集成示例

### 完整的 WebSocket Hook

```tsx
import { useState, useEffect, useRef } from 'react';

interface ToolCall {
  id: string;
  tool: string;
  displayName: string;
  message: string;
  icon: string;
  category: string;
  status: 'calling' | 'completed';
  timestamp: Date;
}

export const useAgentChat = (token: string, sessionId?: number) => {
  const [messages, setMessages] = useState<string[]>([]);
  const [currentChunk, setCurrentChunk] = useState('');
  const [toolCalls, setToolCalls] = useState<ToolCall[]>([]);
  const [status, setStatus] = useState<'idle' | 'thinking' | 'responding' | 'completed'>('idle');
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    const ws = new WebSocket(`ws://localhost:8001/ws/chat${sessionId ? `?session_id=${sessionId}` : ''}`);
    wsRef.current = ws;

    ws.onopen = () => {
      // 发送认证消息
      ws.send(JSON.stringify({ type: 'auth', token }));
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);

      switch (data.type) {
        case 'auth_success':
          console.log('认证成功');
          break;

        case 'status':
          if (data.status === 'thinking') {
            setStatus('thinking');
          } else if (data.status === 'tool_calling') {
            // 🔥 工具调用开始
            setToolCalls(prev => [...prev, {
              id: `${data.data.tool}-${Date.now()}`,
              tool: data.data.tool,
              displayName: data.data.display_name,
              message: data.data.message,
              icon: data.data.icon,
              category: data.data.category,
              status: 'calling',
              timestamp: new Date(),
            }]);
          } else if (data.status === 'tool_completed') {
            // 🔥 工具调用完成
            setToolCalls(prev => prev.map(call => 
              call.tool === data.data.tool && call.status === 'calling'
                ? { ...call, status: 'completed', message: data.data.message }
                : call
            ));
          } else if (data.status === 'completed') {
            setStatus('completed');
          }
          break;

        case 'chunk':
          setStatus('responding');
          if (data.is_final) {
            // 流式输出结束
            setMessages(prev => [...prev, currentChunk]);
            setCurrentChunk('');
          } else {
            // 累积文本片段
            setCurrentChunk(prev => prev + data.content);
          }
          break;

        case 'error':
          console.error('错误:', data.content);
          break;

        case 'session_created':
          console.log('会话创建:', data.data);
          break;

        case 'session_updated':
          console.log('标题更新:', data.data.title);
          break;
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket 错误:', error);
    };

    ws.onclose = () => {
      console.log('连接关闭');
    };

    return () => {
      ws.close();
    };
  }, [token, sessionId]);

  const sendMessage = (query: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ query }));
      setStatus('thinking');
      setToolCalls([]); // 清空之前的工具调用记录
    }
  };

  return {
    messages,
    currentChunk,
    toolCalls,
    status,
    sendMessage,
  };
};
```

---

### 工具调用展示组件

```tsx
import { ToolIcon } from './ToolIcon';
import { Loader2 } from 'lucide-react';

interface ToolCallDisplayProps {
  toolCall: {
    displayName: string;
    message: string;
    icon: string;
    status: 'calling' | 'completed';
  };
}

export const ToolCallDisplay = ({ toolCall }: ToolCallDisplayProps) => {
  const isRunning = toolCall.status === 'calling';

  return (
    <div className={`
      flex items-center gap-3 px-4 py-3 rounded-lg border
      ${isRunning 
        ? 'bg-blue-50 border-blue-200 animate-pulse' 
        : 'bg-green-50 border-green-200'
      }
    `}>
      <ToolIcon iconName={toolCall.icon} />
      
      <div className="flex-1">
        <div className="font-medium text-gray-900">
          {toolCall.displayName}
        </div>
        <div className="text-sm text-gray-600">
          {toolCall.message}
        </div>
      </div>

      {isRunning && (
        <Loader2 className="w-4 h-4 animate-spin text-blue-500" />
      )}
      
      {toolCall.status === 'completed' && (
        <span className="text-green-600 text-xl">✓</span>
      )}
    </div>
  );
};
```

---

### 完整聊天界面示例

```tsx
import { useAgentChat } from './useAgentChat';
import { ToolCallDisplay } from './ToolCallDisplay';

export const ChatInterface = ({ token }: { token: string }) => {
  const { messages, currentChunk, toolCalls, status, sendMessage } = useAgentChat(token);
  const [input, setInput] = useState('');

  const handleSend = () => {
    if (input.trim()) {
      sendMessage(input);
      setInput('');
    }
  };

  return (
    <div className="flex flex-col h-screen max-w-4xl mx-auto">
      {/* 消息列表 */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((msg, idx) => (
          <div key={idx} className="bg-gray-100 rounded-lg p-4">
            {msg}
          </div>
        ))}

        {/* 当前正在输出的消息 */}
        {currentChunk && (
          <div className="bg-gray-100 rounded-lg p-4">
            {currentChunk}
            <span className="animate-pulse">▋</span>
          </div>
        )}

        {/* 工具调用展示区域 */}
        {toolCalls.length > 0 && (
          <div className="space-y-2">
            <div className="text-sm text-gray-500 font-medium">
              正在执行的操作：
            </div>
            {toolCalls.map((toolCall) => (
              <ToolCallDisplay key={toolCall.id} toolCall={toolCall} />
            ))}
          </div>
        )}

        {/* 状态提示 */}
        {status === 'thinking' && (
          <div className="flex items-center gap-2 text-gray-500">
            <Loader2 className="w-4 h-4 animate-spin" />
            <span>正在思考...</span>
          </div>
        )}
      </div>

      {/* 输入框 */}
      <div className="border-t p-4">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSend()}
            placeholder="输入消息..."
            className="flex-1 px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <button
            onClick={handleSend}
            disabled={status === 'thinking' || status === 'responding'}
            className="px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50"
          >
            发送
          </button>
        </div>
      </div>
    </div>
  );
};
```

---

## 📊 工具分类展示

### 按分类分组显示工具调用

```tsx
export const ToolCallHistory = ({ toolCalls }: { toolCalls: ToolCall[] }) => {
  // 按分类分组
  const grouped = toolCalls.reduce((acc, call) => {
    if (!acc[call.category]) {
      acc[call.category] = [];
    }
    acc[call.category].push(call);
    return acc;
  }, {} as Record<string, ToolCall[]>);

  const categoryNames = {
    notification: '📬 通知管理',
    bill: '💰 账单查询',
    message: '💬 消息功能',
    parking: '🅿️ 停车服务',
    repair: '🔧 报修服务',
    other: '🔨 其他功能',
  };

  return (
    <div className="space-y-6">
      {Object.entries(grouped).map(([category, calls]) => (
        <div key={category}>
          <h3 className="text-sm font-semibold text-gray-700 mb-3">
            {categoryNames[category] || category}
          </h3>
          <div className="space-y-2">
            {calls.map((call) => (
              <ToolCallDisplay key={call.id} toolCall={call} />
            ))}
          </div>
        </div>
      ))}
    </div>
  );
};
```

---

## 🔧 获取所有工具元数据（可选）

如果需要在前端预加载所有工具的元数据信息，可以调用：

```typescript
// GET 请求
const response = await fetch('http://localhost:8001/api/tools/metadata', {
  headers: {
    'Authorization': `Bearer ${token}`
  }
});

const result = await response.json();

/*
返回格式：
{
  "success": true,
  "data": {
    "query_unpaid_bills": {
      "display_name": "查询未支付账单",
      "description": "正在查询未支付的账单",
      "icon": "bill",
      "category": "bill"
    },
    "get_user_notifications": {
      "display_name": "查询通知",
      "description": "正在查询您的通知记录",
      "icon": "notification",
      "category": "notification"
    },
    // ... 其他工具
  }
}
*/
```

**用途**：
- 提前渲染工具列表
- 构建图标库
- 多语言本地化准备

---

## 📝 当前支持的工具列表

| 工具函数名 | 显示名称 | 描述 | 分类 | 图标 |
|-----------|---------|------|------|------|
| `query_unpaid_bills` | 查询未支付账单 | 正在查询未支付的账单 | bill | 📄 bill |
| `get_user_notifications` | 查询通知 | 正在查询您的通知记录 | notification | 🔔 notification |
| `read_notification` | 标记已读 | 正在标记通知为已读 | notification | ✅ check |
| `send_private_messages` | 发送私信 | 正在发送私信 | message | ✉️ message |

---

## 🎯 完整对话示例

**用户输入**："我有哪些待缴费用？"

**前端接收到的消息序列**：

```json
// 1. 思考中
{"type":"status","status":"thinking","data":{"message":"正在思考..."}}

// 2. 开始调用工具
{
  "type":"status",
  "status":"tool_calling",
  "data":{
    "tool":"query_unpaid_bills",
    "display_name":"查询未支付账单",
    "message":"正在查询未支付的账单",
    "icon":"bill",
    "category":"bill"
  }
}

// 3. 工具执行完成
{
  "type":"status",
  "status":"tool_completed",
  "data":{
    "tool":"query_unpaid_bills",
    "display_name":"查询未支付账单",
    "message":"查询未支付账单执行完成",
    "icon":"bill",
    "category":"bill"
  }
}

// 4. 开始流式输出回复
{"type":"chunk","content":"您","is_final":false}
{"type":"chunk","content":"目","is_final":false}
{"type":"chunk","content":"前","is_final":false}
{"type":"chunk","content":"有","is_final":false}
{"type":"chunk","content":"3","is_final":false}
{"type":"chunk","content":"条","is_final":false}
{"type":"chunk","content":"待","is_final":false}
{"type":"chunk","content":"缴","is_final":false}
{"type":"chunk","content":"费","is_final":false}
{"type":"chunk","content":"用","is_final":false}
{"type":"chunk","content":"：","is_final":false}
// ... 更多文本片段
{"type":"chunk","content":"","is_final":true}

// 5. 完成
{"type":"status","status":"completed","data":{"message":"回答完成"}}
```

**前端 UI 展示效果**：

```
┌────────────────────────────────────┐
│ 正在执行的操作：                    │
│ ┌──────────────────────────────┐   │
│ │ 📄 查询未支付账单              │   │
│ │ 查询未支付账单执行完成 ✓       │   │
│ └──────────────────────────────┘   │
└────────────────────────────────────┘

┌────────────────────────────────────┐
│ 您目前有3条待缴费用：               │
│ 1. 物业费：500元                   │
│ 2. 停车费：200元                   │
│ 3. 水费：80元                      │
└────────────────────────────────────┘
```

---

## ⚠️ 注意事项

### 1. WebSocket 重连机制
建议实现自动重连逻辑：

```typescript
const connectWebSocket = () => {
  const ws = new WebSocket(WS_URL);
  
  ws.onclose = () => {
    console.log('连接断开，3秒后重连...');
    setTimeout(connectWebSocket, 3000);
  };
  
  return ws;
};
```

### 2. 消息顺序保证
WebSocket 消息是有序的，按接收顺序处理即可。

### 3. 工具调用状态管理
- 一个工具可能被多次调用，使用 `tool + timestamp` 作为唯一标识
- 使用队列管理工具调用状态，先进先出匹配完成状态

### 4. 流式输出优化
- 建议使用 `requestAnimationFrame` 批量更新 UI
- 避免每个字符都触发重渲染

```typescript
let pendingChunks = '';
let rafId: number | null = null;

const handleChunk = (chunk: string) => {
  pendingChunks += chunk;
  
  if (rafId === null) {
    rafId = requestAnimationFrame(() => {
      setCurrentChunk(prev => prev + pendingChunks);
      pendingChunks = '';
      rafId = null;
    });
  }
};
```

---

## 📞 技术支持

如有问题，请联系后端团队或查阅：
- WebSocket API 文档：`docs/websocket_guide.md`
- 工具元数据详细说明：`docs/tool_metadata_usage.md`

---

**文档版本**：v1.0  
**最后更新**：2026-01-11


