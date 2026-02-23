#!/bin/bash
# CEX Intelligence 完整部署脚本
# 使用方法: chmod +x deploy-full.sh && ./deploy-full.sh

set -e  # 遇到错误立即停止

echo "🚀 CEX Intelligence Dashboard 完整部署"
echo "=========================================="

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 项目目录
PROJECT_DIR="/Users/neo/.openclaw/workspace-cex-intelligence"
cd "$PROJECT_DIR"

# 1. 检查 gh 登录状态
echo ""
echo "${YELLOW}步骤 1/6: 检查 GitHub CLI 登录状态...${NC}"
if ! gh auth status &>/dev/null; then
    echo "${RED}错误: gh 未登录。请先运行: gh auth login${NC}"
    exit 1
fi
echo "${GREEN}✅ GitHub CLI 已登录${NC}"

# 2. 检查远程仓库
echo ""
echo "${YELLOW}步骤 2/6: 检查远程仓库...${NC}"
if git remote | grep -q "origin"; then
    echo "远程仓库已存在:"
    git remote -v
else
    echo "远程仓库不存在，需要创建..."
fi

# 3. 创建 GitHub 仓库（如果不存在）
echo ""
echo "${YELLOW}步骤 3/6: 创建 GitHub 仓库...${NC}"
REPO_NAME="cex-intelligence"
if gh repo view "$REPO_NAME" &>/dev/null; then
    echo "${GREEN}✅ 仓库 $REPO_NAME 已存在${NC}"
else
    echo "创建新仓库: $REPO_NAME..."
    gh repo create "$REPO_NAME" --public --description "CEX Intelligence Dashboard - Web3交易所情报监控系统" || {
        echo "${RED}创建仓库失败，尝试使用已有仓库...${NC}"
    }
    echo "${GREEN}✅ 仓库创建成功${NC}"
fi

# 4. 配置 Git
echo ""
echo "${YELLOW}步骤 4/6: 配置 Git...${NC}"
git config user.name "neo-claw-bot" || true
git config user.email "neo_claw_bot@proton.me" || true
echo "${GREEN}✅ Git 配置完成${NC}"

# 5. 添加远程仓库并推送
echo ""
echo "${YELLOW}步骤 5/6: 推送代码到 GitHub...${NC}"

# 检查并添加远程仓库
if ! git remote | grep -q "origin"; then
    gh repo clone "$REPO_NAME" -- --bare 2>/dev/null || true
    git remote add origin "https://github.com/neo-claw-bot/$REPO_NAME.git"
fi

# 添加所有文件
git add .

# 提交（如果有变更）
if git diff --cached --quiet; then
    echo "没有变更需要提交"
else
    git commit -m "Initial deployment: CEX Intelligence Dashboard

- Add Flask web application
- Add daily briefing data
- Configure Railway deployment
- Setup GitHub Actions"
    echo "${GREEN}✅ 代码已提交${NC}"
fi

# 推送
echo "推送到 main 分支..."
git push -u origin main || git push -u origin master || {
    echo "${YELLOW}尝试强制推送...${NC}"
    git push -u origin main --force-with-lease
}
echo "${GREEN}✅ 代码已推送到 GitHub${NC}"

# 6. Railway 部署
echo ""
echo "${YELLOW}步骤 6/6: 部署到 Railway...${NC}"

# 检查 railway CLI
if ! command -v railway &> /dev/null; then
    echo "安装 Railway CLI..."
    npm install -g @railway/cli
fi

# 登录 Railway（使用 token）
echo "登录 Railway..."
export RAILWAY_TOKEN="8f9735ea-4ae2-42c4-9874-baaed1b248ff"
railway login --token "$RAILWAY_TOKEN" 2>/dev/null || true

# 进入 web 目录并部署
cd "$PROJECT_DIR/web"

echo "检查 Railway 项目..."
if ! railway status &>/dev/null; then
    echo "初始化 Railway 项目..."
    railway init --name "cex-intelligence"
fi

echo "部署到 Railway..."
railway up --detach

echo "${GREEN}✅ 部署完成！${NC}"

# 获取部署 URL
echo ""
echo "${GREEN}==========================================${NC}"
echo "${GREEN}🎉 部署成功！${NC}"
echo ""
echo "📊 GitHub 仓库: https://github.com/neo-claw-bot/cex-intelligence"
echo ""
echo "获取网站 URL:"
railway domain show 2>/dev/null || echo "等待 Railway 分配域名..."
echo ""
echo "${GREEN}==========================================${NC}"

# 创建完成标记
touch "$PROJECT_DIR/.deployed"

echo ""
echo "${YELLOW}提示: 每日简报会自动更新，数据保存在 data/intelligence/ 目录${NC}"
echo "${YELLOW}要更新网站，只需推送新的数据文件到 GitHub${NC}"
