from langchain_core.tools import tool
import os
import json
import re
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # 使用非交互式后端
from dotenv import load_dotenv
import token_tracker
load_dotenv()
@tool
def visualize_data(data: str, chart_type: str = "auto", filename: str = "chart.png", title: str = "") -> str:
    """根据数据自动生成可视化图表并保存为图片文件。使用 AI 动态生成绘图代码。

    参数:
    - data: 数据内容，支持：
      1. JSON 字符串：[{"name":"A","value":10},{"name":"B","value":20}]
      2. CSV 文本：列名用逗号分隔，每行一条数据
    - chart_type: 图表类型，可选值：
      "auto" - 自动选择（默认）
      "bar" - 柱状图
      "line" - 折线图
      "pie" - 饼图
      "scatter" - 散点图
    - filename: 图片文件名或路径（如 'chart.png' 或 'D:/charts/data.png'）
    - title: 图表标题（可选）
    """
    try:
        # 解析数据
        parsed_data = []
        try:
            # 尝试解析为 JSON
            json_data = json.loads(data)
            if isinstance(json_data, list) and len(json_data) > 0:
                if isinstance(json_data[0], dict):
                    parsed_data = json_data
                else:
                    return "错误：JSON 数据必须是字典列表"
            elif isinstance(json_data, dict):
                parsed_data = [json_data]
            else:
                return "错误：不支持的 JSON 数据格式"
        except json.JSONDecodeError:
            # 尝试解析为 CSV 文本
            lines = data.strip().split('\n')
            if len(lines) < 2:
                return "错误：CSV 数据至少需要表头和一行数据"

            headers = [h.strip() for h in lines[0].split(',')]
            for line in lines[1:]:
                values = [v.strip() for v in line.split(',')]
                if len(values) == len(headers):
                    parsed_data.append(dict(zip(headers, values)))

        if not parsed_data:
            return "错误：无法解析数据"

        # 确保文件名以图片格式结尾
        if not filename.lower().endswith(('.png', '.jpg', '.jpeg', '.svg')):
            filename += '.png'

        # 确保目录存在
        file_path = os.path.abspath(filename)
        parent_dir = os.path.dirname(file_path)
        if parent_dir and not os.path.exists(parent_dir):
            os.makedirs(parent_dir, exist_ok=True)

        # 尝试使用 AI 生成绘图代码（最多重试 2 次）
        max_retries = 2
        for attempt in range(max_retries):
            try:
                print(f"[AI 可视化] 第 {attempt + 1} 次尝试...")
                _ai_visualize(parsed_data, chart_type, file_path, title, attempt)
                print(f"[AI 可视化] 成功！")
                return f"成功：已生成图表，保存到 {file_path}（共 {len(parsed_data)} 条数据）"
            except Exception as e:
                print(f"[AI 可视化] 第 {attempt + 1} 次失败: {type(e).__name__}: {str(e)[:100]}")
                if attempt < max_retries - 1:
                    print("[AI 可视化] 重试中...")
                    continue
                else:
                    print("[AI 可视化] 达到最大重试次数，使用回退逻辑")

        # 回退到原始逻辑
        return _fallback_visualize(parsed_data, chart_type, file_path, title)

    except Exception as e:
        return f"错误：生成可视化图表失败。{type(e).__name__}: {str(e)}"


