from langchain_core.tools import tool
import os
import json
import csv
from dotenv import load_dotenv
from openai import OpenAI
import token_tracker
load_dotenv()

QIANFAN_API_KEY = os.getenv("QIANFAN_API_KEY")

@tool
def get_current_time() -> str:
    """获取当前日期和时间。

    使用场景：
    1. 用户直接询问当前时间或日期
    2. **重要**：用户询问"最新"、"近期"、"今年"、"最近"等时效性内容时，必须先调用此工具获取当前日期，然后将日期信息传给 ai_search

    返回格式：YYYY-MM-DD HH:MM:SS (例如：2026-07-08 14:30:00)
    """
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

@tool
def ai_search(query: str) -> str:
    """联网搜索最新资讯、新闻、实时信息。

    使用场景：用户询问需要联网检索的信息

    **重要提示**：
    - 如果用户询问"最新"、"近期"、"今年"、"最近"等时效性内容，请先调用 get_current_time 获取当前日期
    - 然后将日期信息（如"2026年7月"）加入到搜索查询中
    - 例如：用户问"最新AI发展" → 先获取时间"2026-07-08" → 搜索"2026年AI人工智能最新发展"

    参数：
    - query: 搜索问题（应包含时间信息，如"2026年XX"）

    返回：搜索结果文本
    """
    if not QIANFAN_API_KEY:
        return "错误：未配置 QIANFAN_API_KEY，无法调用 AI 搜索。"

    print(f"调用ai_search")
    print(f"[调试] 查询内容: {query}")

    # 自动检测并补充当前年份（如果查询中包含"最新"等时效性词汇但没有年份）
    from datetime import datetime
    current_year = datetime.now().year
    time_keywords = ["最新", "近期", "今年", "最近", "当前", "现在"]
    has_time_keyword = any(kw in query for kw in time_keywords)
    has_year = any(str(year) in query for year in range(2020, current_year + 2))

    if has_time_keyword and not has_year:
        # 如果有时效性关键词但没有年份，自动加上当前年份
        query = f"{current_year}年{query}"
        print(f"[调试] 自动补充年份后: {query}")

    try:
        # 创建 OpenAI 客户端，使用千帆 AI 搜索接口
        client = OpenAI(
            api_key=QIANFAN_API_KEY,
            base_url="https://qianfan.baidubce.com/v2/ai_search",
            timeout=60.0,  # 设置 60 秒超时
            max_retries=2  # 自动重试 2 次
        )

        # 调用聊天接口
        response = client.chat.completions.create(
            model="deepseek-v4-pro",
            messages=[
                {"role": "user", "content": query}
            ],
            stream=False
        )

        content = response.choices[0].message.content
        if not content:
            return "错误：未获取到有效内容"

        usage = response.usage
        if usage:
            print(f"[调试] Token 消耗：输入 {usage.prompt_tokens}，输出 {usage.completion_tokens}，总计 {usage.total_tokens}")
            token_tracker.record("ai_search", usage.prompt_tokens, usage.completion_tokens, usage.total_tokens)

        print(f"[调试] 获取到内容，长度: {len(content)}")
        return content

    except Exception as e:
        error_type = type(e).__name__
        error_msg = str(e)

        # 特殊处理 SSL 连接错误
        if "SSL" in error_msg or "EOF" in error_msg or "ConnectError" in error_type:
            return "错误：连接千帆 AI 搜索服务失败（SSL/网络问题），请稍后重试或检查网络环境。"

        return f"错误：AI 搜索请求失败。{error_type}: {error_msg}"


@tool
def write_text_to_csv(content: str, filename: str) -> str:
    """将纯文本内容写入 CSV 文件。文本应该是已格式化好的 CSV 格式（包含表头），每行用换行符分隔，列用逗号分隔。

    参数:
    - content: CSV 格式的文本内容，如 "列1,列2,列3\n值1,值2,值3"
    - filename: CSV 文件名或完整路径（如 'output.csv' 或 'D:/data/output.csv'）
    """
    try:
        # 确保文件名以 .csv 结尾
        if not filename.endswith('.csv'):
            filename += '.csv'

        # 如果是相对路径，确保父目录存在
        file_path = os.path.abspath(filename)
        parent_dir = os.path.dirname(file_path)
        if parent_dir and not os.path.exists(parent_dir):
            os.makedirs(parent_dir, exist_ok=True)

        # 直接写入文本内容
        with open(file_path, 'w', encoding='utf-8-sig', newline='') as f:
            f.write(content)

        line_count = len([line for line in content.split('\n') if line.strip()])
        return f"成功：已将 {line_count} 行数据写入到 {file_path}"

    except Exception as e:
        return f"错误：写入 CSV 失败。{type(e).__name__}: {str(e)}"


@tool
def write_json_to_csv(json_data: str, filename: str) -> str:
    """将 JSON 格式的数据转换并写入 CSV 文件。适合结构化数据。

    参数:
    - json_data: JSON 格式字符串，支持：
      1. 字典列表：[{"name":"A","value":1},{"name":"B","value":2}]
      2. 单个字典：{"name":"A","value":1}
    - filename: CSV 文件名或完整路径（如 'output.csv' 或 'D:/data/output.csv'）
    """
    try:
        # 确保文件名以 .csv 结尾
        if not filename.endswith('.csv'):
            filename += '.csv'

        # 如果是相对路径，确保父目录存在
        file_path = os.path.abspath(filename)
        parent_dir = os.path.dirname(file_path)
        if parent_dir and not os.path.exists(parent_dir):
            os.makedirs(parent_dir, exist_ok=True)

        # 解析 JSON
        data = json.loads(json_data)

        rows_to_write = []
        headers = None

        if isinstance(data, dict):
            # 单个字典：键作为表头
            headers = list(data.keys())
            rows_to_write = [list(data.values())]

        elif isinstance(data, list):
            if not data:
                return "错误：JSON 数据为空列表"

            if isinstance(data[0], dict):
                # 字典列表：提取所有键作为表头
                all_keys = set()
                for item in data:
                    if isinstance(item, dict):
                        all_keys.update(item.keys())
                headers = sorted(list(all_keys))
                rows_to_write = [[item.get(key, '') for key in headers] for item in data]
            else:
                return "错误：JSON 列表中的元素必须是字典"
        else:
            return f"错误：不支持的 JSON 数据类型 {type(data).__name__}"

        # 写入 CSV 文件
        with open(file_path, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.writer(f)
            if headers:
                writer.writerow(headers)
            writer.writerows(rows_to_write)

        row_count = len(rows_to_write)
        return f"成功：已将 {row_count} 行数据写入到 {file_path}"

    except json.JSONDecodeError as e:
        return f"错误：JSON 解析失败。{str(e)}"
    except Exception as e:
        return f"错误：写入 CSV 失败。{type(e).__name__}: {str(e)}"
