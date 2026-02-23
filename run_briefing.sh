#!/bin/bash
# CEX 情报简报包装脚本

SCRIPT_DIR="/Users/neo/.openclaw/workspace-cex-intelligence"
LOG_FILE="$SCRIPT_DIR/data/cron.log"

# 记录开始时间
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting CEX briefing..." >> "$LOG_FILE"

# 运行简报生成器
cd "$SCRIPT_DIR"
/opt/homebrew/bin/python3 daily_briefing.py >> "$LOG_FILE" 2>&1

# 检查是否成功
if [ -f "$SCRIPT_DIR/data/last_discord_msg.txt" ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Briefing generated successfully" >> "$LOG_FILE"
    # 输出简报内容（供 OpenClaw 读取）
    cat "$SCRIPT_DIR/data/last_discord_msg.txt"
    exit 0
else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Failed to generate briefing" >> "$LOG_FILE"
    exit 1
fi
