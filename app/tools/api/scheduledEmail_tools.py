import json
from langchain_core.tools import tool
from app.utils.http_client import http_client
from langchain_core.tools import tool
from pydantic import BaseModel, Field, validator
from datetime import datetime, timezone
import json

# 第一步：定义参数模型（映射 Java 的 ScheduledEmailRequest）
class ScheduledEmailSchema(BaseModel):
    """定时邮件请求参数模型（对应Java后端ScheduledEmailRequest）"""
    subject: str = Field(
        ...,  # 必填
        description="邮件主题，不能为空，最多200个字符",
        max_length=200
    )
    content: str = Field(
        ...,  # 必填
        description="邮件内容，不能为空，最多10000个字符",
        max_length=10000
    )
    isHtml: bool = Field(
        default=False,
        description="是否为HTML格式，默认false"
    )
    scheduledTime: str = Field(
        ...,  # 必填
        description="计划发送时间，必须是将来的时间，格式为2026-01-14T12:30:00"
    )

    # 验证：确保时间是将来的时间，并转换为Java后端接受的格式
    @validator('scheduledTime')
    def validate_future_time(cls, v):
        try:
            # 尝试解析各种ISO格式时间
            if '+' in v or v.endswith('Z'):
                # 带时区的格式，解析后转换
                scheduled_dt = datetime.fromisoformat(v.replace('Z', '+00:00'))
            else:
                # 不带时区的格式，假设是本地时间
                scheduled_dt = datetime.fromisoformat(v)
                # 添加本地时区信息用于比较
                scheduled_dt = scheduled_dt.replace(tzinfo=datetime.now().astimezone().tzinfo)
            
            # 转换为本地时区进行比较
            now = datetime.now(timezone.utc).astimezone()
            if scheduled_dt <= now:
                raise ValueError("发送时间必须是将来的时间")
            
            # 返回不带时区的格式（Java后端需要）
            # 如果原始时间带时区，转换为本地时间后去掉时区
            if '+' in v or v.endswith('Z'):
                local_dt = scheduled_dt.astimezone()
                return local_dt.strftime('%Y-%m-%dT%H:%M:%S')
            else:
                # 已经是不带时区的格式，直接返回
                return v
        except ValueError as ve:
            raise ve
        except Exception as e:
            raise ValueError(f"时间格式错误，需为格式如2026-01-20T14:30:00：{str(e)}")


@tool(args_schema=ScheduledEmailSchema)
async def send_scheduled_email(subject: str, content: str, scheduledTime: str, isHtml: bool = False) -> str:
    """
    发送定时邮件
    参数: subject: 邮件主题
    参数: content: 邮件内容
    参数: scheduledTime: 计划发送时间
    参数: isHtml: 是否为HTML格式
    """
    data = await http_client.post("/api/scheduled-email", json_data={"subject": subject, "content": content, "scheduledTime": scheduledTime, "isHtml": isHtml})
    return json.dumps(data, ensure_ascii=False)

@tool
async def get_scheduled_email(pageNum: int = 0, pageSize: int = 10) -> str:
    """
    查询当前用户的定时邮件记录
    参数: pageNum: 页码
    参数: pageSize: 每页条数
    """
    data = await http_client.get("/api/scheduled-email/list", params={"page": pageNum, "size": pageSize})
    return json.dumps(data, ensure_ascii=False)

@tool
async def delete_scheduled_email(id: str) -> str:
    """
    删除定时邮件记录
    参数: id: 定时邮件记录ID
    """
    data = await http_client.delete(f"/api/scheduled-email/{id}")
    return json.dumps(data, ensure_ascii=False)