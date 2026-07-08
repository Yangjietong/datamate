from dotenv import load_dotenv
load_dotenv()

import os
import re
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage
from langchain_openai import ChatOpenAI
from sessionmanager import SessionManager
from tool import get_current_time, ai_search, write_text_to_csv, write_json_to_csv
from visualization_tool import visualize_data, preprocess_data
import token_tracker



api_key = os.getenv("DEEPSEEK_API_KEY")
base_url = os.getenv("DEEPSEEK_BASE_URL")
llm = ChatOpenAI(model="deepseek-v4-pro", base_url=base_url, api_key=api_key)


from mem0 import MemoryClient
memory = MemoryClient()

TOOLS_GENERAL = [ get_current_time, ai_search, write_text_to_csv, write_json_to_csv, visualize_data, preprocess_data]
TOOL_MAP = {t.name: t for t in TOOLS_GENERAL}

# 标记哪些工具需要执行前审批（HITL Approval）
TOOLS_REQUIRING_APPROVAL = {
    "write_text_to_csv",   # CSV 文件写入
    "write_json_to_csv",   # CSV 文件写入
}

with open('AGENT.md', 'r', encoding='utf-8') as file:
    BASE_SYSTEM = file.read()

def request_human_approval(goal: str, tool_name: str, args: dict) -> str:
    """
    审批型 HITL：呈现当前意图、待执行动作与参数、风险提示，等待人输入。
    返回 "approve" | "reject" 或 "reject:原因"
    """
    # 根据工具类型生成不同的风险提示
    risk_hints = {
        "write_text_to_csv": "将创建或覆盖 CSV 文件",
        "write_json_to_csv": "将创建或覆盖 CSV 文件",
    }
    risk_hint = risk_hints.get(tool_name, "该操作需要人工确认")

    print("\n  ---------- [HITL 审批] ----------")
    print("  当前意图：", goal[:100] + ("..." if len(goal) > 100 else ""))
    print("  待执行动作：", tool_name)
    print("  参数：", args)
    print(f"  风险提示：{risk_hint}")
    print("  输入 y 通过 / n 或 n:原因 拒绝 ----------")
    raw = input("  你的决策 (y/n): ").strip().lower()
    if raw.startswith("y") or raw == "yes":
        return "approve"
    if raw.startswith("n") or raw == "no":
        if ":" in raw:
            return "reject:" + raw.split(":", 1)[1].strip()
        return "reject:用户拒绝执行"
    return "reject:无效输入，视为拒绝"

def run_general(
    user_input: str,
    context: list[dict],
    session_id: str,
    session_manager: SessionManager,
    max_steps: int = 10,
    user_id: str = "default_user",
    use_memory: bool = True,
) -> str:
    # 0. 重置本次请求的 token 统计
    token_tracker.reset()

    # 1. 检索相关长期记忆，动态增强 System Prompt
    system_content = BASE_SYSTEM
    if use_memory:
        related = memory.search(query=user_input, filters={"user_id": user_id}, limit=3)
        results = related.get("results") or []
        memories_str = "\n".join(f"- {r.get('memory', r)}" for r in results)
        if memories_str:
            system_content = f"{BASE_SYSTEM}\n\n【用户记忆】\n{memories_str}"

    messages = [SystemMessage(content=system_content)]
    for h in context:
        role, content = h.get("role", ""), h.get("content", "")
        if role == "user":
            messages.append(HumanMessage(content=content))
        elif role == "assistant":
            messages.append(AIMessage(content=content))
    messages.append(HumanMessage(content=user_input))

    llm_with_tools = llm.bind_tools(TOOLS_GENERAL)
    reply = "达到最大步数，未得到最终回复。"
    for _ in range(max_steps):
        response = llm_with_tools.invoke(messages)
        messages.append(response)

        usage = getattr(response, "usage_metadata", None)
        if usage:
            token_tracker.record("主模型(deepseek-v4-pro)", usage.get("input_tokens", 0), usage.get("output_tokens", 0), usage.get("total_tokens", 0))

        if not getattr(response, "tool_calls", None):
            reply = (response.content or "").strip() or "（无回复）"
            break

        for call in response.tool_calls:
            name = call.get("name", "")
            args = call.get("args") or {}
            tid = call.get("id", "")
            fn = TOOL_MAP.get(name)

            if not fn:
                content = f"错误：未知工具 {name}"
            else:
                # HITL 审批逻辑
                if name in TOOLS_REQUIRING_APPROVAL:
                    approval_result = request_human_approval(
                        goal=user_input,
                        tool_name=name,
                        args=args
                    )

                    if approval_result.startswith("reject"):
                        # 用户拒绝，提取拒绝原因
                        reason = approval_result.split(":", 1)[1] if ":" in approval_result else "用户拒绝执行"
                        content = f"工具调用被用户拒绝：{reason}"
                    else:
                        # 用户批准，执行工具
                        content = str(fn.invoke(args))
                else:
                    # 无需审批的工具直接执行
                    content = str(fn.invoke(args))

            messages.append(ToolMessage(content=content, tool_call_id=tid))

    # 2. 短期会话历史
    session_manager.append_history(session_id, "user", user_input)
    session_manager.append_history(session_id, "assistant", reply)

    # 3. 写入长期记忆（让 mem0 从对话中推断并存储）
    if use_memory:
        memory.add(
            [
                {"role": "user", "content": user_input},
                {"role": "assistant", "content": reply},
            ],
            user_id=user_id,
        )

    print(token_tracker.summary())

    return reply