def _ai_visualize(data: list, chart_type: str, file_path: str, title: str, attempt: int) -> None:
    """使用 AI 生成 matplotlib 绘图代码"""

    # 采样数据（最多 30 条）
    import random
    sample_size = min(30, len(data))
    if len(data) > sample_size:
        sample_data = random.sample(data, sample_size)
    else:
        sample_data = data

    # 提取列信息
    keys = list(data[0].keys()) if data else []

    prompt = f"""请分析以下数据并生成 matplotlib 绘图代码。

数据信息：
- 总行数：{len(data)}
- 列名：{keys}
- 数据样本（{'随机抽取 ' + str(sample_size) + ' 条' if len(data) > sample_size else '全部'}）：
{json.dumps(sample_data, ensure_ascii=False, indent=2)}

绘图要求：
- 图表类型：{chart_type if chart_type != 'auto' else '自动选择最合适的类型（bar/line/pie/scatter）'}
- 保存路径：{file_path}
- 图表标题：{title if title else '根据数据内容生成合适的中文标题'}
- 必须支持中文显示
- 图表尺寸：(10, 6)
- DPI：150
- 需要清理空值和无效数据

请生成一个完整的 Python 函数，函数签名必须是：
```python
def create_chart(data: list, file_path: str) -> None:
    # 你的代码
    # 函数不返回任何值，直接保存图片到 file_path
```

要求：
- 只返回函数代码，不要有任何其他说明文字
- 函数必须命名为 create_chart
- 使用 matplotlib.pyplot 绘图
- 配置中文字体：plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
- 配置负号显示：plt.rcParams['axes.unicode_minus'] = False
- 智能识别数值列和分类列（年份、时间相关的列应作为 X 轴）
- 过滤掉无效数据行（包含空值或无法转换为数字的值）
- 使用 plt.savefig() 保存，然后 plt.close()
- 不要使用 print 语句
{f'- 上次执行失败，请生成更简单、更健壮的代码' if attempt > 0 else ''}

只返回代码，不要有任何解释。"""

    # 调用 DeepSeek
    api_key = os.getenv("DEEPSEEK_API_KEY")
    base_url = os.getenv("DEEPSEEK_BASE_URL")

    from langchain_openai import ChatOpenAI
    llm = ChatOpenAI(model="deepseek-chat", base_url=base_url, api_key=api_key, temperature=0)

    response = llm.invoke(prompt)
    code = response.content.strip()

    usage = getattr(response, "usage_metadata", None)
    if usage:
        token_tracker.record("visualize_data(AI生成)", usage.get("input_tokens", 0), usage.get("output_tokens", 0), usage.get("total_tokens", 0))

    # 清理代码块标记
    code = re.sub(r'```python\n?', '', code)
    code = re.sub(r'```\n?', '', code)
    code = code.strip()

    # 执行生成的代码
    namespace = {
        'json': json,
        're': re,
        'plt': plt,
        'matplotlib': matplotlib,
        'os': os
    }
    exec(code, namespace)

    # 调用生成的函数
    create_func = namespace.get('create_chart')
    if not create_func:
        raise ValueError("生成的代码中没有 create_chart 函数")

    # 执行绘图
    create_func(data, file_path)

    # 验证文件是否生成
    if not os.path.exists(file_path):
        raise ValueError(f"图表文件未生成：{file_path}")


def _fallback_visualize(data: list, chart_type: str, file_path: str, title: str) -> str:
    """回退逻辑：使用原始规则方法绘图"""
    print("[回退逻辑] 使用规则方法进行可视化")

    try:
        # 配置中文字体
        plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
        plt.rcParams['axes.unicode_minus'] = False

        # 提取数值列和分类列
        keys = list(data[0].keys())

        # 步骤1：优先识别时间列作为 X 轴（分类列）
        time_keywords = ["年份", "年", "时间", "日期", "year", "date", "time", "月", "month", "日", "day"]
        category_col = None
        for key in keys:
            key_lower = key.lower()
            if any(kw in key_lower for kw in time_keywords):
                category_col = key
                break

        # 步骤2：识别数值列
        numeric_cols = []
        for key in keys:
            if key == category_col:
                continue

            try:
                valid_count = 0
                for item in data:
                    val = item.get(key)
                    if val and str(val).strip():
                        float(str(val))
                        valid_count += 1

                if valid_count > 0:
                    numeric_cols.append(key)
            except (ValueError, TypeError):
                if category_col is None:
                    category_col = key

        # 步骤3：过滤无效数据行
        filtered_data = []
        for item in data:
            if category_col and not item.get(category_col):
                continue

            has_valid_numeric = False
            if numeric_cols:
                for col in numeric_cols:
                    val = item.get(col)
                    if val and str(val).strip():
                        try:
                            float(str(val))
                            has_valid_numeric = True
                            break
                        except (ValueError, TypeError):
                            pass

            if has_valid_numeric or not numeric_cols:
                filtered_data.append(item)

        if not filtered_data:
            return "错误：过滤后没有有效数据行"

        data = filtered_data

        if not numeric_cols:
            return "错误：数据中没有数值列，无法绘图"

        # 如果是 auto，使用简单规则选择
        if chart_type == "auto":
            if len(data) <= 10 and len(numeric_cols) == 1:
                chart_type = "pie" if category_col else "bar"
            elif len(numeric_cols) >= 2:
                chart_type = "scatter"
            else:
                chart_type = "line" if category_col else "bar"
            print(f"[回退逻辑] 选择图表类型: {chart_type}")

        # 创建图表
        fig, ax = plt.subplots(figsize=(10, 6))

        if chart_type == "bar":
            labels = [str(item.get(category_col, i)) for i, item in enumerate(data)]
            values = [float(item[numeric_cols[0]]) for item in data]
            ax.bar(labels, values)
            ax.set_xlabel(category_col or "类别")
            ax.set_ylabel(numeric_cols[0])
            plt.xticks(rotation=45, ha='right')

        elif chart_type == "line":
            labels = [str(item.get(category_col, i)) for i, item in enumerate(data)]
            values = [float(item[numeric_cols[0]]) for item in data]
            ax.plot(labels, values, marker='o')
            ax.set_xlabel(category_col or "类别")
            ax.set_ylabel(numeric_cols[0])
            plt.xticks(rotation=45, ha='right')

        elif chart_type == "pie":
            labels = [str(item.get(category_col, i)) for i, item in enumerate(data)]
            values = [float(item[numeric_cols[0]]) for item in data]
            ax.pie(values, labels=labels, autopct='%1.1f%%', startangle=90)
            ax.axis('equal')

        elif chart_type == "scatter":
            if len(numeric_cols) < 2:
                return "错误：散点图需要至少两个数值列"
            x_values = [float(item[numeric_cols[0]]) for item in data]
            y_values = [float(item[numeric_cols[1]]) for item in data]
            ax.scatter(x_values, y_values)
            ax.set_xlabel(numeric_cols[0])
            ax.set_ylabel(numeric_cols[1])

        else:
            return f"错误：不支持的图表类型 {chart_type}"

        if title:
            ax.set_title(title)
        else:
            ax.set_title(f"数据可视化 ({chart_type})")

        plt.tight_layout()
        plt.savefig(file_path, dpi=150, bbox_inches='tight')
        plt.close()

        return f"成功：已生成 {chart_type} 图表，保存到 {file_path}（共 {len(data)} 条数据）"

    except Exception as e:
        return f"错误：回退逻辑绘图失败。{type(e).__name__}: {str(e)}"


