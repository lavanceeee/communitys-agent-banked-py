import os
import json
import asyncio
import aiohttp
from typing import Optional
from langchain_core.tools import tool
from dotenv import load_dotenv

load_dotenv()

# 从环境变量获取配置
API_KEY = os.getenv("API_KEY")
CREATE_TEXT_URL = os.getenv("QWEN_CREATE_TEXT_URL")
GET_RESULT_URL = os.getenv("QWEN_GET_RESULT_URL")


@tool
async def generate_image_from_text(
    prompt: str, size: Optional[str] = "1024*1024", n: Optional[int] = 1
) -> str:
    """
    根据文本描述生成图片 (使用通义万相 text2image API).

    Args:
        prompt: 图片描述提示词
        size: 图片尺寸, 默认为 "1024*1024". 可选值: "1024*1024", "720*1280", "1280*720"
        n: 生成数量, 默认为 1 (API限制通常为1-4)

    Returns:
        生成的图片URL的JSON字符串
    """
    if not API_KEY or not CREATE_TEXT_URL or not GET_RESULT_URL:
        return json.dumps(
            {
                "success": False,
                "error": "Missing Configuration",
                "message": "API key or URLs are missing in environment variables.",
            }
        )

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "X-DashScope-Async": "enable",
    }

    payload = {
        "model": "wanx-v1",
        "input": {"prompt": prompt},
        "parameters": {"style": "<auto>", "size": size, "n": n},
    }

    try:
        async with aiohttp.ClientSession() as session:
            # 1. 提交任务
            async with session.post(
                CREATE_TEXT_URL, headers=headers, json=payload
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    return json.dumps(
                        {
                            "success": False,
                            "error": "API Error",
                            "message": f"Failed to submit task. Status: {response.status}",
                            "detail": error_text,
                        },
                        ensure_ascii=False,
                    )

                result = await response.json()
                if "output" not in result or "task_id" not in result["output"]:
                    return json.dumps(
                        {
                            "success": False,
                            "error": "Invalid Response",
                            "message": "Task ID not found in response",
                            "detail": result,
                        },
                        ensure_ascii=False,
                    )

                task_id = result["output"]["task_id"]
                print(f"Image generation task submitted. Task ID: {task_id}")

            # 2. 轮询结果
            task_status = "PENDING"
            wait_time = 1
            max_retries = 30  # 30 * (1~2s) approx 60s max wait

            for attempt in range(max_retries):
                await asyncio.sleep(wait_time)

                check_url = f"{GET_RESULT_URL}/{task_id}"
                async with session.get(check_url, headers=headers) as check_response:
                    if check_response.status != 200:
                        # 简单的重试逻辑或直接报错
                        continue

                    check_result = await check_response.json()

                    if "output" in check_result:
                        task_status = check_result["output"]["task_status"]

                        if task_status == "SUCCEEDED":
                            # 成功，返回结果
                            # result format: output: { task_status: "SUCCEEDED", results: [ { url: "..." } ] }
                            if "results" in check_result["output"]:
                                return json.dumps(
                                    {
                                        "success": True,
                                        "task_id": task_id,
                                        "images": check_result["output"]["results"],
                                    },
                                    ensure_ascii=False,
                                )
                            else:
                                return json.dumps(
                                    {
                                        "success": False,
                                        "error": "No Results",
                                        "message": "Task succeeded but no image results found.",
                                    },
                                    ensure_ascii=False,
                                )

                        elif task_status == "FAILED":
                            return json.dumps(
                                {
                                    "success": False,
                                    "error": "Generation Failed",
                                    "message": check_result["output"].get(
                                        "message", "Unknown error"
                                    ),
                                },
                                ensure_ascii=False,
                            )

                        # else PENDING or RUNNING, continue loop

            return json.dumps(
                {
                    "success": False,
                    "error": "Timeout",
                    "message": "Image generation timed out.",
                },
                ensure_ascii=False,
            )

    except Exception as e:
        return json.dumps(
            {"success": False, "error": "Exception", "message": str(e)},
            ensure_ascii=False,
        )