def run_deep_research(
    user_input: str,
    context: list[dict],
    session_id: str,
    session_manager: SessionManager,
    user_id: str = "default_user",
    use_memory: bool = True,
) -> str:
    """深度研究模式：集成长期记忆、HITL、token 统计。

    流程：规划（拆分子问题）→ 检索（联网搜索）→ 合成（生成报告）
    """
    # 0. 重置 token 统计
    token_tracker.reset()

    # 1. 检索相关长期记忆
    system_content = "你是一个深度研究助手，擅长拆解复杂问题、收集证据并撰写报告。"
    if use_memory:
        related = memory.search(query=user_input, filters={"user_id": user_id}, limit=3)
        results = related.get("results") or []
        memories_str = "\n".join(f"- {r.get('memory', r)}" for r in results)
        if memories_str:
            system_content += f"\n\n【用户记忆】\n{memories_str}"

    # 2. 构建对话上下文
    messages = [SystemMessage(content=system_content)]
    for h in context:
        role, content = h.get("role", ""), h.get("content", "")
        if role == "user":
            messages.append(HumanMessage(content=content))
        elif role == "assistant":
            messages.append(AIMessage(content=content))
    messages.append(HumanMessage(content=user_input))

    # ====== 阶段 1: 规划 - 拆分子问题 ======
    print("\n[深度研究] 阶段1：规划子问题...")

    # 复制 messages 并添加规划指令
    plan_messages = messages.copy()
    plan_messages.append(HumanMessage(content=f"""请将上述研究问题拆成多个可独立检索的子问题，每行一个，不要编号和其他内容。例如：
子问题1
子问题2
子问题3
..."""))

    plan_response = llm.invoke(plan_messages)
    plan_text = (plan_response.content or "").strip()

    usage = getattr(plan_response, "usage_metadata", None)
    if usage:
        token_tracker.record("规划阶段(deepseek-v4-pro)", usage.get("input_tokens", 0), usage.get("output_tokens", 0), usage.get("total_tokens", 0))

    lines = [s.strip() for s in plan_text.split("\n") if s.strip()][:3]
    sub_questions = [re.sub(r"^[\d\.\、\s]+", "", s).strip() or s for s in lines]

    if not sub_questions:
        sub_questions = [user_input]

    print(f"[深度研究] 已拆分为 {len(sub_questions)} 个子问题：")
    for i, sq in enumerate(sub_questions, 1):
        print(f"  {i}. {sq}")

    # ====== 阶段 2: 检索 - 联网搜索 ======
    print("\n[深度研究] 阶段2：联网检索证据...")
    evidence_pool = []

    for sq in sub_questions:
        print(f"[深度研究] 检索：{sq}")
        search_result = ai_search.invoke({"query": sq})

        if search_result and not search_result.startswith("错误："):
            evidence_pool.append({
                "sub_question": sq,
                "content": search_result[:1000]  # 限制每条证据长度
            })
        else:
            evidence_pool.append({
                "sub_question": sq,
                "content": f"未找到相关信息：{search_result}"
            })

    evidence_text = "\n\n".join(
        f"【子问题 {i+1}】{e['sub_question']}\n{e['content']}"
        for i, e in enumerate(evidence_pool)
    )

    # ====== 阶段 3: 合成 - 生成报告 ======
    print("\n[深度研究] 阶段3：合成研究报告...")

    # 复制 messages 并添加证据和合成指令
    synth_messages = messages.copy()
    synth_messages.append(HumanMessage(content=f"""以下是从多来源收集到的证据：

{evidence_text}

请根据上述证据，写一份结构化的研究报告（300～600 字），包含：
1. 摘要（一段话概括核心发现）
2. 主要发现（分 2-3 点，每点有依据）
3. 结论与建议

要求：
- 基于证据，不要编造
- 如果证据不足，明确指出
- 使用清晰的中文表达"""))

    report_response = llm.invoke(synth_messages)
    report_text = (report_response.content or "").strip() or "（未能生成报告）"

    usage = getattr(report_response, "usage_metadata", None)
    if usage:
        token_tracker.record("合成阶段(deepseek-v4-pro)", usage.get("input_tokens", 0), usage.get("output_tokens", 0), usage.get("total_tokens", 0))

    # 格式化最终报告
    final_report = f"""【深度研究报告】

研究问题：{user_input}

{report_text}

---
本报告基于 {len(sub_questions)} 个子问题的联网检索结果生成。"""

    # 保存到会话历史
    session_manager.append_history(session_id, "user", user_input)
    session_manager.append_history(session_id, "assistant", final_report)

    # 写入长期记忆
    if use_memory:
        memory.add(
            [
                {"role": "user", "content": user_input},
                {"role": "assistant", "content": final_report},
            ],
            user_id=user_id,
        )

    # 打印 token 统计
    print(token_tracker.summary())

    return final_report