@tool
def preprocess_data(raw_data: str, extract_table: bool = True) -> str:
    """智能预处理数据，使用 AI 动态生成清洗代码，清洗并标准化为 JSON 格式。

    参数:
    - raw_data: 原始数据，可以是：
      1. 非结构化文本（如 AI 搜索返回的文本）
      2. JSON 字符串
      3. CSV 文本
    - extract_table: 是否从非结构化文本中提取表格数据（默认 True）

    功能：
    - 使用 AI 分析数据格式并生成专门的清洗代码
    - 随机采样数据供 AI 分析（最多 50 行）
    - 智能清洗：去除占位符、货币符号、单位等
    - 失败时自动重试，最终回退到规则方法
    """
    try:
        # 步骤1：采样数据（随机抽取最多 50 行）
        lines = raw_data.strip().split('\n')
        sample_size = min(50, len(lines))

        if len(lines) > sample_size:
            # 随机采样
            import random
            sampled_lines = random.sample(lines, sample_size)
            sample_data = '\n'.join(sampled_lines)
            is_sampled = True
        else:
            sample_data = raw_data
            is_sampled = False

        # 步骤2：尝试使用 AI 生成清洗代码（最多重试 2 次）
        max_retries = 2
        for attempt in range(max_retries):
            try:
                print(f"[AI 预处理] 第 {attempt + 1} 次尝试...")
                result = _ai_preprocess(raw_data, sample_data, is_sampled, attempt)
                print(f"[AI 预处理] 成功！")
                return result
            except Exception as e:
                print(f"[AI 预处理] 第 {attempt + 1} 次失败: {type(e).__name__}: {str(e)[:100]}")
                if attempt < max_retries - 1:
                    print("[AI 预处理] 重试中...")
                    continue
                else:
                    print("[AI 预处理] 达到最大重试次数，使用回退逻辑")

        # 步骤3：回退到原始规则逻辑
        return _fallback_preprocess(raw_data, extract_table)

    except Exception as e:
        return f"错误：数据预处理失败。{type(e).__name__}: {str(e)}"


