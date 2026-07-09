# DataMate AI数据助手

一个功能强大的 AI 对话系统，支持联网搜索、数据可视化、深度研究、对话持久化等功能。

## 核心功能

- 🤖 **智能对话**：基于 DeepSeek 的高质量对话
- 🔍 **联网搜索**：实时获取最新资讯（千帆 AI 搜索）
- 📊 **数据可视化**：AI 自动生成图表和数据分析
- 🧠 **深度研究**：多步推理、证据收集、报告生成
- 💾 **对话持久化**：SQLite 存储，支持恢复历史对话
- 🧩 **长期记忆**（可选）：基于 mem0，跨会话记住用户偏好
- 🎯 **智能路由**：自动选择合适的 agent 处理请求
- 📈 **Token 统计**：实时追踪 API 消耗

## 快速开始

### 1. 环境要求

- Python 3.10+
- Windows / macOS / Linux

### 2. 安装

**Windows：**
```cmd
install.bat
```

**macOS/Linux：**
```bash
./install.sh
```

安装脚本会自动创建虚拟环境、安装依赖，并询问是否启用长期记忆功能（默认禁用，可随时后续开启，见[长期记忆配置](#长期记忆配置可选)）。

也可以手动安装：
```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
```

### 3. 配置 API 密钥

复制配置模板并填写必需的 API 密钥：

```bash
cp .env.example .env
```

编辑 `.env`，填写以下必需项：

```env
# 必需 - DeepSeek API（主对话模型）
# 获取：https://platform.deepseek.com/
DEEPSEEK_API_KEY=sk-你的密钥

# 必需 - 千帆 AI 搜索（联网功能）
# 获取：https://console.bce.baidu.com/qianfan/
QIANFAN_API_KEY=你的密钥

# 必需 - Embedding 模型（智能路由）
# 获取：https://ai.gitee.com/（免费）
EMBEDDING_API_KEY=你的密钥
EMBEDDING_BASE_URL=https://ai.gitee.com/v1
```

### 4. 运行

```Windows
# 启动对话助手
chat.bat
```
或
```bash
# 启动对话助手
python main.py

# 恢复之前的对话
python main.py --session-id <session_id>
```

### 第一次对话示例

```
你: 你好
助手: 你好！有什么我可以帮你的吗？

你: 北京今天天气怎么样？
助手: 北京今天天气：晴，25°C

你: 帮我查询AI领域最新发展
助手: [调用联网搜索，返回最新资讯]
```

## 使用指南

### 基本对话

```
你: 北京今天天气怎么样？
助手: 北京今天天气：晴，25°C

你: 帮我查询一下AI领域最新发展
助手: [调用联网搜索，返回最新资讯]
```

### 数据可视化

```
你: 查询2000-2023年安徽省理科高考一本线并可视化
助手: [自动搜索数据 → 清洗 → 生成图表 → 保存 CSV]
```

### 深度研究

```
你: 调研一下区块链技术的最新进展
助手: [触发深度研究模式]
  1. 拆分子问题
  2. 联网检索证据
  3. 生成结构化报告
```

### 对话管理

系统使用 SQLite（`conversations.db`）持久化每一轮对话，支持随时恢复。

**表结构**：
- `conversations`：对话元数据（session_id、标题、时间、消息数量等）
- `messages`：具体消息内容（role、content、timestamp）

**命令行工具**：

```bash
# 列出所有对话
python cli_conversation.py list [--user USER_ID] [--limit N] [--offset N]

# 搜索对话
python cli_conversation.py search "关键词" [--user USER_ID] [--limit N]

# 查看对话详情
python cli_conversation.py show <session_id> [--limit N]

# 查看如何恢复某个对话（打印上下文预览和代码示例）
python cli_conversation.py resume <session_id>

# 删除对话
python cli_conversation.py delete <session_id> [-y]
```

**代码中使用**：

对话在每次调用 `gateway.handle_request()` 后自动保存，无需额外操作：

**注意事项**：
- `SessionManager` 本身仍是内存存储（会话摘要功能有效，但重启后丢失）；`ConversationManager` 的 SQLite 存储才是持久化的，重启后可通过 `--session-id` 或 `restore_session()` 恢复。
- 自动生成的 `session_id` 格式为 `{user_id}_{8位随机hex}`。
- 对话标题自动从首条消息的前 50 个字符生成。
- 当前搜索是简单文本匹配（`LIKE`），如需语义搜索可后续集成 ChromaDB。

## 长期记忆配置（可选）

长期记忆功能使用 mem0 服务，可以跨会话记住用户偏好和重要信息，提供更个性化的对话体验（如记住用户喜欢简洁的回答、工作领域、经常查询的信息类型等）。

**核心功能对比**：

| 功能 | 启用长期记忆 | 禁用长期记忆 |
|------|-------------|-------------|
| 基本对话 | ✅ | ✅ |
| 联网搜索 | ✅ | ✅ |
| 数据可视化 | ✅ | ✅ |
| 对话持久化 | ✅ | ✅ |
| 跨会话记忆 | ✅ | ❌ |
| 个性化回答 | ✅ | ❌ |
| 需要 mem0 | ✅ | ❌ |
| 额外网络调用 | ✅ | ❌ |

### 启用方式

**方式 1：安装时配置（推荐新用户）**

运行 `install.bat`（Windows）或 `./install.sh`（macOS/Linux），脚本会询问：
```
Enable long-term memory? (y/N)
```
- 输入 `y` → 启用
- 输入 `n` 或直接回车 → 禁用（默认）

**方式 2：使用配置管理脚本**

```bash
# Windows
config.bat

# Linux/macOS
./config.sh
```

脚本提供：
1. 查看当前状态
2. 启用长期记忆
3. 禁用长期记忆

**方式 3：手动配置**

1. 在 https://app.mem0.ai/ 注册并获取 API 密钥
2. 编辑 `.env` 文件
3. 找到这一行：
   ```env
   # MEM0_API_KEY=your_mem0_api_key_here
   ```
4. 删除开头的 `#` 并填入你的密钥：
   ```env
   MEM0_API_KEY=m0-你的实际密钥
   ```
5. 重启应用

**禁用**：在 `.env` 中的 `MEM0_API_KEY=` 前加上 `#` 注释，并重启应用。

### 自动检测机制

Gateway 会在启动时自动检测：

```
[INFO] Long-term memory ENABLED (MEM0_API_KEY configured)
```
或
```
[INFO] Long-term memory DISABLED (MEM0_API_KEY not configured)
```

**检测规则**：
- 如果 `.env` 中有 `MEM0_API_KEY=xxx`（未注释）→ 启用
- 如果 `MEM0_API_KEY=` 为空或被注释（`#`）→ 禁用

**实现位置**：[gateway.py:18](gateway.py#L18)

```python
self.use_memory = bool(os.getenv("MEM0_API_KEY"))
```

无需修改代码，完全配置驱动。调用位置：`run_general()` 和 `run_deep_research()`。

### 常见问题

**Q1: 不配置长期记忆会影响基本功能吗？**

不会。所有核心功能（对话、搜索、可视化、对话持久化）都正常工作。

**Q2: 长期记忆和对话持久化有什么区别？**

- **对话持久化（SQLite）**：完整保存对话历史，可以恢复上次的对话
- **长期记忆（mem0）**：智能提取关键信息（偏好、背景），不保存完整对话

**Q3: 可以先不启用，以后再开启吗？**

可以。任何时候都可以通过 `config.bat/sh` 或手动编辑 `.env` 启用。

**Q4: 启用后会产生额外费用吗？**

mem0 有免费额度，超出后才会收费。建议查看官网的定价页面。

**Q5: 如何验证长期记忆是否生效？**

1. 启动应用，看到 `[INFO] Long-term memory ENABLED`
2. 在对话中说："记住我喜欢简洁的回答"
3. 重新启动应用并开始新对话
4. 问一个问题，看回答是否简洁

**Q6: 长期记忆的数据存储在哪里？**

存储在 mem0 的云端服务器，不在本地。

### 推荐配置

- **新用户/轻度使用**：建议先**禁用**，熟悉基本功能后再启用
- **重度使用/需要个性化**：建议**启用**长期记忆
- **企业/团队使用**：每个用户配置独立的 `user_id`，启用长期记忆提供个性化服务

### 安全提示

- ⚠️ MEM0_API_KEY 是敏感信息，不要分享给他人
- ⚠️ 不要将包含真实密钥的 `.env` 文件提交到 git
- ⚠️ 打包分发前使用 `cleanup.bat/sh` 删除 `.env`

## 项目结构

```
program/
├── main.py                    # 命令行入口
├── gateway.py                 # 请求网关和路由
├── route.py                   # 智能路由系统
├── memory.py                  # 对话逻辑（run_general / run_deep_research）
├── sessionmanager.py          # 会话管理（内存 + 自动摘要）
├── conversation_manager.py    # 对话持久化（SQLite）
├── tool.py                    # 工具函数（天气、时间、AI搜索等）
├── visualization_tool.py      # AI 数据可视化工具
├── token_tracker.py           # Token 消耗统计
├── cli_conversation.py        # 对话管理命令行工具
├── install.bat / install.sh   # 安装脚本
├── config.bat / config.sh     # 配置管理脚本
├── cleanup.bat / cleanup.sh   # 清理脚本（打包前使用）
├── AGENT.md                   # Agent 系统提示词
├── .env.example               # 配置模板
├── .env                       # 实际配置（不提交到 git）
├── requirements.txt           # Python 依赖
└── conversations.db           # 对话数据库（自动创建）
```

## 配置说明

### 必需配置

| 配置项 | 说明 | 获取地址 |
|--------|------|----------|
| `DEEPSEEK_API_KEY` | 主对话模型 API | https://platform.deepseek.com/ |
| `QIANFAN_API_KEY` | AI 搜索功能 | https://console.bce.baidu.com/qianfan/ |
| `EMBEDDING_API_KEY` | 路由和相似度计算 | https://ai.gitee.com/ |

### 可选配置

| 配置项 | 说明 | 默认 |
|--------|------|------|
| `MEM0_API_KEY` | 长期记忆功能 | 未启用 |
| `DASHSCOPE_*` | 阿里云模型服务 | 未启用 |

## 高级功能

### 1. Token 统计

每次请求后自动显示 Token 消耗明细：

```
[Token 统计] 本次请求明细：
  - 主模型(deepseek-v4-pro): 输入 2148，输出 71，总计 2219
  - ai_search: 输入 150，输出 450，总计 600
  合计：2819 tokens
```

### 2. HITL 审批

对文件写入等操作，会请求用户确认：

```
---------- [HITL 审批] ----------
当前意图：查询数据并保存到 CSV
待执行动作：write_json_to_csv
参数：{"json_data": "...", "filename": "data.csv"}
风险提示：将创建或覆盖 CSV 文件
输入 y 通过 / n 或 n:原因 拒绝 ----------
```

### 3. 自动摘要

SessionManager 每 5 轮对话自动折叠成摘要，节省上下文：

```
[系统] 以下是之前对话的摘要：
用户询问了北京天气，查询了 AI 发展趋势，并请求数据可视化...

[最近对话]
你: ...
助手: ...
```

## 开发指南

### 添加新工具

在 [tool.py](tool.py) 中添加：

```python
@tool
def your_tool(param: str) -> str:
    """工具描述（会被传给 LLM）"""
    # 实现逻辑
    return result
```

在 [memory.py](memory.py) 中注册：

```python
TOOLS_GENERAL = [get_weather, ..., your_tool]
```

### 添加新 Agent

在 [route.py](route.py) 的 `ROUTE_RULES` 中添加路由规则：

```python
ROUTE_RULES = [
    (["关键词1", "关键词2"], "your_agent_id"),
    ...
]
```

在 [gateway.py](gateway.py) 中添加处理逻辑。

## 打包与分发

### 1. 清理敏感文件（必需）

**为什么需要清理？**
- 防止泄露你的 API 密钥
- 防止包含你的私人对话记录
- 减小打包体积

**清理脚本**：

```bash
# Windows
cleanup.bat

# Linux/macOS
./cleanup.sh
```

**清理内容**：
- `.env` - 包含你的 API 密钥（敏感）
- `*.db` - 对话数据库（包含你的对话记录）
- `*.csv` - 生成的数据文件
- `*.png`, `*.jpg` - 生成的图片
- `test_*.py` - 测试文件
- `requirements_full.txt` - 完整依赖列表

**安全检查清单**：
- [ ] `.env.example` 存在且完整
- [ ] `requirements.txt` 存在
- [ ] `README.md` 完整
- [ ] 所有测试文件已删除
- [ ] 没有硬编码的 API 密钥

**注意**：
- ⚠️ 清理前确保 `.env` 中的 API 密钥已经备份到安全的地方
- ⚠️ 重要的对话记录已经导出或备份
- ⚠️ 生成的图表和数据文件已经保存到其他位置

### 2. 分发方式

**方式 1：源码压缩包（推荐）**

```bash
# 1. 清理敏感文件
cleanup.bat  # Windows
# 或 ./cleanup.sh（Linux/macOS）

# 2. 创建压缩包
# Windows（使用 PowerShell）
Compress-Archive -Path * -DestinationPath ai-assistant-v1.0.zip

# Linux/macOS
zip -r ai-assistant-v1.0.zip * -x "*.git*" "*__pycache__*" "*.pyc"
```

**用户安装步骤**：
1. 解压 zip
2. 运行 `install.bat` (Windows) 或 `./install.sh` (Linux/macOS)
3. 编辑 `.env` 填写 API 密钥
4. 运行 `python main.py`

**方式 2：Git 仓库**

```bash
git init
git add .
git commit -m "chore: initial release"
git remote add origin <your-repo-url>
git push -u origin main
```

**用户安装步骤**：
```bash
git clone <repo-url>
cd ai-assistant
./install.sh  # 或 install.bat
# 编辑 .env
python main.py
```

### 3. 恢复清理的文件

如果误删了文件：

1. `.env` - 从 `.env.example` 复制并重新填写 API 密钥
2. `*.db` - 数据库文件删除后无法恢复，对话记录会丢失
3. 其他文件 - 可以重新生成

## 常见问题

### Q1: 启动时报错 "未配置 API KEY"

**A:** 检查 `.env` 文件是否存在，并且填写了正确的 API 密钥。

### Q2: AI 搜索返回 SSL 错误

**A:** 这是网络连接问题，工具已添加自动重试。如果持续出现，检查防火墙或代理设置。

### Q3: 对话恢复后没有历史记录

**A:** 确保使用了正确的 `--session-id` 参数，并且该对话存在于数据库中（用 `cli_conversation.py list` 查看）。

### Q4: Embedding 编码错误

**A:** Windows 终端编码问题，设置环境变量：`set PYTHONIOENCODING=utf-8`

### Q5: 清理脚本提示 "找不到命令"

**A:**
- Windows：使用 `cleanup.bat`（不要加 `./`），或双击运行
- Linux/macOS：确保脚本有执行权限 `chmod +x cleanup.sh`

### Q6: 可以跳过清理直接打包吗？

**A:** **强烈不建议**！如果不清理：
- 会泄露你的 API 密钥
- 会包含你的私人对话记录
- 会增加打包体积

### Q7: Windows 终端中文乱码或 emoji 显示问题

**A:** Windows 终端对某些 emoji 和中文支持不佳，这不影响功能。可以：
1. 使用 Windows Terminal 替代 cmd
2. 设置 `set PYTHONIOENCODING=utf-8`

## 性能优化

- **本地 Embedding**: 使用本地模型替代 API 调用，降低延迟
- **缓存**: 添加 Redis 缓存常见查询结果
- **批量处理**: 深度研究模式的多个搜索可以并行执行

## 路线图

- [ ] 支持多模态（图片、音频）
- [ ] ChromaDB 语义检索集成
- [ ] Web UI 界面
- [ ] Docker 部署支持
- [ ] 插件系统

## 版本说明

### v1.0 (2026-07-08)

**核心功能**：
- ✅ 智能对话（DeepSeek）
- ✅ 联网搜索（千帆 AI）
- ✅ 数据可视化（AI 生成）
- ✅ 深度研究模式
- ✅ 对话持久化（SQLite）
- ✅ 长期记忆（可选，mem0）
- ✅ Token 统计
- ✅ HITL 审批

**已知限制**：
- Windows 终端 emoji 显示问题
- 路由系统 embedding 编码问题（不影响核心功能）
- mem0 长期记忆需要额外配置

**系统要求**：
- Python 3.10+
- 2GB RAM
- 网络连接（API 调用）

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！
