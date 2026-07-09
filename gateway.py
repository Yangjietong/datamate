from route import route
from sessionmanager import SessionManager
from memory import run_general, run_deep_research
from conversation_manager import ConversationManager
from typing import Any
import os
from dotenv import load_dotenv

load_dotenv()

class Gateway:
    def __init__(self, session_manager: SessionManager) -> None:
        self.session_manager = session_manager
        self.conversation_manager = ConversationManager()

        # 自动检测是否启用长期记忆
        # 如果配置了 MEM0_API_KEY，则启用；否则禁用
        self.use_memory = bool(os.getenv("MEM0_API_KEY"))

        if self.use_memory:
            print("[INFO] Long-term memory ENABLED (MEM0_API_KEY configured)")
        else:
            print("[INFO] Long-term memory DISABLED (MEM0_API_KEY not configured)")

    def handle_request(
        self,
        user_id: str,
        message: str,
        session_id: str | None = None,
    ) -> dict[str, Any]:
        if not session_id:
            session = self.session_manager.create_session(user_id)
            session_id = session["id"]
        else:
            session = self.session_manager.get_session(session_id)
            if not session:
                return {"response": "错误：会话不存在或已过期。", "session_id": session_id or "", "error": "session_not_found"}

        agent_id = route(message)
        history = self.session_manager.get_history(session_id, limit=10)
        if agent_id == "deep_research_agent":
            response = run_deep_research(
                user_input=message,
                context=history,
                session_id=session_id,
                user_id=user_id,
                session_manager=self.session_manager,
                use_memory=self.use_memory  # 使用自动检测的配置
            )
        else:  response = run_general(
                user_input=message,
                context=history,
                session_id=session_id,
                user_id=user_id,
                session_manager=self.session_manager,
                use_memory=self.use_memory  # 使用自动检测的配置
            )

        self.session_manager.update_session(session_id, {"last_agent": agent_id, "last_message": message})

        # 持久化对话到 SQLite
        self.conversation_manager.save_conversation(
            session_id=session_id,
            user_id=user_id,
            user_message=message,
            assistant_response=response,
            agent_id=agent_id
        )

        return {"response": response, "session_id": session_id, "agent_id": agent_id}
