#!/bin/bash
# CEX Intelligence 部署脚本
# 执行以下步骤来部署项目到 Railway

cd /Users/neo/.openclaw/workspace-cex-intelligence

# 1. 初始化 Git 仓库（如果未初始化）
if [ ! -d ".git" ]; then
    git init
    echo "✅ Git 仓库已初始化"
else
    echo "📁 Git 仓库已存在"
fi

# 2. 配置 Git 用户名和邮箱
git config user.name "neo-claw-bot"
git config user.email "neo_claw_bot@proton.me"
echo "✅ Git 用户名和邮箱已配置"

# 3. 添加所有文件
git add .
echo "✅ 文件已添加到暂存区"

# 4. 提交代码
git commit -m "Initial commit for Railway deployment"
echo "✅ 代码已提交"

# 5. 检查远程仓库
if ! git remote get-url origin &> /dev/null; then
    git remote add origin https://github.com/neo-claw-bot/cex-intelligence.git
    echo "✅ 远程仓库已添加"
else
    echo "📡 远程仓库已存在: $(git remote get-url origin)"
fi

# 6. 推送代码到 main 分支
git branch -M main
git push -u origin main
echo "✅ 代码已推送到 GitHub"

# 7. 显示状态
echo ""
echo "📊 Git 状态:"
git status
echo ""
echo "🔗 远程仓库:"
git remote -v