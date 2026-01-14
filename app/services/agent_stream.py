"""
流式 Agent 服务
支持 WebSocket 流式输出

本模块实现了基于 LangGraph 的 AI Agent 流式响应功能，
通过 WebSocket 实时向客户端发送 AI 的思考过程、工具调用状态和生成的文本。
"""

# ============ 导入依赖 ============

# LangChain 消息类型，用于构建对话历史
from langchain_core.messages.ai import AIMessage  # AI 助手的消息类型
from langchain_core.messages.human import HumanMessage  # 用户的消息类型

# 从数据库获取历史消息的服务函数
from app.database.service.message import get_messages

# Python 标准库
import os  # 用于读取环境变量
import asyncio  # 异步编程支持，用于并发处理和延迟控制

# 1.0.5 版本正确导入 InMemorySaver
from langgraph.checkpoint.memory import InMemorySaver


# LangChain OpenAI 集成，用于调用兼容 OpenAI API 的大语言模型
from langchain_openai import ChatOpenAI

# LangGraph 提供的预置 ReAct Agent 创建函数
# ReAct = Reasoning + Acting，一种让 LLM 能够思考并调用工具的 Agent 架构
from langgraph.prebuilt import create_react_agent

# 导入所有可用的工具列表（如天气查询、账单查询等）
from app.tools import all_tools

# WebSocket 连接管理器，用于向客户端发送消息
from app.websocket.manager import manager

# 加载 .env 文件中的环境变量
from dotenv import load_dotenv

# 保存消息到数据库的服务函数
from app.database.service.message import save_message

# 工具元数据，用于获取工具的展示名称、图标、描述等信息
from app.tools.tool_metadata import get_tool_display_info, get_all_tools_metadata

# 加载环境变量（从 .env 文件读取配置）
load_dotenv()


# 从环境变量获取 API 密钥（用于调用大语言模型）
API_KEY = os.getenv("API_KEY")


checkpointer = InMemorySaver()

