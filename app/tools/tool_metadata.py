"""
工具元数据映射表
用于前端展示工具调用的可读信息
"""

# 工具名称到可读信息的映射
TOOL_METADATA = {
    # 通知相关
    "get_user_notifications": {
        "display_name": "查询通知",
        "description": "正在查询您的通知记录",
        "icon": "notification",
        "category": "notification"
    },
    "read_notification": {
        "display_name": "标记已读",
        "description": "正在标记通知为已读",
        "icon": "check",
        "category": "notification"
    },
    
    # 账单相关
    "query_bills": {
        "display_name": "查询账单",
        "description": "正在查询您的账单信息",
        "icon": "bill",
        "category": "bill"
    },
    "query_unpaid_bills": {
        "display_name": "查询未支付账单",
        "description": "正在查询未支付的账单",
        "icon": "bill",
        "category": "bill"
    },
    
    # 私信相关
    "send_private_messages": {
        "display_name": "发送私信",
        "description": "正在发送私信",
        "icon": "message",
        "category": "message"
    },
    
    # 停车相关
    "query_parking_records": {
        "display_name": "查询停车记录",
        "description": "正在查询停车记录",
        "icon": "parking",
        "category": "parking"
    },
    "book_parking_space": {
        "display_name": "预约停车位",
        "description": "正在预约停车位",
        "icon": "parking",
        "category": "parking"
    },
    
    # 报修相关
    "submit_repair_request": {
        "display_name": "提交报修",
        "description": "正在提交报修请求",
        "icon": "repair",
        "category": "repair"
    },
    "query_repair_status": {
        "display_name": "查询报修状态",
        "description": "正在查询报修状态",
        "icon": "repair",
        "category": "repair"
    },
}


def get_tool_display_info(tool_name: str) -> dict:
    """
    获取工具的显示信息
    
    Args:
        tool_name: 工具名称
        
    Returns:
        包含显示信息的字典
    """
    if tool_name in TOOL_METADATA:
        return TOOL_METADATA[tool_name]
    
    # 如果没有找到，返回默认信息
    return {
        "display_name": tool_name,
        "description": f"正在执行: {tool_name}",
        "icon": "tool",
        "category": "other"
    }


def get_all_tools_metadata() -> dict:
    """
    获取所有工具的元数据
    
    Returns:
        所有工具的元数据字典
    """
    return TOOL_METADATA

