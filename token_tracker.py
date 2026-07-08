_usage_log = []


def reset():
    """开始处理新请求前清空记录"""
    _usage_log.clear()


def record(source: str, prompt_tokens: int, completion_tokens: int, total_tokens: int):
    """记录一次 LLM 调用的 token 消耗"""
    _usage_log.append({
        "source": source,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": total_tokens,
    })


def summary() -> str:
    """返回本次请求的 token 消耗明细及合计"""
    if not _usage_log:
        return "[Token 统计] 本次请求未记录 token 消耗"

    lines = ["[Token 统计] 本次请求明细："]
    total = 0
    for entry in _usage_log:
        lines.append(
            f"  - {entry['source']}: 输入 {entry['prompt_tokens']}，"
            f"输出 {entry['completion_tokens']}，总计 {entry['total_tokens']}"
        )
        total += entry["total_tokens"]
    lines.append(f"  合计：{total} tokens")
    return "\n".join(lines)
