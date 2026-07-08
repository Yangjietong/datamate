import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import Optional


class ConversationManager:
    """管理对话的持久化存储（SQLite）"""

    def __init__(self, db_path: str = "conversations.db"):
        self.db_path = db_path
        self._init_database()

    def _init_database(self):
        """初始化数据库表结构"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # conversations 表：存储会话元数据
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                session_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                title TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                message_count INTEGER DEFAULT 0,
                first_message TEXT,
                last_agent TEXT
            )
        """)

        # messages 表：存储具体消息
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (session_id) REFERENCES conversations(session_id)
            )
        """)

        # 创建索引加速查询
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_messages_session
            ON messages(session_id, timestamp)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_conversations_user
            ON conversations(user_id, updated_at DESC)
        """)

        conn.commit()
        conn.close()

    def save_conversation(
        self,
        session_id: str,
        user_id: str,
        user_message: str,
        assistant_response: str,
        agent_id: Optional[str] = None
    ):
        """保存一轮对话"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        now = datetime.now().isoformat()

        # 检查 conversation 是否已存在
        cursor.execute(
            "SELECT message_count, first_message FROM conversations WHERE session_id = ?",
            (session_id,)
        )
        result = cursor.fetchone()

        if result is None:
            # 新会话：插入 conversation 记录
            cursor.execute("""
                INSERT INTO conversations
                (session_id, user_id, title, created_at, updated_at, message_count, first_message, last_agent)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                session_id,
                user_id,
                self._generate_title(user_message),
                now,
                now,
                2,  # user + assistant = 2 条消息
                user_message[:200],  # 存储前 200 字符用于生成标题
                agent_id
            ))
        else:
            # 已有会话：更新
            message_count = result[0]
            cursor.execute("""
                UPDATE conversations
                SET updated_at = ?, message_count = ?, last_agent = ?
                WHERE session_id = ?
            """, (now, message_count + 2, agent_id, session_id))

        # 插入消息
        cursor.execute("""
            INSERT INTO messages (session_id, role, content, timestamp)
            VALUES (?, ?, ?, ?)
        """, (session_id, "user", user_message, now))

        cursor.execute("""
            INSERT INTO messages (session_id, role, content, timestamp)
            VALUES (?, ?, ?, ?)
        """, (session_id, "assistant", assistant_response, now))

        conn.commit()
        conn.close()

    def _generate_title(self, first_message: str) -> str:
        """根据首条消息生成标题"""
        # 简单截取前 50 字符作为标题
        title = first_message.strip()[:50]
        if len(first_message) > 50:
            title += "..."
        return title

    def list_conversations(
        self,
        user_id: Optional[str] = None,
        limit: int = 20,
        offset: int = 0
    ) -> list[dict]:
        """列出对话列表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        if user_id:
            cursor.execute("""
                SELECT session_id, user_id, title, created_at, updated_at,
                       message_count, first_message, last_agent
                FROM conversations
                WHERE user_id = ?
                ORDER BY updated_at DESC
                LIMIT ? OFFSET ?
            """, (user_id, limit, offset))
        else:
            cursor.execute("""
                SELECT session_id, user_id, title, created_at, updated_at,
                       message_count, first_message, last_agent
                FROM conversations
                ORDER BY updated_at DESC
                LIMIT ? OFFSET ?
            """, (limit, offset))

        results = cursor.fetchall()
        conn.close()

        conversations = []
        for row in results:
            conversations.append({
                "session_id": row[0],
                "user_id": row[1],
                "title": row[2],
                "created_at": row[3],
                "updated_at": row[4],
                "message_count": row[5],
                "first_message": row[6],
                "last_agent": row[7]
            })

        return conversations

    def get_conversation(self, session_id: str) -> Optional[dict]:
        """获取指定会话的元数据"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT session_id, user_id, title, created_at, updated_at,
                   message_count, first_message, last_agent
            FROM conversations
            WHERE session_id = ?
        """, (session_id,))

        result = cursor.fetchone()
        conn.close()

        if result is None:
            return None

        return {
            "session_id": result[0],
            "user_id": result[1],
            "title": result[2],
            "created_at": result[3],
            "updated_at": result[4],
            "message_count": result[5],
            "first_message": result[6],
            "last_agent": result[7]
        }

    def get_messages(
        self,
        session_id: str,
        limit: Optional[int] = None
    ) -> list[dict]:
        """获取指定会话的所有消息"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        if limit:
            cursor.execute("""
                SELECT role, content, timestamp
                FROM messages
                WHERE session_id = ?
                ORDER BY id DESC
                LIMIT ?
            """, (session_id, limit))
            results = cursor.fetchall()
            results.reverse()  # 反转为正序
        else:
            cursor.execute("""
                SELECT role, content, timestamp
                FROM messages
                WHERE session_id = ?
                ORDER BY id ASC
            """, (session_id,))
            results = cursor.fetchall()

        conn.close()

        messages = []
        for row in results:
            messages.append({
                "role": row[0],
                "content": row[1],
                "timestamp": row[2]
            })

        return messages

    def search_conversations(
        self,
        keyword: str,
        user_id: Optional[str] = None,
        limit: int = 20
    ) -> list[dict]:
        """按关键词搜索对话（简单文本匹配）"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        keyword_pattern = f"%{keyword}%"

        if user_id:
            cursor.execute("""
                SELECT DISTINCT c.session_id, c.user_id, c.title, c.created_at,
                       c.updated_at, c.message_count, c.first_message, c.last_agent
                FROM conversations c
                LEFT JOIN messages m ON c.session_id = m.session_id
                WHERE c.user_id = ?
                  AND (c.title LIKE ? OR c.first_message LIKE ? OR m.content LIKE ?)
                ORDER BY c.updated_at DESC
                LIMIT ?
            """, (user_id, keyword_pattern, keyword_pattern, keyword_pattern, limit))
        else:
            cursor.execute("""
                SELECT DISTINCT c.session_id, c.user_id, c.title, c.created_at,
                       c.updated_at, c.message_count, c.first_message, c.last_agent
                FROM conversations c
                LEFT JOIN messages m ON c.session_id = m.session_id
                WHERE c.title LIKE ? OR c.first_message LIKE ? OR m.content LIKE ?
                ORDER BY c.updated_at DESC
                LIMIT ?
            """, (keyword_pattern, keyword_pattern, keyword_pattern, limit))

        results = cursor.fetchall()
        conn.close()

        conversations = []
        for row in results:
            conversations.append({
                "session_id": row[0],
                "user_id": row[1],
                "title": row[2],
                "created_at": row[3],
                "updated_at": row[4],
                "message_count": row[5],
                "first_message": row[6],
                "last_agent": row[7]
            })

        return conversations

    def delete_conversation(self, session_id: str) -> bool:
        """删除指定会话及其所有消息"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 删除消息
        cursor.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))

        # 删除会话
        cursor.execute("DELETE FROM conversations WHERE session_id = ?", (session_id,))

        deleted = cursor.rowcount > 0
        conn.commit()
        conn.close()

        return deleted
