#!/usr/bin/env python3
"""对话管理命令行工具

用法：
    python cli_conversation.py list [--user USER_ID] [--limit N]
    python cli_conversation.py search KEYWORD [--user USER_ID]
    python cli_conversation.py show SESSION_ID
    python cli_conversation.py delete SESSION_ID
    python cli_conversation.py resume SESSION_ID
"""

import sys
import argparse
from datetime import datetime
from conversation_manager import ConversationManager


def format_datetime(iso_str: str) -> str:
    """格式化 ISO 时间字符串"""
    try:
        dt = datetime.fromisoformat(iso_str)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except:
        return iso_str


def cmd_list(args):
    """列出对话列表"""
    cm = ConversationManager()
    conversations = cm.list_conversations(
        user_id=args.user,
        limit=args.limit,
        offset=args.offset
    )

    if not conversations:
        print("未找到对话记录")
        return

    print(f"\n{'='*80}")
    print(f"{'序号':<4} {'Session ID':<25} {'标题':<30} {'更新时间':<20}")
    print(f"{'='*80}")

    for i, conv in enumerate(conversations, 1):
        title = conv['title'][:28] + "..." if len(conv['title']) > 28 else conv['title']
        updated = format_datetime(conv['updated_at'])
        print(f"{i:<4} {conv['session_id']:<25} {title:<30} {updated:<20}")

    print(f"{'='*80}")
    print(f"共 {len(conversations)} 个对话\n")


def cmd_search(args):
    """搜索对话"""
    cm = ConversationManager()
    conversations = cm.search_conversations(
        keyword=args.keyword,
        user_id=args.user,
        limit=args.limit
    )

    if not conversations:
        print(f"未找到包含 '{args.keyword}' 的对话")
        return

    print(f"\n搜索关键词: {args.keyword}")
    print(f"{'='*80}")
    print(f"{'序号':<4} {'Session ID':<25} {'标题':<30} {'更新时间':<20}")
    print(f"{'='*80}")

    for i, conv in enumerate(conversations, 1):
        title = conv['title'][:28] + "..." if len(conv['title']) > 28 else conv['title']
        updated = format_datetime(conv['updated_at'])
        print(f"{i:<4} {conv['session_id']:<25} {title:<30} {updated:<20}")

    print(f"{'='*80}")
    print(f"共找到 {len(conversations)} 个对话\n")


def cmd_show(args):
    """显示对话详情"""
    cm = ConversationManager()
    conv = cm.get_conversation(args.session_id)

    if not conv:
        print(f"错误：对话 {args.session_id} 不存在")
        return

    messages = cm.get_messages(args.session_id, limit=args.limit)

    print(f"\n{'='*80}")
    print(f"对话详情")
    print(f"{'='*80}")
    print(f"Session ID: {conv['session_id']}")
    print(f"用户 ID: {conv['user_id']}")
    print(f"标题: {conv['title']}")
    print(f"创建时间: {format_datetime(conv['created_at'])}")
    print(f"更新时间: {format_datetime(conv['updated_at'])}")
    print(f"消息数量: {conv['message_count']}")
    print(f"最后使用的 Agent: {conv['last_agent'] or 'N/A'}")
    print(f"{'='*80}\n")

    if not messages:
        print("该对话没有消息记录")
        return

    print(f"{'='*80}")
    print(f"对话历史 (最近 {len(messages)} 条消息)")
    print(f"{'='*80}\n")

    for i, msg in enumerate(messages, 1):
        role_display = "用户" if msg['role'] == "user" else "助手"
        timestamp = format_datetime(msg['timestamp'])
        content = msg['content']

        print(f"[{i}] {role_display} ({timestamp})")
        print(f"{content}")
        print(f"{'-'*80}\n")


def cmd_delete(args):
    """删除对话"""
    cm = ConversationManager()

    # 确认删除
    if not args.yes:
        response = input(f"确认删除对话 {args.session_id}？(y/N): ").strip().lower()
        if response not in ['y', 'yes']:
            print("已取消删除")
            return

    success = cm.delete_conversation(args.session_id)

    if success:
        print(f"✓ 已删除对话 {args.session_id}")
    else:
        print(f"✗ 删除失败：对话 {args.session_id} 不存在")


def cmd_resume(args):
    """生成恢复对话的命令提示"""
    cm = ConversationManager()
    conv = cm.get_conversation(args.session_id)

    if not conv:
        print(f"错误：对话 {args.session_id} 不存在")
        return

    print(f"\n{'='*80}")
    print(f"恢复对话: {conv['title']}")
    print(f"{'='*80}")
    print(f"Session ID: {conv['session_id']}")
    print(f"用户 ID: {conv['user_id']}")
    print(f"消息数量: {conv['message_count']}")
    print(f"{'='*80}\n")

    # 显示最近几条消息作为上下文预览
    messages = cm.get_messages(args.session_id, limit=4)
    if messages:
        print("最近的对话内容：")
        print(f"{'-'*80}")
        for msg in messages[-4:]:
            role_display = "用户" if msg['role'] == "user" else "助手"
            content_preview = msg['content'][:100] + "..." if len(msg['content']) > 100 else msg['content']
            print(f"{role_display}: {content_preview}")
        print(f"{'-'*80}\n")

    print("要恢复此对话，请在启动应用时传入以下参数：")
    print(f"  --session-id {args.session_id}")
    print("\n或者在代码中调用：")
    print(f"  gateway.handle_request(user_id='{conv['user_id']}', message='...', session_id='{args.session_id}')")
    print()


def main():
    parser = argparse.ArgumentParser(
        description="对话管理命令行工具",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    subparsers = parser.add_subparsers(dest='command', help='子命令')

    # list 命令
    parser_list = subparsers.add_parser('list', help='列出对话列表')
    parser_list.add_argument('--user', help='按用户 ID 筛选')
    parser_list.add_argument('--limit', type=int, default=20, help='显示数量（默认 20）')
    parser_list.add_argument('--offset', type=int, default=0, help='跳过数量（默认 0）')

    # search 命令
    parser_search = subparsers.add_parser('search', help='搜索对话')
    parser_search.add_argument('keyword', help='搜索关键词')
    parser_search.add_argument('--user', help='按用户 ID 筛选')
    parser_search.add_argument('--limit', type=int, default=20, help='显示数量（默认 20）')

    # show 命令
    parser_show = subparsers.add_parser('show', help='显示对话详情')
    parser_show.add_argument('session_id', help='Session ID')
    parser_show.add_argument('--limit', type=int, help='显示最近 N 条消息（默认全部）')

    # delete 命令
    parser_delete = subparsers.add_parser('delete', help='删除对话')
    parser_delete.add_argument('session_id', help='Session ID')
    parser_delete.add_argument('-y', '--yes', action='store_true', help='跳过确认')

    # resume 命令
    parser_resume = subparsers.add_parser('resume', help='查看如何恢复对话')
    parser_resume.add_argument('session_id', help='Session ID')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # 路由到对应的命令处理函数
    commands = {
        'list': cmd_list,
        'search': cmd_search,
        'show': cmd_show,
        'delete': cmd_delete,
        'resume': cmd_resume
    }

    commands[args.command](args)


if __name__ == '__main__':
    main()
