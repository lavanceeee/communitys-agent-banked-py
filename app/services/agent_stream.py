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

load_dotenv()

API_KEY = os.getenv("API_KEY")


async def get_agent_response_stream(user_id: str, user_input: str):
    """
    流式获取 Agent 响应，通过 WebSocket 发送

    Args:
        user_id: 用户 ID
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
        tool_call_in_progress = False
        try:
            async for event in agent_executor.astream_events(
                {"messages": [("user", f"User ID: {user_id}\nRequest: {user_input}")]},
                config=config,
                version="v1",
            ):
                kind = event["event"]
                
                # 调试日志：打印事件类型
                print(f"[Event] {kind}")

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
                    tool_call_in_progress = True
                    tool_name = event["name"]
                    print(f"[Tool Start] {tool_name}")
                    
                    # 获取工具的显示信息
                    tool_info = get_tool_display_info(tool_name)
                    await manager.send_status(
                        user_id,
                        "tool_calling",
                        {
                            "tool": tool_name,
                            "message": tool_info["description"],
                            "display_name": tool_info["display_name"],
                            "icon": tool_info["icon"],
                            "category": tool_info["category"]
                        },
                    )

                elif kind == "on_tool_end":
                    # 工具调用结束
                    tool_call_in_progress = False
                    tool_name = event["name"]
                    print(f"[Tool End] {tool_name}")
                    try:
                        # 获取工具的显示信息
                        tool_info = get_tool_display_info(tool_name)
                        await manager.send_status(
                            user_id,
                            "tool_completed",
                            {
                                "tool": tool_name,
                                "message": f"{tool_info['display_name']}完成",
                                "display_name": tool_info["display_name"],
                                "icon": tool_info["icon"],
                                "category": tool_info["category"]
                            },
                        )
                        # 工具调用后，Agent 会继续思考，不要立即结束
                        await manager.send_status(user_id, "thinking", {"message": "正在整理结果..."})
                    except Exception as send_error:
                        print(f"[Send Error after tool] {send_error}")
                        # 继续循环，不要中断
        except Exception as stream_error:
            print(f"[Stream Event Error] {stream_error}")
            print(f"[Debug] Error type: {type(stream_error)}")
            import traceback
            traceback.print_exc()
            # 如果是连接断开，不继续抛出异常
            if "disconnected" not in str(stream_error).lower():
                raise
        
        print(f"[Stream Finished] Full response length: {len(full_response)}")
        print(f"[Debug] Tool was called but final response not generated" if tool_call_in_progress else "[Debug] Normal completion")

        # 发送完成状态
        await manager.send_text_chunk(user_id, "", is_final=True)
        await manager.send_status(user_id, "completed", {"message": "回答完成"})

    except ConnectionError as e:
        # WebSocket 连接已断开，不需要发送错误消息
        print(f"[Agent Stream Error] Connection lost: {e}")
    except Exception as e:
        print(f"[Agent Stream Error] {e}")
        try:
            await manager.send_error(user_id, f"处理出错: {str(e)}")
        except:
            # 如果连接已断开，忽略发送错误
            pass


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
