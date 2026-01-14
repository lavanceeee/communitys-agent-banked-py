import json
from langchain_core.tools import tool
from app.utils.http_client import http_client
from pydantic import BaseModel, Field, validator

from datetime import datetime


class VisitorRegisterSchema(BaseModel):
    """访客登记请求参数模型"""

    visitorName: str = Field(..., description="访客姓名，不能为空", min_length=1)
    visitorPhone: str = Field(
        ..., description="访客电话，必须是11位手机号", pattern=r"^1[3-9]\d{9}$"
    )
    visitPurpose: str = Field(..., description="来访目的，不能为空", min_length=1)
    allowTime: str = Field(
        ...,
        description="放行时间，格式：yyyy-MM-dd HH:mm:ss (例如: 2026-01-05 10:00:00)",
    )
    validDate: str = Field(
        ...,
        description="有效日期，格式：yyyy-MM-dd HH:mm:ss (例如: 2026-01-05 23:59:59)",
    )

    @validator("allowTime", "validDate")
    def validate_datetime_format(cls, v):
        try:
            # 验证格式是否为 "YYYY-MM-DD HH:MM:SS"
            datetime.strptime(v, "%Y-%m-%d %H:%M:%S")
            return v
        except ValueError:
            raise ValueError(
                "时间格式必须为 'yyyy-MM-dd HH:mm:ss'，例如 '2026-01-05 10:00:00'"
            )


@tool(args_schema=VisitorRegisterSchema)
async def create_visitor(
    visitorName: str,
    visitorPhone: str,
    visitPurpose: str,
    allowTime: str,
    validDate: str,
) -> str:
    """
    登记访客信息
    """
    try:
        payload = {
            "visitorName": visitorName,
            "visitorPhone": visitorPhone,
            "visitPurpose": visitPurpose,
            "allowTime": allowTime,
            "validDate": validDate,
        }
        data = await http_client.post("/api/visitor/register", json_data=payload)
        return json.dumps(data, ensure_ascii=False)
    except Exception as e:
        error_msg = {
            "success": False,
            "error": "服务暂时不可用",
            "message": "抱歉，访客登记服务当前无法访问，请稍后再试。",
            "detail": str(e),
        }
        return json.dumps(error_msg, ensure_ascii=False)
