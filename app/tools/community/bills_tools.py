import json
from langchain_core.tools import tool
from app.utils.http_client import http_client


"""
// 查询我的物业费账单
export const getMyBillsApi = (params: any) => {
  return $api('/api/property-fee/bills', {
    method: 'GET',
    params
  })
}

"""


@tool
async def query_unpaid_bills(status: int = 0) -> str:
    """
    查询用户当前所有的代缴账单记录。
    参数: status: 0 (代缴)
    """
    try:
        data = await http_client.get("/api/property-fee/bills", params={"status": status})
        return json.dumps(data, ensure_ascii=False)
    except Exception as e:
        error_msg = {
            "success": False,
            "error": "服务暂时不可用",
            "message": "抱歉，账单服务当前无法访问，请稍后再试。",
            "detail": str(e)
        }
        return json.dumps(error_msg, ensure_ascii=False)
