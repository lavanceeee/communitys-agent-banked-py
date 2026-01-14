导出依赖: pip freeze > requirements.txt

安装依赖：pip install -r requirements.txt

创建虚拟环境: python -m venv venv

激活虚拟环境: .\venv\Scripts\Activate.ps1

关闭虚拟环境：deactivate

# dotenv
from dotenv import load_dotenv

load_dotenv()


# Function Tool规范

函数名：query_bills

Docstring:
"""
查询用户的所有未支付账单。
当用户问"我有哪些待缴费用"时使用此工具。
"""

参数需要加类型
def query_bills(user_id: str, limit: int = 10): 

返回JSON字符串
return json.dumps(data, ensure_ascii=False) 

错误处理
try:
except Exception as e:
    return {"error": str(e)}