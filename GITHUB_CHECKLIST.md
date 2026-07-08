# GitHub 上传前检查清单

在推送到 GitHub 之前，请逐项检查：

## 🔐 安全检查

- [ ] `.env` 文件已删除（运行 `cleanup.bat/sh`）
- [ ] 代码中没有硬编码的 API 密钥
- [ ] `.gitignore` 包含了 `.env`、`*.db`、`*.csv` 等敏感文件
- [ ] 对话数据库（`*.db`）已清理

## 📄 文件检查

- [ ] `.env.example` 存在且完整（包含所有必需的配置项）
- [ ] `requirements.txt` 存在且包含所有依赖
- [ ] `README.md` 完整且准确
- [ ] 安装脚本（`install.bat`, `install.sh`）存在
- [ ] 配置脚本（`config.bat`, `config.sh`）存在
- [ ] 清理脚本（`cleanup.bat`, `cleanup.sh`）存在

## 🧪 功能测试

- [ ] 基本对话功能正常
- [ ] 联网搜索功能正常
- [ ] 对话持久化功能正常
- [ ] 安装脚本可以正常运行

## 📝 文档检查

- [ ] README.md 包含完整的安装说明
- [ ] README.md 包含 API 密钥获取方法
- [ ] README.md 包含使用示例
- [ ] README.md 包含常见问题解答

## 🔍 代码质量

- [ ] 删除了所有测试文件（`test_*.py`）
- [ ] 删除了调试用的 print（可选）
- [ ] 代码中的注释是中文（与项目风格一致）

## 检查命令

```bash
# 检查是否有 .env 文件（应该返回 "没有那个文件或目录"）
ls .env

# 检查 git 状态
git status

# 检查将要提交的文件
git diff --cached --name-only

# 搜索可能的 API 密钥（应该只在 .env.example 中找到）
grep -r "sk-" . --exclude-dir=.git --exclude-dir=.venv || echo "✓ 没有找到硬编码的密钥"
grep -r "MEM0_API_KEY=" . --exclude-dir=.git --exclude-dir=.venv | grep -v ".env.example" || echo "✓ 没有找到硬编码的 MEM0 密钥"
```

## 推送命令

```bash
# 1. 添加所有文件
git add .

# 2. 查看状态
git status

# 3. 提交
git commit -m "feat: complete AI assistant with conversation persistence and memory"

# 4. 推送
git push origin main
```

## 推送后验证

- [ ] 在 GitHub 上查看 README.md 渲染是否正确
- [ ] 检查是否有敏感文件被上传
- [ ] 测试克隆仓库并按照 README 安装是否成功

## 如果发现敏感信息已上传

```bash
# 从历史记录中删除敏感文件
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch .env" \
  --prune-empty --tag-name-filter cat -- --all

# 强制推送（危险操作，仅在必要时使用）
git push origin --force --all

# 更好的方法：使用 BFG Repo-Cleaner
# https://rtyley.github.io/bfg-repo-cleaner/
```
