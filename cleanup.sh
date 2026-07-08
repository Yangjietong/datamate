#!/bin/bash
# 打包前清理脚本 - 删除敏感文件和临时文件

echo "========================================"
echo "打包前清理"
echo "========================================"
echo ""

echo "[警告] 此脚本将删除以下文件:"
echo "  - .env (包含 API 密钥)"
echo "  - *.db (对话数据库)"
echo "  - *.csv (生成的数据文件)"
echo "  - *.png, *.jpg (生成的图片)"
echo "  - test_*.py (测试文件)"
echo "  - requirements_full.txt"
echo ""
read -p "按回车键继续，或按 Ctrl+C 取消... "
echo ""

# 删除敏感配置
if [ -f ".env" ]; then
    rm -f .env
    echo "[OK] 已删除 .env"
fi

# 删除数据库
rm -f *.db 2>/dev/null
echo "[OK] 已删除数据库文件"

# 删除生成的文件
rm -f *.csv *.png *.jpg *.jpeg 2>/dev/null
echo "[OK] 已删除生成的文件"

# 删除测试文件
rm -f test_*.py 2>/dev/null
echo "[OK] 已删除测试文件"

# 删除完整依赖列表
if [ -f "requirements_full.txt" ]; then
    rm -f requirements_full.txt
    echo "[OK] 已删除 requirements_full.txt"
fi

# 确保 .env.example 存在
if [ ! -f ".env.example" ]; then
    echo "[警告] .env.example 不存在，请确保已创建配置模板"
fi

echo ""
echo "========================================"
echo "清理完成！"
echo "========================================"
echo ""
echo "检查清单:"
echo "[  ] .env.example 存在且完整"
echo "[  ] requirements.txt 存在且精简"
echo "[  ] README.md 文档完整"
echo "[  ] 所有测试文件已删除"
echo "[  ] 没有硬编码的 API 密钥"
echo ""
echo "可以开始打包了！"
