# CEX Intelligence Railway 部署指南

## 部署状态

⚠️ **注意**: 当前环境中无法执行 Git 命令（需要配置配对节点）。已为你准备了部署脚本。

## 快速部署

### 方法 1: 运行部署脚本

在配置好节点后，执行以下命令：

```bash
cd /Users/neo/.openclaw/workspace-cex-intelligence
chmod +x deploy-to-railway.sh
./deploy-to-railway.sh
```

### 方法 2: 手动执行

如果脚本无法运行，可以手动执行以下命令：

```bash
# 1. 进入项目目录
cd /Users/neo/.openclaw/workspace-cex-intelligence

# 2. 初始化 Git 仓库（如果未初始化）
git init

# 3. 配置 Git 用户名和邮箱
git config user.name "neo-claw-bot"
git config user.email "neo_claw_bot@proton.me"

# 4. 添加所有文件
git add .

# 5. 提交代码
git commit -m "Initial commit for Railway deployment"

# 6. 添加远程仓库（如果没有）
git remote add origin https://github.com/neo-claw-bot/cex-intelligence.git

# 7. 推送代码到 main 分支
git branch -M main
git push -u origin main
```

## 重要提示

### 1. GitHub 仓库

在推送代码之前，请确保 GitHub 仓库已创建：
- 仓库地址: https://github.com/neo-claw-bot/cex-intelligence
- 如果不存在，需要先创建该仓库

### 2. 身份验证

推送代码时需要身份验证，可以使用：
- SSH 密钥（推荐）
- GitHub Personal Access Token
- GitHub CLI (`gh auth login`)

### 3. Railway 部署

代码推送到 GitHub 后，在 Railway 中：
1. 登录 Railway 控制台
2. 创建新项目
3. 选择 "Deploy from GitHub repo"
4. 选择 `neo-claw-bot/cex-intelligence` 仓库
5. Railway 会自动部署项目

## 部署后检查

部署完成后，验证以下信息：

```bash
# 检查 Git 状态
git status

# 检查远程仓库
git remote -v

# 检查提交历史
git log --oneline -5
```

## 文件说明

- `deploy-to-railway.sh` - 自动化部署脚本
- `DEPLOY.md` - 本部署指南

---
*生成时间: 2026-02-24*