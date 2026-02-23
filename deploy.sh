#!/bin/bash
# CEX Intelligence 部署脚本

echo "🚀 CEX Intelligence Dashboard 部署脚本"
echo "=========================================="

# 检查 GitHub 登录
echo ""
echo "步骤 1: 确保已登录 GitHub"
echo "用户名: neo-claw-bot"
echo "邮箱: neo_claw_bot@proton.me"
echo ""
read -p "按回车继续..."

# 初始化 Git
echo ""
echo "步骤 2: 初始化 Git 仓库..."
cd /Users/neo/.openclaw/workspace-cex-intelligence

if [ ! -d ".git" ]; then
    git init
    echo "✅ Git 仓库已初始化"
else
    echo "✅ Git 仓库已存在"
fi

# 配置 Git
git config user.name "neo-claw-bot"
git config user.email "neo_claw_bot@proton.me"

# 添加文件
echo ""
echo "步骤 3: 添加文件到 Git..."
git add web/ data/intelligence/ .github/workflows/ DEPLOY_GUIDE.md

# 提交
echo ""
echo "步骤 4: 提交代码..."
git commit -m "Initial deployment: CEX Intelligence Dashboard" || echo "无变更可提交"

# 添加远程仓库
echo ""
echo "步骤 5: 配置远程仓库..."
if ! git remote | grep -q "origin"; then
    git remote add origin https://github.com/neo-claw-bot/cex-intelligence.git
    echo "✅ 远程仓库已添加"
else
    echo "✅ 远程仓库已存在"
fi

echo ""
echo "=========================================="
echo "📋 下一步操作:"
echo ""
echo "1. 在 GitHub 创建仓库:"
echo "   https://github.com/new"
echo "   仓库名: cex-intelligence"
echo ""
echo "2. 推送代码:"
echo "   git push -u origin main"
echo ""
echo "3. 在 Railway 部署:"
echo "   - 访问 https://railway.app"
echo "   - New Project → Deploy from GitHub"
echo "   - 选择 cex-intelligence 仓库"
echo ""
echo "4. 配置 Railway Token (用于自动部署):"
echo "   - Railway Dashboard → Project Settings → Tokens"
echo "   - 复制 Token"
echo "   - GitHub → Settings → Secrets → RAILWAY_TOKEN"
echo ""
echo "=========================================="