async def get_agent_response_stream(user_id: str, session_id: int, user_input: str):
    """
    流式获取 Agent 响应，通过 WebSocket 发送

    这是核心的流式响应函数，它会：
    1. 加载历史对话记录
    2. 创建 AI Agent 并开始处理用户输入
    3. 实时通过 WebSocket 发送：思考状态、工具调用状态、生成的文本片段
    4. 完成后保存对话到数据库

    Args:
        user_id: 用户 ID，用于标识 WebSocket 连接和消息归属
        session_id: 会话 ID，用于加载和保存对话历史
        user_input: 用户输入的文本内容
    """
    try:
        # ============ 第一步：通知客户端开始处理 ============
        # 发送 "thinking" 状态，让前端显示 "正在思考..." 的提示
        await manager.send_status(user_id, "thinking", {"message": "正在思考..."})

        # ============ 第二步：加载历史对话记录 ============
        # 初始化历史消息列表，用于存储转换后的 LangChain 消息对象
        # history_message = []

        # # 如果提供了会话 ID，则从数据库加载该会话的历史消息
        # if session_id:
        #     # 调用数据库服务获取历史消息
        #     db_res = get_messages(session_id)

        #     # 如果数据库返回了消息数据
        #     if db_res.data:
        #         # 遍历每条历史消息
        #         for msg in db_res.data:
        #             # 获取消息的角色（user 或 assistant）
        #             role = msg.get("role")
        #             # 获取消息的内容
        #             content = msg.get("content")

        #             # 根据角色类型，创建对应的 LangChain 消息对象
        #             if role == "user":
        #                 # 用户消息转换为 HumanMessage
        #                 history_message.append(HumanMessage(content=content))

        #             else:
        #                 # AI 助手消息转换为 AIMessage
        #                 history_message.append(AIMessage(content=content))

        # ============ 第三步：构建当前消息 ============
        # 创建当前用户消息，包含用户 ID（供工具使用）和实际请求内容
        current_message = HumanMessage(
            content=f"Request: {user_input}"
        )

        # 将历史消息和当前消息合并，形成完整的对话上下文
        input_message = current_message

        # ============ 第四步：初始化大语言模型 ============
        # 创建 ChatOpenAI 实例，配置模型参数
        llm = ChatOpenAI(
            api_key=API_KEY,  # API 密钥，用于认证
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",  # 阿里云通义千问的兼容接口地址
            model="qwen-plus",  # 使用的模型名称（通义千问 Plus 版本）
            temperature=0,  # 温度参数设为 0，使输出更加确定性（减少随机性）
            streaming=True,  # 启用流式输出，允许逐字符接收响应
        )

        # ============ 第五步：创建 ReAct Agent ============
        # 使用 LangGraph 的 create_react_agent 创建具有工具调用能力的 Agent
        # Agent 可以根据用户请求，自主决定是否调用工具，以及调用哪些工具
        agent_executor = create_react_agent(llm, all_tools, checkpointer=checkpointer)

        # ============ 第六步：配置运行参数 ============
        # 配置字典，用于控制 Agent 的运行行为
        config = {
            "recursion_limit": 50,  # 递归限制：防止 Agent 陷入无限循环调用工具
            "configurable": {
                # 会话唯一标识：用户ID+会话ID，确保记忆隔离
                "thread_id": f"{user_id}_{session_id}",
                # 命名空间：隔离不同业务场景的记忆
                "checkpoint_ns": "agent_stream_service"
            }
        }

        # ============ 第七步：流式运行 Agent 并处理事件 ============
        # 用于累积完整的 AI 响应文本
        full_response = ""

        # 使用 astream_events 异步迭代 Agent 产生的所有事件
        # 这是流式处理的核心，每当有新事件（文本片段、工具调用等）产生时，立即处理
        async for event in agent_executor.astream_events(
            {"messages": input_message},  # 输入：包含历史和当前消息的列表
            version="v1",  # 事件版本，使用 v1 格式
            config=config,  # 运行配置
        ):
            # 获取事件类型
            kind = event["event"]

            # -------- 事件处理：LLM 流式输出 --------
            if kind == "on_chat_model_stream":
                # 当 LLM 产生新的文本片段时触发
                # 从事件数据中提取文本内容
                content = event["data"]["chunk"].content

                # 如果有实际内容（非空）
                if content:
                    # 累加到完整响应中
                    full_response += content
                    # 通过 WebSocket 发送文本片段给客户端，is_final=False 表示还未结束
                    await manager.send_text_chunk(user_id, content, is_final=False)
                    # 短暂延迟 10ms，避免发送过快导致客户端处理不过来
                    await asyncio.sleep(0.01)

            # -------- 事件处理：工具调用开始 --------
            elif kind == "on_tool_start":
                # 当 Agent 开始调用某个工具时触发
                # 获取正在调用的工具名称
                tool_name = event["name"]
                # 获取工具的元数据（展示名称、描述、图标、分类等）
                tool_info = get_tool_display_info(tool_name)
                # 通过 WebSocket 发送工具调用状态给客户端
                await manager.send_status(
                    user_id,
                    "tool_calling",  # 状态类型：正在调用工具
                    {
                        "tool": tool_name,  # 工具的内部名称
                        "display_name": tool_info["display_name"],  # 工具的展示名称
                        "message": tool_info["description"],  # 工具的描述
                        "icon": tool_info["icon"],  # 工具的图标
                        "category": tool_info["category"],  # 工具的分类
                    },
                )

            # -------- 事件处理：工具调用结束 --------
            elif kind == "on_tool_end":
                # 当工具执行完成时触发
                # 获取已完成的工具名称
                tool_name = event["name"]
                # 获取工具的元数据
                tool_info = get_tool_display_info(tool_name)
                # 通过 WebSocket 发送工具完成状态给客户端
                await manager.send_status(
                    user_id,
                    "tool_completed",  # 状态类型：工具执行完成
                    {
                        "tool": tool_name,  # 工具的内部名称
                        "display_name": tool_info["display_name"],  # 工具的展示名称
                        "message": f"{tool_info['display_name']}执行完成",  # 完成提示消息
                        "icon": tool_info["icon"],  # 工具的图标
                        "category": tool_info["category"],  # 工具的分类
                    },
                )

        # ============ 第八步：发送完成状态 ============
        # 发送最终的空文本片段，is_final=True 表示流式输出结束
        await manager.send_text_chunk(user_id, "", is_final=True)
        # 发送 "completed" 状态，通知客户端整个响应已完成
        await manager.send_status(user_id, "completed", {"message": "回答完成"})

        # ============ 第九步：异步保存消息到数据库 ============
        # 打印日志，标记开始保存
        print("---开始保存消息----")

        # 定义内部异步函数，用于保存单条消息到数据库
        async def _save_to_db(sid, role, content):
            """
            异步保存消息到数据库

            Args:
                sid: 会话 ID
                role: 消息角色（user 或 assistant）
                content: 消息内容
            """
            try:
                # 调用数据库服务保存消息
                # 注意：如果 save_message 是阻塞操作，可以考虑用 loop.run_in_executor 包装
                save_message(session_id=sid, role=role, content=content)
            except Exception as e:
                # 记录保存失败的错误，但不影响主流程
                print(f"保存消息失败: {e}")

        # 如果有会话 ID，则保存对话记录
        if session_id:
            # 使用 asyncio.create_task 异步执行保存操作，不阻塞主流程
            # 保存用户消息
            asyncio.create_task(_save_to_db(session_id, "user", user_input))
            # 保存 AI 助手消息
            asyncio.create_task(_save_to_db(session_id, "assistant", full_response))

    # ============ 异常处理 ============
    except Exception as e:
        # 导入 traceback 模块获取详细错误堆栈
        import traceback

        # 格式化完整的错误堆栈信息
        error_details = traceback.format_exc()
        # 打印错误摘要
        print(f"[Agent Stream Error] {e}")
        # 打印详细错误堆栈
        print(f"[Agent Stream Error Details]\n{error_details}")
        # 通过 WebSocket 向客户端发送错误消息
        await manager.send_error(user_id, f"处理出错: {str(e)}")


def get_agent_response(user_id: str, user_input: str):
    """
    同步获取 Agent 响应（保留原有接口兼容性）

    这是一个非流式的同步接口，适用于不需要实时反馈的场景。
    它会等待 Agent 完全处理完毕后，一次性返回完整响应。

    Args:
        user_id: 用户 ID，用于标识请求来源
        user_input: 用户输入的文本内容

    Returns:
        str: 完整的 AI 响应文本
    """
    # 初始化大语言模型（非流式模式）
    llm = ChatOpenAI(
        api_key=API_KEY,  # API 密钥
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",  # 阿里云通义千问接口
        model="qwen-plus",  # 模型名称
        temperature=0,  # 温度参数，0 表示确定性输出
        # 注意：这里没有启用 streaming，因为是同步接口
    )

    # 使用 LangGraph 创建 ReAct Agent
    agent_executor = create_react_agent(llm, all_tools)

    # 同步调用 invoke 方法运行 Agent
    # 将用户 ID 和请求内容组合成消息格式
    result = agent_executor.invoke(
        {"messages": [("user", f"User ID: {user_id}\nRequest: {user_input}")]},
        checkpointer=checkpointer
    )

    # 从结果中提取最后一条消息的内容（即 AI 的最终回复）
    # result["messages"] 是一个消息列表，最后一条是 AI 的回复
    return result["messages"][-1].content
