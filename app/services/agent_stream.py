"""
流式 Agent 服务
支持 WebSocket 流式输出
"""

import os
import asyncio
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from app.tools import all_tools
from app.tools.tool_metadata import get_tool_display_info
from app.websocket.manager import manager
from dotenv import load_dotenv
from app.database.service.message import save_message

load_dotenv()

API_KEY = os.getenv("API_KEY")


async def get_agent_response_stream(user_id: str, session_id: int, user_input: str):
    """
    流式获取 Agent 响应，通过 WebSocket 发送

    Args:
        user_id: 用户 ID
        session_id: 会话 ID
        user_input: 用户输入
    """
    try:
        # 发送开始状态
        await manager.send_status(user_id, "thinking", {"message": "正在思考..."})

        # 初始化模型（启用流式输出）
        llm = ChatOpenAI(
            api_key=API_KEY,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            model="qwen-plus",
            temperature=0,
            streaming=True,  # 启用流式输出
        )

        # 使用 langgraph 的 create_react_agent
        agent_executor = create_react_agent(llm, all_tools)

        # 配置：增加递归限制，防止无限循环
        config = {
            "recursion_limit": 50,  # 增加递归限制
        }

        # 流式运行
        full_response = ""
        async for event in agent_executor.astream_events(
            {"messages": [("user", f"User ID: {user_id}\nRequest: {user_input}")]},
            version="v1",
        ):
            kind = event["event"]

            # 处理不同类型的事件
            if kind == "on_chat_model_stream":
                # LLM 流式输出
                content = event["data"]["chunk"].content
                if content:
                    full_response += content
                    # 发送文本片段
                    await manager.send_text_chunk(user_id, content, is_final=False)
                    # 添加小延迟，模拟打字机效果
                    await asyncio.sleep(0.01)

            elif kind == "on_tool_start":
                # 工具调用开始
                tool_name = event["name"]
                await manager.send_status(
                    user_id,
                    "tool_calling",
                    {"tool": tool_name, "message": f"正在调用工具: {tool_name}"},
                )

            elif kind == "on_tool_end":
                # 工具调用结束
                tool_name = event["name"]
                await manager.send_status(
                    user_id,
                    "tool_completed",
                    {"tool": tool_name, "message": f"工具 {tool_name} 执行完成"},
                )

        # 发送完成状态
        await manager.send_text_chunk(user_id, "", is_final=True)
        await manager.send_status(user_id, "completed", {"message": "回答完成"})

        # 异步保存消息到
        print("---开始保存消息----")

        async def _save_to_db(sid, role, content):
            try:
                # 假设 save_message 是同步的，这里直接调用
                # 如果是耗时操作，建议用 loop.run_in_executor
                save_message(session_id=sid, role=role, content=content)
            except Exception as e:
                print(f"保存消息失败: {e}")

        if session_id:
            asyncio.create_task(_save_to_db(session_id, "user", user_input))
            asyncio.create_task(_save_to_db(session_id, "assistant", full_response))
    except Exception as e:
        import traceback

        error_details = traceback.format_exc()
        print(f"[Agent Stream Error] {e}")
        print(f"[Agent Stream Error Details]\n{error_details}")
        await manager.send_error(user_id, f"处理出错: {str(e)}")


def get_agent_response(user_id: str, user_input: str):
    """
    同步获取 Agent 响应（保留原有接口兼容性）

    Args:
        user_id: 用户 ID
        user_input: 用户输入

    Returns:
        完整的响应文本
    """
    # 初始化模型
    llm = ChatOpenAI(
        api_key=API_KEY,
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        model="qwen-plus",
        temperature=0,
    )

    # 使用 langgraph 的 create_react_agent
    agent_executor = create_react_agent(llm, all_tools)

    # 运行（注入用户ID到消息中）
    result = agent_executor.invoke(
        {"messages": [("user", f"User ID: {user_id}\nRequest: {user_input}")]}
    )

    # 提取最后一条消息内容
    return result["messages"][-1].content
