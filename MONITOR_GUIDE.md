# CEX 情报监控系统 - 使用指南

## 📁 文件结构

```
workspace-cex-intelligence/
├── daily_briefing.py          # 每日简报生成器
├── cex_monitor.py             # 完整版监控器（带历史比对）
├── send_briefing.py           # Discord发送脚本
├── crontab.txt                # 定时任务配置
└── data/
    ├── intelligence/          # 每日情报数据
    │   └── YYYY-MM-DD.json
    ├── last_briefing.txt      # 最新简报文本
    ├── last_discord_msg.txt   # 最新Discord消息
    └── cron.log               # 定时任务日志
```

## 🚀 使用方法

### 1. 手动生成今日简报
```bash
cd /Users/neo/.openclaw/workspace-cex-intelligence
python3 daily_briefing.py
```

### 2. 发送到Discord
```bash
# 方式1: 通过openclaw命令
openclaw message send --channel discord --content-file data/last_discord_msg.txt

# 方式2: 手动复制内容发送
# 查看 data/last_discord_msg.txt 并复制到Discord
```

### 3. 查看历史数据
```bash
python3 cex_monitor.py --history
python3 cex_monitor.py --date 2026-02-21
```

## ⏰ 设置定时任务

### macOS/Linux (crontab)
```bash
# 编辑crontab
crontab -e

# 添加以下行（每日北京时间 09:00, 15:00, 21:00 执行）
0 9,15,21 * * * cd /Users/neo/.openclaw/workspace-cex-intelligence && /opt/homebrew/bin/python3 daily_briefing.py >> data/cron.log 2>&1
```

### 使用 OpenClaw Cron (推荐)
将以下内容添加到 OpenClaw 配置:
```yaml
cron:
  - name: cex-morning-briefing
    schedule: "0 9 * * *"
    command: "cd /Users/neo/.openclaw/workspace-cex-intelligence && python3 daily_briefing.py"
    channel: discord
    
  - name: cex-afternoon-briefing
    schedule: "0 15 * * *"
    command: "cd /Users/neo/.openclaw/workspace-cex-intelligence && python3 daily_briefing.py"
    channel: discord
    
  - name: cex-evening-briefing
    schedule: "0 21 * * *"
    command: "cd /Users/neo/.openclaw/workspace-cex-intelligence && python3 daily_briefing.py"
    channel: discord
```

## 📊 监控范围

### 交易所
- Binance
- OKX
- Coinbase
- Bybit
- Bitget
- Kraken
- KuCoin
- Gate.io (可选)
- MEXC (可选)

### 情报来源
- X (Twitter) 社区讨论
- Web 新闻搜索
- FinTelegram 警告

### 监控指标
| 级别 | 说明 |
|------|------|
| 🔴 Critical | 黑客攻击、大量资金损失、服务完全中断 |
| 🟠 High | 监管行动、提现暂停、重大安全漏洞 |
| 🟡 Medium | 用户投诉、合规问题、小额技术故障 |
| 🟢 Low | 一般性公告、正面新闻 |

## 🔧 配置调整

### 修改监控交易所
编辑 `daily_briefing.py` 第85行:
```python
exchanges = ["Binance", "OKX", "Coinbase", "Bybit", "Bitget", "Kraken", "KuCoin"]
```

### 调整采集频率
修改 `crontab.txt` 中的时间设置:
```
# 每4小时一次
0 */4 * * * ...

# 每天一次（早9点）
0 9 * * * ...
```

## 📝 日志查看

```bash
# 查看定时任务日志
tail -f data/cron.log

# 查看最新简报
cat data/last_briefing.txt

# 查看某日数据
jq '.' data/intelligence/2026-02-22.json
```

## ⚠️ 注意事项

1. **API Key**: 确保 `XAI_API_KEY` 环境变量已设置
2. **网络**: Grok API 需要稳定的国际网络连接
3. **成本**: 每次采集消耗约 0.5-1 美元 API 额度
4. **时效性**: 简报基于过去24-48小时的数据

## 🔄 工作流程

```
[定时触发] → [Grok搜索X+Web] → [解析结果] → [保存JSON]
                                                 ↓
[Discord通知] ← [格式化简报] ← [加载昨日数据比对]
```
