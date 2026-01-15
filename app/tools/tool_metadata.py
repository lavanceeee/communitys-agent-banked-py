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
    "query_unpaid_bills": {
        "display_name": "查询未支付账单",
        "description": "正在查询未支付的账单",
        "icon": "bill",
        "category": "bill"
    },
    "pay_bill": {
        "display_name": "支付账单",
        "description": "正在支付账单",
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
    
    # 天气相关
    "get_weather": {
        "display_name": "查询天气",
        "description": "正在查询天气",
        "icon": "weather",
        "category": "weather"
    },
    
    # 时间相关
    "get_time": {
        "display_name": "获取当前时间",
        "description": "正在获取当前时间",
        "icon": "time",
        "category": "time"
    },
    
    # 邮件相关
    "send_scheduled_email": {
        "display_name": "发送定时邮件",
        "description": "正在发送定时邮件",
        "icon": "email",
        "category": "email"
    },
    "get_scheduled_email": {
        "display_name": "查询定时邮件",
        "description": "正在查询定时邮件",
        "icon": "email",
        "category": "email"
    },
    "delete_scheduled_email": {
        "display_name": "删除定时邮件",
        "description": "正在删除定时邮件",
        "icon": "email",
        "category": "email"
    },
    
    # 搜索相关
    "web_search": {
        "display_name": "网络搜索",
        "description": "正在使用 Google 搜索联网查询",
        "icon": "search",
        "category": "search"
    },
    "wikipedia_search": {
        "display_name": "维基百科搜索",
        "description": "正在查询维基百科",
        "icon": "wikipedia",
        "category": "search"
    },
    "toutiao_hot_news": {
        "display_name": "头条热榜",
        "description": "正在获取今日头条热榜新闻",
        "icon": "news",
        "category": "search"
    },
    "search_domains_info": {
        "display_name": "域名搜索",
        "description": "正在搜索域名信息",
        "icon": "domain",
        "category": "search"
    },
    
    # 图片生成相关
    "generate_image_from_text": {
        "display_name": "文生图",
        "description": "正在根据描述生成图片",
        "icon": "image",
        "category": "image"
    },
    
    # 访客相关
    "create_visitor": {
        "display_name": "访客登记",
        "description": "正在登记访客信息",
        "icon": "visitor",
        "category": "visitor"
    },
    
    # 商城相关
    "search_goods": {
        "display_name": "搜索商品",
        "description": "正在搜索商品",
        "icon": "shop",
        "category": "mall"
    },
    
    # 社区公告相关
    "get_community_announcements": {
        "display_name": "获取社区公告",
        "description": "正在获取社区公告",
        "icon": "announcement",
        "category": "community"
    },
    
    # 用户相关
    "get_user_profile": {
        "display_name": "获取用户资料",
        "description": "正在获取用户资料",
        "icon": "user",
        "category": "user"
    },
    "update_user_profile": {
        "display_name": "更新用户资料",
        "description": "正在更新用户资料",
        "icon": "user",
        "category": "user"
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

