#!/usr/bin/env python3
"""
发送CEX简报到Discord
"""

import json
import subprocess
from datetime import datetime
from pathlib import Path

def load_today_briefing() -> dict:
    """加载今日简报数据"""
    today = datetime.now().strftime("%Y-%m-%d")
    data_file = Path(f"/Users/neo/.openclaw/workspace-cex-intelligence/data/intelligence/{today}.json")
    
    if not data_file.exists():
        return None
    
    with open(data_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def format_discord_message(data: dict) -> str:
    """格式化为Discord消息"""
    lines = []
    lines.append("## 🎯 CEX 情报每日简报")
    lines.append(f"📅 {data['date']} | ⏰ {data['collected_at'][:16]}")
    lines.append("")
    
    # 关键警报
    alerts = data.get("alerts", [])
    critical = [a for a in alerts if a.get("severity") == "critical"]
    high = [a for a in alerts if a.get("severity") == "high"]
    medium = [a for a in alerts if a.get("severity") == "medium"]
    
    if critical:
        lines.append("### 🚨 严重警报")
        for a in critical:
            lines.append(f"🔴 **{a['exchange']}**: {a['title']}")
            desc = a.get('description', '')[:200]
            lines.append(f"> {desc}...")
        lines.append("")
    
    if high:
        lines.append("### ⚠️ 高风险事件")
        for a in high:
            lines.append(f"🟠 **{a['exchange']}**: {a['title']}")
        lines.append("")
    
    if medium and not critical and not high:
        lines.append("### 📊 中风险关注")
        for a in medium[:2]:
            lines.append(f"🟡 **{a['exchange']}**: {a['title']}")
        lines.append("")
    
    # 交易所状态
    lines.append("### 📊 交易所状态")
    status_emoji = {"normal": "🟢", "warning": "🟡", "critical": "🔴"}
    
    for ex, info in data.get("exchange_status", {}).items():
        emoji = status_emoji.get(info.get("status", "normal"), "⚪")
        notes = info.get("notes", "")
        if notes and info.get("status") != "normal":
            lines.append(f"{emoji} **{ex}**: {notes[:80]}{'...' if len(notes) > 80 else ''}")
        elif info.get("status") == "normal":
            lines.append(f"{emoji} **{ex}**: 正常")
    
    # FinTelegram
    ft = data.get("fintelegram_highlights", [])
    if ft:
        lines.append("")
        lines.append(f"### 🔍 FinTelegram ({len(ft)} 条)")
        for item in ft[:2]:
            lines.append(f"• {item[:100]}{'...' if len(item) > 100 else ''}")
    
    # 摘要
    if data.get("summary"):
        lines.append("")
        lines.append(f"**💡 摘要**: {data['summary'][:200]}{'...' if len(data['summary']) > 200 else ''}")
    
    return "\n".join(lines)

def send_to_discord(message: str):
    """发送到Discord - 通过openclaw命令"""
    # 保存消息到文件
    msg_file = Path("/Users/neo/.openclaw/workspace-cex-intelligence/data/last_discord_msg.txt")
    with open(msg_file, 'w', encoding='utf-8') as f:
        f.write(message)
    
    print(f"💾 消息已保存: {msg_file}")
    print("📤 消息预览:")
    print("-" * 50)
    print(message)
    print("-" * 50)
    
    # 提示用户可以通过openclaw发送
    print("\n✅ 简报已生成。使用以下命令发送:")
    print(f"  openclaw message send --file {msg_file}")

def main():
    """主入口"""
    data = load_today_briefing()
    
    if not data:
        print("❌ 未找到今日简报数据。请先运行 daily_briefing.py")
        return
    
    message = format_discord_message(data)
    send_to_discord(message)

if __name__ == "__main__":
    main()
