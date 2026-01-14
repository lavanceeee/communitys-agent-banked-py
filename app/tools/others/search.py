import os
import json
import aiohttp
from langchain_core.tools import tool
from dotenv import load_dotenv

load_dotenv()

SERP_KEY = os.getenv("SERP_KEY")


@tool
async def web_search(query: str):
    """
    使用 Google 搜索联网查询信息。
    当用户询问无法直接回答的实时信息、新闻、百科知识时，使用此工具。
    返回搜索结果的摘要。

    Args:
        query: 搜索关键词
    """
    if not SERP_KEY:
        return "Error: SERP_KEY not configured."

    url = "https://serpapi.com/search"
    params = {
        "engine": "google",
        "q": query,
        "api_key": SERP_KEY,
        "hl": "zh-cn",  # 默认使用中文界面
        "gl": "cn",  # 默认位置中国
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status != 200:
                    return (
                        f"Error: SerpApi request failed with status {response.status}"
                    )

                data = await response.json()

                # 提取有用的信息
                results = []

                # 1. Answer Box (直接答案)
                if "answer_box" in data:
                    box = data["answer_box"]
                    if "answer" in box:
                        results.append(f"【直接答案】: {box['answer']}")
                    elif "snippet" in box:
                        results.append(f"【直接答案】: {box['snippet']}")

                # 2. Sports Results
                if "sports_results" in data:
                    results.append(
                        f"【体育结果】: {json.dumps(data['sports_results'], ensure_ascii=False)}"
                    )

                # 3. Knowledge Graph (知识图谱)
                if "knowledge_graph" in data:
                    kg = data["knowledge_graph"]
                    title = kg.get("title", "")
                    desc = kg.get("description", "")
                    results.append(f"【知识图谱】{title}: {desc}")

                # 4. Organic Results (自然搜索结果)
                if "organic_results" in data:
                    for res in data["organic_results"][:5]:  # 取前5条
                        title = res.get("title", "")
                        snippet = res.get("snippet", "")
                        link = res.get("link", "")
                        results.append(
                            f"【搜索结果】{title}\n摘要: {snippet}\n链接: {link}"
                        )

                if not results:
                    return "No relevant search results found."

                return "\n\n".join(results)

    except Exception as e:
        return f"Error performing search: {str(e)}"


@tool
async def wikipedia_search(query: str, lang: str = "zh"):
    """
    使用维基百科搜索查询信息。
    当用户需要了解详细的历史背景、人物生平、专有名词解释时，使用此工具。
    返回最相关词条的摘要。

    Args:
        query: 搜索关键词
        lang: 语言代码，默认为中文 "zh"，英文为 "en"
    """
    url = f"https://{lang}.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "format": "json",
        "list": "search",
        "srsearch": query,
        "srlimit": 1,  # 只取最相关的一条
        "utf8": 1,
    }

    try:
        async with aiohttp.ClientSession() as session:
            # 1. 搜索词条
            async with session.get(url, params=params) as response:
                if response.status != 200:
                    return (
                        f"Error: Wikipedia request failed with status {response.status}"
                    )
                data = await response.json()

            if not data.get("query", {}).get("search"):
                return "No relevant Wikipedia pages found."

            page_title = data["query"]["search"][0]["title"]

            # 2. 获取词条详细摘要
            detail_params = {
                "action": "query",
                "format": "json",
                "prop": "extracts",
                "exintro": 1,  # 只取摘要
                "explaintext": 1,  # 纯文本，不要 HTML
                "titles": page_title,
                "utf8": 1,
            }

            async with session.get(url, params=detail_params) as response:
                if response.status != 200:
                    return f"Error: Wikipedia detail request failed with status {response.status}"
                detail_data = await response.json()

            pages = detail_data.get("query", {}).get("pages", {})
            for page_id, page_info in pages.items():
                if page_id == "-1":
                    continue
                extract = page_info.get("extract", "")
                return f"【维基百科-{page_title}】\n{extract}"

            return "Failed to retrieve page content."

    except Exception as e:
        return f"Error performing Wikipedia search: {str(e)}"


@tool
async def toutiao_hot_news(limit: int = 10):
    """
    获取今日头条实时热榜新闻。
    当用户询问"今天发生了什么"、"热门新闻"、"头条热榜"时，使用此工具。
    返回热点新闻标题和链接列表。

    Args:
        limit: 返回的新闻条数限制，默认为 10 条
    """
    url = "https://tenapi.cn/v2/toutiaohotnew"
    # 添加 User-Agent 头，防止被 API 拦截
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status != 200:
                    return f"Error: Toutiao API request failed with status {response.status}"

                try:
                    data = await response.json()
                except Exception:
                    # 如果不能解析 JSON，尝试返回前 100 个字符
                    text = await response.text()
                    return (
                        f"Error: Failed to parse JSON. Response preview: {text[:100]}"
                    )

                if data.get("code") != 200:
                    try:
                        msg = data.get("msg", "Unknown error")
                        return f"Error: API returned error code {data.get('code')}, msg: {msg}"
                    except Exception:
                        return f"Error: API returned error code {data.get('code')}"

                news_list = data.get("data", [])
                if not news_list:
                    return "No hot news found."

                # 格式化输出
                results = ["【今日头条热榜】"]
                for i, news in enumerate(news_list[:limit], 1):
                    name = news.get("name", "Unknown Title")
                    link = news.get("url", "#")
                    results.append(f"{i}. {name}\n   链接: {link}")

                return "\n".join(results)

    except Exception as e:
        return f"Error fetching toutiao hot news: {str(e)}"


@tool
async def search_domains_info(query: str, limit: int = 10):
    """
    Search for domain information using DomainsDB API.
    Use this tool when users ask about domain availability, registration details, or domain lists containing specific keywords.

    Args:
        query: domain keyword to search for (e.g., "example")
        limit: number of results to return (default 10)
    """
    api_key = os.getenv("DOMAINSDB_KEY")
    if not api_key:
        return "Error: DOMAINSDB_KEY not configured."

    url = "https://api.domainsdb.info/v1/domains/search"
    params = {"api_key": api_key, "domain": query, "limit": limit}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status != 200:
                    return (
                        f"Error: DomainsDB request failed with status {response.status}"
                    )

                data = await response.json()

                domains = data.get("domains", [])
                if not domains:
                    return "No domains found."

                results = [
                    f"Found {data.get('total', 0)} domains, showing top {len(domains)}:"
                ]

                for d in domains:
                    name = d.get("domain", "N/A")
                    country = d.get("country", "N/A")
                    create_date = d.get("create_date", "N/A")
                    is_dead = d.get("isDead", "N/A")
                    # Format as a concise block
                    info = f"• {name} ({country}) - Created: {create_date}, Dead: {is_dead}"
                    results.append(info)

                return "\n".join(results)

    except Exception as e:
        return f"Error performing domain search: {str(e)}"