def _ai_preprocess(raw_data: str, sample_data: str, is_sampled: bool, attempt: int) -> str:
    """使用 AI 生成代码进行预处理"""

    sample_lines = len(sample_data.split('\n'))
    prompt = f"""请分析以下数据样本并生成 Python 代码来清洗和提取结构化数据。

数据样本{'（随机抽取 ' + str(sample_lines) + ' 行）' if is_sampled else '（完整数据）'}：
{sample_data}

任务：
1. 识别数据格式（JSON、CSV、键值对文本、表格等）
2. 提取所有有效的结构化数据
3. 智能清洗：
   - 识别并移除占位符（如"未公开"、"暂无"、"-"、"无数据"、"N/A"等）
   - 去除货币符号（¥、$、元）、单位（克、个、件）
   - 标准化数值格式（去除逗号，统一小数点）
   - 处理缺失值和异常值
4. 返回标准格式：列表中包含字典，每个字典代表一条记录

请生成一个完整的 Python 函数，函数签名必须是：
```python
def clean_data(raw_text: str) -> list:
    # 你的代码
    return result  # 必须返回 list[dict]
```

要求：
- 只返回函数代码，不要有任何其他说明文字或注释
- 函数必须命名为 clean_data
- 可以使用 json, re 等标准库（不要导入外部库）
- 代码要健壮，处理边界情况（空行、格式错误等）
- 确保返回的是 list[dict] 格式，不能是空列表
- 不要使用 print 语句
{f'- 上次执行失败，请生成更简单、更健壮的代码，避免复杂的逻辑' if attempt > 0 else ''}

只返回代码，不要有任何解释。"""

    # 调用 DeepSeek
    api_key = os.getenv("DEEPSEEK_API_KEY")
    base_url = os.getenv("DEEPSEEK_BASE_URL")

    from langchain_openai import ChatOpenAI
    llm = ChatOpenAI(model="deepseek-chat", base_url=base_url, api_key=api_key, temperature=0)

    response = llm.invoke(prompt)
    code = response.content.strip()

    usage = getattr(response, "usage_metadata", None)
    if usage:
        token_tracker.record("preprocess_data(AI生成)", usage.get("input_tokens", 0), usage.get("output_tokens", 0), usage.get("total_tokens", 0))

    # 清理代码块标记
    code = re.sub(r'```python\n?', '', code)
    code = re.sub(r'```\n?', '', code)
    code = code.strip()

    print(f"[AI 预处理] 生成的代码长度: {len(code)} 字符")

    # 执行生成的代码
    namespace = {'json': json, 're': re}
    exec(code, namespace)

    # 调用生成的函数
    clean_func = namespace.get('clean_data')
    if not clean_func:
        raise ValueError("生成的代码中没有 clean_data 函数")

    # 处理完整数据
    result = clean_func(raw_data)

    if not isinstance(result, list):
        raise ValueError(f"clean_data 返回类型错误，期望 list，实际 {type(result).__name__}")

    if len(result) == 0:
        raise ValueError("clean_data 返回空列表，没有提取到有效数据")

    # 验证第一条数据是字典
    if result and not isinstance(result[0], dict):
        raise ValueError(f"返回数据格式错误，期望 list[dict]，实际 list[{type(result[0]).__name__}]")

    # 转为 JSON
    return json.dumps(result, ensure_ascii=False)


def _fallback_preprocess(raw_data: str, extract_table: bool) -> str:
    """回退逻辑：使用原始规则方法"""
    print("[回退逻辑] 使用规则方法进行数据预处理")
    try:
        # 步骤1：尝试直接解析为 JSON
        try:
            data = json.loads(raw_data)
            if isinstance(data, list) and len(data) > 0:
                # 已经是结构化数据，进行清洗
                cleaned = _clean_structured_data(data)
                return json.dumps(cleaned, ensure_ascii=False)
        except json.JSONDecodeError:
            pass

        # 步骤2：尝试解析为 CSV
        lines = raw_data.strip().split('\n')
        csv_data = []
        for line in lines:
            if ',' in line or '\t' in line:
                # 可能是 CSV 或制表符分隔
                separator = '\t' if '\t' in line else ','
                values = [v.strip() for v in line.split(separator)]
                csv_data.append(values)

        if len(csv_data) >= 2:
            # 转换 CSV 为字典列表
            headers = csv_data[0]
            data_rows = []
            for row in csv_data[1:]:
                if len(row) == len(headers):
                    data_rows.append(dict(zip(headers, row)))

            if data_rows:
                cleaned = _clean_structured_data(data_rows)
                return json.dumps(cleaned, ensure_ascii=False)

        # 步骤3：从非结构化文本中提取表格
        if extract_table:
            extracted = _extract_table_from_text(raw_data)
            if extracted:
                cleaned = _clean_structured_data(extracted)
                return json.dumps(cleaned, ensure_ascii=False)

        return "错误：无法从数据中提取有效的表格结构"

    except Exception as e:
        return f"错误：回退逻辑失败。{type(e).__name__}: {str(e)}"


