import os
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from app.tools import all_tools  # 从统一入口导入

# dotenv
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_KEY")


async def get_agent_response(user_id: str, user_input: str):
    """
    异步获取 Agent 响应

    Args:
        user_id: 用户 ID
        user_input: 用户输入

    Returns:
        Agent 的响应文本
    """
    # 初始化模型
    llm = ChatOpenAI(
        api_key=API_KEY,
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        model="qwen-plus",
        temperature=0,
    )

    # 使用 langgraph 的 create_react_agent（新版推荐方式）
    agent_executor = create_react_agent(llm, all_tools)

    # 异步运行（注入用户ID到消息中）
    result = await agent_executor.ainvoke(
        {"messages": [("user", f"User ID: {user_id}\nRequest: {user_input}")]}
    )

    # 提取最后一条消息内容
    return result["messages"][-1].content
