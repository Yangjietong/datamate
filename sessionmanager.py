import uuid
from dotenv import load_dotenv
load_dotenv()

import os
import re
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_openai import ChatOpenAI

sum_api_key = os.getenv("DEEPSEEK_API_KEY")
sum_base_url = os.getenv("DEEPSEEK_BASE_URL")
sum_model = "deepseek-v4-flash"

ROUND_SIZE = 2          # 一轮对话 = user + assistant 两条消息
SUMMARY_EVERY = 5       # 每 5 轮总结一次
SUMMARY_BATCH = ROUND_SIZE * SUMMARY_EVERY  # 每次折叠的消息条数（10）

class SessionManager:
    def __init__(self):
        self._sessions:dict[str, dict]={}
        self._history:dict[str, list[dict]]={}
        self._memory:dict[str, str]={}            # 每个会话的累积摘要（记忆）
        self._summarized_count:dict[str, int]={}  # 水位线：已折叠进摘要的消息条数
        self._summarizer = ChatOpenAI(
            model=sum_model,
            api_key=sum_api_key,
            base_url=sum_base_url,
            temperature=0.3,
        )
    
    def create_session(self, user_id: str):
        session_id = f"{user_id}_{uuid.uuid4().hex[:8]}"
        session = {"id":session_id, "user_id":user_id, "last_agent":None, "last_message":None}
        self._sessions[session_id] = session
        self._history[session_id]=[]
        self._memory[session_id]=""
        self._summarized_count[session_id]=0
        return session

    def restore_session(self, session_id: str, user_id: str, history: list[dict], last_agent: str | None = None):
        """从持久化存储恢复一个会话（用于跨进程恢复对话）。

        history 中的消息会被视为未折叠的原始消息，重新接入摘要机制。
        """
        if session_id not in self._sessions:
            self._sessions[session_id] = {
                "id": session_id, "user_id": user_id,
                "last_agent": last_agent, "last_message": None
            }
            self._history[session_id] = []
            self._memory[session_id] = ""
            self._summarized_count[session_id] = 0

        self._history[session_id].extend(history)
        self._maybe_summarize(session_id)
        return self._sessions[session_id]
    
    def get_session(self, session_id: str):
        return self._sessions.get(session_id)
    
    def update_session(self, session_id: str, updates: dict):
        if session_id in self._sessions:
            return self._sessions[session_id].update(updates)
    
    def append_history(self, session_id: str, role: str, content: str):
        if session_id in self._history:
            self._history[session_id].append({"role":role, "content":content})
            self._maybe_summarize(session_id)

    def _maybe_summarize(self, session_id: str):
        """当未折叠的新消息累计满一个批次（5 轮 = 10 条）时，把它们折叠进摘要。"""
        hist = self._history.get(session_id, [])
        done = self._summarized_count.get(session_id, 0)
        # 只要积压的新消息够一个批次就折叠（防止一次性补很多消息时漏总结）
        while len(hist) - done >= SUMMARY_BATCH:
            batch = hist[done:done + SUMMARY_BATCH]
            summary = self._summarize(self._memory.get(session_id, ""), batch)
            if summary is None:
                # 总结失败：水位线不前进，下次再试，不影响主流程
                break
            self._memory[session_id] = summary
            done += SUMMARY_BATCH
            self._summarized_count[session_id] = done

    def _summarize(self, prev_summary: str, batch: list[dict]) -> str | None:
        """把已有摘要与新一批对话合并成新的摘要；失败返回 None。"""
        convo = "\n".join(f"{m['role']}: {m['content']}" for m in batch)
        prompt = (
            "你是对话记忆助手。请把【已有摘要】和【新增对话】整合成一份简洁、连贯的中文摘要，"
            "保留关键事实、用户偏好、未决事项，去掉寒暄与冗余。只输出摘要正文。\n\n"
            f"【已有摘要】\n{prev_summary or '（无）'}\n\n"
            f"【新增对话】\n{convo}"
        )
        try:
            resp = self._summarizer.invoke([HumanMessage(content=prompt)])
            text = (resp.content or "").strip()
            return text or None
        except Exception:
            return None
    
    def get_history(self, session_id: str, limit: int) -> list[dict]:
        hist = self._history.get(session_id, [])
        done = self._summarized_count.get(session_id, 0)
        summary = self._memory.get(session_id, "")

        # 未折叠进摘要的原始消息
        unsummarized = hist[done:]
        # 只保留最近 limit 条原始消息
        if limit is not None and limit >= 0:
            unsummarized = unsummarized[-limit:]

        result: list[dict] = []
        if summary:
            result.append({"role": "system", "content": f"以下是之前对话的摘要：\n{summary}"})
        result.extend(unsummarized)
        return result
