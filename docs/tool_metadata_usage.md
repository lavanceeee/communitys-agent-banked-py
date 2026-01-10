# 工具元数据使用指南

## 概述

工具元数据系统允许前端展示更友好的工具调用信息，而不是显示原始的函数名。

## 后端实现

### 1. 工具元数据定义

文件：`app/tools/tool_metadata.py`

每个工具包含以下信息：
- `display_name`: 显示名称（用户友好的名称）
- `description`: 描述信息（工具调用时的提示文本）
- `icon`: 图标标识（前端可以根据此映射到图标）
- `category`: 分类（用于分组展示）

### 2. WebSocket 消息格式

当 AI 调用工具时，前端会收到增强的状态消息：

#### 工具调用开始
```json
{
  "type": "status",
  "status": "tool_calling",
  "data": {
    "tool": "get_user_notifications",
    "message": "正在查询您的通知记录",
    "display_name": "查询通知",
    "icon": "notification",
    "category": "notification"
  }
}
```

#### 工具调用完成
```json
{
  "type": "status",
  "status": "tool_completed",
  "data": {
    "tool": "get_user_notifications",
    "message": "查询通知完成",
    "display_name": "查询通知",
    "icon": "notification",
    "category": "notification"
  }
}
```

### 3. REST API

获取所有工具元数据：

```bash
GET /api/tools/metadata
```

响应：
```json
{
  "success": true,
  "data": {
    "get_user_notifications": {
      "display_name": "查询通知",
      "description": "正在查询您的通知记录",
      "icon": "notification",
      "category": "notification"
    },
    "send_private_messages": {
      "display_name": "发送私信",
      "description": "正在发送私信",
      "icon": "message",
      "category": "message"
    }
    // ... 其他工具
  }
}
```

## 前端使用

### 1. 图标映射示例（React）

```tsx
// IconMapper.tsx
import { Bell, Mail, FileText, Car, Wrench, Tool } from 'lucide-react';

const ICON_MAP = {
  notification: Bell,
  message: Mail,
  bill: FileText,
  parking: Car,
  repair: Wrench,
  tool: Tool,
};

export const ToolIcon = ({ iconName }: { iconName: string }) => {
  const Icon = ICON_MAP[iconName] || Tool;
  return <Icon className="w-4 h-4" />;
};
```

### 2. 工具调用展示组件

```tsx
// ToolCallIndicator.tsx
import { ToolIcon } from './IconMapper';

interface ToolCallProps {
  toolName: string;
  displayName: string;
  message: string;
  icon: string;
  status: 'calling' | 'completed';
}

export const ToolCallIndicator = ({ 
  displayName, 
  message, 
  icon, 
  status 
}: ToolCallProps) => {
  return (
    <div className={`
      flex items-center gap-2 p-3 rounded-lg
      ${status === 'calling' ? 'bg-blue-50 animate-pulse' : 'bg-green-50'}
    `}>
      <ToolIcon iconName={icon} />
      <div>
        <div className="font-medium">{displayName}</div>
        <div className="text-sm text-gray-600">{message}</div>
      </div>
      {status === 'calling' && (
        <div className="ml-auto">
          <Spinner />
        </div>
      )}
    </div>
  );
};
```

### 3. WebSocket 消息处理

```tsx
// useAgent.ts
const [toolCalls, setToolCalls] = useState<ToolCall[]>([]);

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  if (data.type === 'status') {
    if (data.status === 'tool_calling') {
      // 添加工具调用记录
      setToolCalls(prev => [...prev, {
        id: Date.now(),
        toolName: data.data.tool,
        displayName: data.data.display_name,
        message: data.data.message,
        icon: data.data.icon,
        category: data.data.category,
        status: 'calling',
        startTime: new Date()
      }]);
    } else if (data.status === 'tool_completed') {
      // 更新工具调用状态
      setToolCalls(prev => prev.map(call => 
        call.toolName === data.data.tool && call.status === 'calling'
          ? { ...call, status: 'completed', endTime: new Date() }
          : call
      ));
    }
  }
};
```

### 4. 分类展示

```tsx
// ToolCallHistory.tsx
const groupedTools = toolCalls.reduce((acc, tool) => {
  if (!acc[tool.category]) {
    acc[tool.category] = [];
  }
  acc[tool.category].push(tool);
  return acc;
}, {} as Record<string, ToolCall[]>);

return (
  <div className="space-y-4">
    {Object.entries(groupedTools).map(([category, tools]) => (
      <div key={category}>
        <h3 className="text-sm font-medium text-gray-500 mb-2">
          {category}
        </h3>
        <div className="space-y-2">
          {tools.map(tool => (
            <ToolCallIndicator key={tool.id} {...tool} />
          ))}
        </div>
      </div>
    ))}
  </div>
);
```

## 工具分类

当前支持的分类：
- `notification`: 通知相关
- `bill`: 账单相关
- `message`: 消息相关
- `parking`: 停车相关
- `repair`: 报修相关
- `other`: 其他

## 添加新工具

在 `app/tools/tool_metadata.py` 中添加新工具的元数据：

```python
TOOL_METADATA = {
    # ... 现有工具
    
    "your_new_tool": {
        "display_name": "你的新工具",
        "description": "正在执行你的新工具",
        "icon": "tool",
        "category": "your_category"
    },
}
```

## 注意事项

1. **图标名称**：前端需要根据 `icon` 字段映射到实际的图标组件
2. **分类扩展**：添加新分类时，前端也需要相应更新
3. **国际化**：如果需要多语言支持，可以扩展元数据结构
4. **后备方案**：如果工具没有在元数据中定义，会返回默认值