def _extract_table_from_text(text: str) -> list:
    """从非结构化文本中提取表格数据"""
    lines = text.strip().split('\n')

    # 查找表格特征：包含多个数字或结构化数据的行
    table_lines = []
    for line in lines:
        # 跳过太短的行
        if len(line.strip()) < 5:
            continue

        # 检测是否包含结构化数据的特征
        # 1. 包含冒号分隔的键值对
        # 2. 包含数字
        if ':' in line or '：' in line:
            table_lines.append(line)
        elif re.search(r'\d+\.?\d*', line):
            # 包含数字
            table_lines.append(line)

    if not table_lines:
        return []

    # 尝试提取键值对格式的数据
    extracted_data = []
    current_item = {}

    for line in table_lines:
        # 检测键值对格式：名称:值 或 名称：值
        matches = re.findall(r'([^:：,，]+)[：:]([^,，\n]+)', line)

        if matches:
            for key, value in matches:
                key = key.strip()
                value = value.strip()

                # 如果当前项已经有数据且遇到重复的键，说明是新的一条记录
                if key in current_item and current_item:
                    extracted_data.append(current_item)
                    current_item = {}

                current_item[key] = value

        # 检测表格行格式（用逗号或制表符分隔）
        elif ',' in line or '\t' in line:
            separator = '\t' if '\t' in line else ','
            parts = [p.strip() for p in line.split(separator)]
            if len(parts) >= 2:
                # 假设第一列是键，后续是值
                if not extracted_data:
                    # 可能是表头
                    continue
                else:
                    # 数据行
                    item = {}
                    for i, part in enumerate(parts):
                        item[f"列{i+1}"] = part
                    extracted_data.append(item)

    # 添加最后一个项
    if current_item:
        extracted_data.append(current_item)

    return extracted_data


def _ai_select_chart_type(data: list, numeric_cols: list, category_col: str) -> str:
    """使用 DeepSeek-v4-pro 智能分析数据并选择最佳图表类型"""
    try:
        # 准备数据样本（如果数据超过 10 条，只取前 10 条传给 LLM）
        sample_data = data[:10] if len(data) > 10 else data

        # 构建分析提示
        prompt = f"""请分析以下数据，并推荐最合适的图表类型。

数据信息：
- 总行数：{len(data)}
- 数值列：{numeric_cols}
- 分类列：{category_col or "无"}
- 数据样本（前 10 条）：
{json.dumps(sample_data, ensure_ascii=False, indent=2)}

可选图表类型：
1. bar（柱状图）：适合比较不同类别的数值
2. line（折线图）：适合展示趋势或时间序列
3. pie（饼图）：适合展示占比关系，数据条目不宜过多（≤10）
4. scatter（散点图）：适合展示两个数值变量之间的关系，需要至少两个数值列

请只返回一个 JSON 对象，格式：{{"chart_type": "类型", "reason": "原因"}}
不要返回其他任何内容，包括代码块标记。"""

        # 调用 DeepSeek API
        api_key = os.getenv("DEEPSEEK_API_KEY")
        base_url = os.getenv("DEEPSEEK_BASE_URL")

        from langchain_openai import ChatOpenAI
        llm = ChatOpenAI(model="deepseek-chat", base_url=base_url, api_key=api_key, temperature=0)

        response = llm.invoke(prompt)
        result_text = response.content.strip()

        # 解析 LLM 返回的 JSON
        # 去除可能的 markdown 代码块标记
        result_text = re.sub(r'```json\n?', '', result_text)
        result_text = re.sub(r'```\n?', '', result_text)
        result_text = result_text.strip()

        result = json.loads(result_text)
        chart_type = result.get("chart_type", "bar")
        reason = result.get("reason", "")

        print(f"[AI 推荐理由] {reason}")

        # 验证图表类型是否有效
        valid_types = ["bar", "line", "pie", "scatter"]
        if chart_type not in valid_types:
            print(f"[警告] AI 返回了无效的图表类型 '{chart_type}'，使用默认值 'bar'")
            return "bar"

        return chart_type

    except Exception as e:
        print(f"[警告] AI 选择图表类型失败：{e}，使用回退逻辑")
        # AI 失败时的回退逻辑
        if len(data) <= 10 and len(numeric_cols) == 1:
            return "pie" if category_col else "bar"
        elif len(numeric_cols) >= 2:
            return "scatter"
        else:
            return "bar"