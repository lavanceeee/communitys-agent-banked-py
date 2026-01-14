# 统一导入所有工具文件
from app.tools.community.bills_tools import query_unpaid_bills
from app.tools.community.notification_tools import get_user_notifications
from app.tools.community.privatemessage_tools import send_private_messages
from app.tools.community.notification_tools import read_notification
from app.tools.api.weather_tools import get_weather
from app.tools.api.get_time_tools import get_time
from app.tools.others.search import (
    web_search,
    wikipedia_search,
    toutiao_hot_news,
    search_domains_info,
)
from app.tools.api.scheduledEmail_tools import send_scheduled_email, delete_scheduled_email, get_scheduled_email

# 未来如果有其他工具文件，继续在这里导入
# from app.tools.wallet_tools import query_wallet_balance, transfer_money
# from app.tools.order_tools import create_order, cancel_order

# 导出所有工具的统一列表
all_tools = [
    query_unpaid_bills,
    get_user_notifications,
    send_private_messages,
    read_notification,
    get_weather,
    web_search,
    wikipedia_search,
    toutiao_hot_news,
    search_domains_info,
    send_scheduled_email,
    get_time,
    delete_scheduled_email,
    get_scheduled_email,
    # 以后新增工具直接在这里添加
]
