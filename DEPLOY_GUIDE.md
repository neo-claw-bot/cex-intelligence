# CEX Intelligence Web 部署指南

## 📋 项目结构
```
web/
├── app.py              # Flask 主应用
├── requirements.txt    # Python 依赖
├── Procfile           # Railway 进程配置
├── railway.json       # Railway 配置
├── README.md          # 项目说明
└── templates/
    └── index.html     # 网页模板
```

## 🚀 部署步骤

### 1. 创建 GitHub 仓库

使用提供的账号登录 GitHub：
- 用户名: `neo-claw-bot`
- 邮箱: `neo_claw_bot@proton.me`
- 密码: `Hodna7-qozrob-xexxyw`

创建新仓库:
```bash
# 仓库名称: cex-intelligence
# 可见性: Public 或 Private
```

### 2. 推送代码到 GitHub

```bash
# 在项目根目录初始化git
cd /Users/neo/.openclaw/workspace-cex-intelligence
git init
git add .
git commit -m "Initial commit: CEX Intelligence Dashboard"

# 添加远程仓库
git remote add origin https://github.com/neo-claw-bot/cex-intelligence.git

# 推送代码
git branch -M main
git push -u origin main
```

### 3. 部署到 Railway

#### 方式 A: 通过 Railway CLI

```bash
# 安装 Railway CLI
npm install -g @railway/cli

# 登录 Railway
railway login

# 进入 web 目录
cd web

# 初始化项目
railway init --name cex-intelligence

# 部署
railway up
```

#### 方式 B: 通过 Railway 网页

1. 访问 https://railway.app
2. 点击 "New Project" → "Deploy from GitHub repo"
3. 选择 `neo-claw-bot/cex-intelligence` 仓库
4. Railway 会自动检测配置并部署

### 4. 配置环境变量

在 Railway Dashboard 中添加环境变量:
```
PYTHON_VERSION=3.11
```

### 5. 配置自动更新

在 Railway Dashboard → Settings → Cron Jobs 中添加:
```
# 每天 09:00, 15:00, 21:00 (北京时间)
0 1 * * * curl -X POST https://your-app-url.railway.app/api/refresh
0 7 * * * curl -X POST https://your-app-url.railway.app/api/refresh
0 13 * * * curl -X POST https://your-app-url.railway.app/api/refresh
```

## 🔧 数据更新机制

### 本地数据采集
在本地机器运行:
```bash
python3 daily_briefing.py
```

### 自动同步到 Railway
数据文件位于 `data/intelligence/YYYY-MM-DD.json`

可以通过以下方式同步:
1. GitHub Actions 自动推送
2. 手动推送到仓库
3. 使用 Railway Volume 持久化存储

### 推荐方案: GitHub Actions + Railway

已在 `.github/workflows/deploy.yml` 配置自动部署:
- 每次推送到 main 分支自动部署
- 每天定时 09:00, 15:00, 21:00 自动更新

## 📊 API 端点

部署后可通过以下 API 访问数据:

- `GET /` - 网页界面（最新数据）
- `GET /api/latest` - 最新简报 JSON
- `GET /api/dates` - 可用日期列表
- `GET /api/YYYY-MM-DD` - 指定日期数据

## 🌐 访问网站

部署成功后，Railway 会提供域名:
```
https://cex-intelligence-production.up.railway.app
```

## 🔄 更新流程

### 每日自动更新
1. OpenClaw 运行 `daily_briefing.py` 采集数据
2. 数据保存到 `data/intelligence/`
3. GitHub Actions 定时推送更新
4. Railway 自动重新部署

### 手动更新
```bash
cd /Users/neo/.openclaw/workspace-cex-intelligence
python3 daily_briefing.py
git add data/intelligence/
git commit -m "Update: $(date +%Y-%m-%d) briefing"
git push
```

## 🛠️ 故障排除

### 问题1: 部署失败
- 检查 `requirements.txt` 是否正确
- 查看 Railway 日志: `railway logs`

### 问题2: 数据不显示
- 确认 JSON 文件格式正确
- 检查文件路径: `data/intelligence/YYYY-MM-DD.json`

### 问题3: 定时任务不执行
- 检查 GitHub Actions 状态
- 确认 RAILWAY_TOKEN 已配置

## 📞 支持

如有问题，请检查:
1. Railway Dashboard 日志
2. GitHub Actions 运行记录
3. 本地数据文件是否正确生成
