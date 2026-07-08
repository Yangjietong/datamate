import argparse
from sessionmanager import SessionManager
from gateway import Gateway
from conversation_manager import ConversationManager

def main():
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="对话助手")
    parser.add_argument("--session-id", help="恢复指定的对话会话")
    parser.add_argument("--user-id", default="cli_user", help="用户 ID（默认 cli_user）")
    args = parser.parse_args()

    session_manager = SessionManager()
    gateway = Gateway(session_manager)

    print("流程：输入 → Gateway 路由 → Runtime（工具调用）→ 返回结果")
    print("工具：天气、当前时间、订单查询（仅 ORD001 有数据）")
    print("输入 quit 退出。\n")

    user_id = args.user_id
    session_id: str | None = args.session_id

    # 如果指定了 session_id，从数据库恢复对话历史
    if session_id:
        cm = ConversationManager()
        conv = cm.get_conversation(session_id)

        if conv:
            print(f"[恢复对话] {conv['title']}")
            print(f"Session ID: {session_id}")
            print(f"消息数量: {conv['message_count']}\n")

            # 加载历史消息
            messages = cm.get_messages(session_id)
            history = [{"role": msg["role"], "content": msg["content"]} for msg in messages]

            # 恢复会话到 SessionManager
            session_manager.restore_session(
                session_id=session_id,
                user_id=user_id,
                history=history,
                last_agent=conv.get("last_agent")
            )

            print("最近的对话：")
            for msg in messages[-4:]:
                role_display = "你" if msg["role"] == "user" else "助手"
                content_preview = msg["content"][:60] + "..." if len(msg["content"]) > 60 else msg["content"]
                # 处理可能的 emoji 编码问题
                try:
                    print(f"  {role_display}: {content_preview}")
                except UnicodeEncodeError:
                    # 移除无法编码的字符
                    safe_content = content_preview.encode('gbk', errors='ignore').decode('gbk')
                    print(f"  {role_display}: {safe_content}")
            print()
        else:
            print(f"[警告] 对话 {session_id} 不存在，将创建新对话\n")
            session_id = None

    while True:
        try:
            user_input = input("你: ").strip()
        except EOFError:
            break
        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit", "q"):
            break

        result = gateway.handle_request(user_id, user_input, session_id)
        session_id = result.get("session_id") or session_id
        print("助手:", result.get("response", ""))
        if result.get("agent_id"):
            print("  [路由:", result["agent_id"], "]")
        print()



if __name__ == "__main__":
    main()
