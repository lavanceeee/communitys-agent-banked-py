from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import os

llm = ChatOpenAI(
    api_key=os.getenv("API_KEY"),
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    model="qwen-plus",
    temperature=0.3,
)

prompt = ChatPromptTemplate.from_template(
    """你是一个专业的对话总结助手。
请根据用户的输入内容，生成一个简短的会话标题。

要求：
1. 长度控制在 10 个字符以内。
2. 只要返回标题文本，不要包含引号或其他标点。
3. 如果输入太短或无意义，返回 "新会话"。

用户输入: {content}

标题:"""
)

title_chain = prompt | llm | StrOutputParser()


async def generate_title(content: str) -> str:
    try:
        title = await title_chain.ainvoke({"content": content})
        return title.strip()
    except Exception as e:
        print(f"生成标题失败: {e}")
        return "新会话"
