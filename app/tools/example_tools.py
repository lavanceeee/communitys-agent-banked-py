"""
示例：使用 http_client 处理多种业务逻辑

这个文件展示了如何使用统一的 http_client 来处理不同的业务场景
"""

import json
from langchain_core.tools import tool
from app.utils.http_client import http_client


# ============ 账单相关 ============


@tool
async def query_unpaid_bills(user_id: str):
    """查询用户当前所有的代缴账单记录"""
    data = await http_client.get("/api/bills", params={"uid": user_id})
    return json.dumps(data, ensure_ascii=False)


@tool
async def pay_bill(user_id: str, bill_id: str):
    """支付指定账单"""
    data = await http_client.post(
        "/api/bills/pay", json_data={"uid": user_id, "bill_id": bill_id}
    )
    return json.dumps(data, ensure_ascii=False)


# ============ 停车相关 ============


@tool
async def query_parking_records(user_id: str, page: int = 1, limit: int = 10):
    """查询停车记录"""
    data = await http_client.get(
        "/api/parking/records", params={"uid": user_id, "page": page, "limit": limit}
    )
    return json.dumps(data, ensure_ascii=False)


@tool
async def book_parking_space(user_id: str, space_id: str, date: str):
    """预约停车位"""
    data = await http_client.post(
        "/api/parking/book",
        json_data={"uid": user_id, "space_id": space_id, "date": date},
    )
    return json.dumps(data, ensure_ascii=False)


# ============ 报修相关 ============


@tool
async def submit_repair_request(user_id: str, description: str, location: str):
    """提交报修请求"""
    data = await http_client.post(
        "/api/repairs",
        json_data={"uid": user_id, "description": description, "location": location},
    )
    return json.dumps(data, ensure_ascii=False)


@tool
async def query_repair_status(user_id: str, repair_id: str):
    """查询报修状态"""
    data = await http_client.get(f"/api/repairs/{repair_id}", params={"uid": user_id})
    return json.dumps(data, ensure_ascii=False)


# ============ 社区公告 ============


@tool
async def get_community_announcements(user_id: str, category: str = "all"):
    """获取社区公告"""
    data = await http_client.get(
        "/api/announcements", params={"uid": user_id, "category": category}
    )
    return json.dumps(data, ensure_ascii=False)


# ============ 用户信息 ============


@tool
async def get_user_profile(user_id: str):
    """获取用户资料"""
    data = await http_client.get(f"/api/users/{user_id}")
    return json.dumps(data, ensure_ascii=False)


@tool
async def update_user_profile(user_id: str, name: str = None, phone: str = None):
    """更新用户资料"""
    update_data = {"uid": user_id}
    if name:
        update_data["name"] = name
    if phone:
        update_data["phone"] = phone

    data = await http_client.put(f"/api/users/{user_id}", json_data=update_data)
    return json.dumps(data, ensure_ascii=False)
