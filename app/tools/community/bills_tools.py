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
async def query_unpaid_bills(status: int) -> str:
    """
    查询用户当前所有的代缴账单记录。
    参数: status: 0 (代缴)
    """

    data = await http_client.get("/api/property-fee/bills", params={"status": 0})
    return json.dumps(data, ensure_ascii=False)
