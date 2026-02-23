#!/usr/bin/env python3
"""
CEX 每日简报生成器 - 轻量版
用于定时任务生成每日简报
"""

import os
import json
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

def call_grok(prompt: str, tools: list) -> dict:
    """调用 Grok API"""
    api_key = os.getenv("XAI_API_KEY")
    data = {
        "model": "grok-4-1-fast-reasoning",
        "input": [{"role": "user", "content": prompt}],
        "tools": tools
    }
    
    curl_cmd = [
        "curl", "-s", "--max-time", "60",
        "https://api.x.ai/v1/responses",
        "-H", "Content-Type: application/json",
        "-H", f"Authorization: Bearer {api_key}",
        "-d", json.dumps(data, ensure_ascii=False)
    ]
    
    result = subprocess.run(curl_cmd, capture_output=True, text=True, timeout=65)
    return json.loads(result.stdout) if result.returncode == 0 else {"error": result.stderr}

def extract_text(response: dict) -> str:
    """提取响应文本"""
    try:
        for item in response.get("output", []):
            if item.get("type") == "message" or item.get("role") == "assistant":
                for content in item.get("content", []):
                    if content.get("type") in ["text", "output_text"]:
                        return content.get("text", "")
    except:
        pass
    return ""

def collect_daily_intel() -> dict:
    """采集每日情报"""
    exchanges = ["Binance", "OKX", "Coinbase", "Bybit", "Bitget", "Kraken", "KuCoin"]
    today = datetime.now().strftime("%Y-%m-%d")
    
    prompt = f"""Generate a comprehensive daily intelligence briefing for major crypto exchanges: {', '.join(exchanges)}.

Search for (last 24-48 hours):
1. Security incidents or hacks
2. Withdrawal/deposit issues  
3. Regulatory actions or legal issues
4. Service outages or technical problems
5. Scam warnings or user complaints
6. Major announcements

Return a structured JSON report:
{{
  "summary": "brief overall summary",
  "alerts": [
    {{"exchange": "name", "severity": "critical|high|medium|low", "title": "alert title", "description": "details"}}
  ],
  "exchange_status": {{
    "Binance": {{"status": "normal|warning|critical", "notes": "brief notes"}},
    "OKX": {{"status": "normal|warning|critical", "notes": "brief notes"}},
    "Coinbase": {{"status": "normal|warning|critical", "notes": "brief notes"}},
    "Bybit": {{"status": "normal|warning|critical", "notes": "brief notes"}},
    "Bitget": {{"status": "normal|warning|critical", "notes": "brief notes"}},
    "Kraken": {{"status": "normal|warning|critical", "notes": "brief notes"}},
    "KuCoin": {{"status": "normal|warning|critical", "notes": "brief notes"}}
  }},
  "fintelegram_highlights": ["key findings"],
  "sources_checked": ["x_search", "web_search"]
}}

Be concise but thorough. If no issues found for an exchange, mark as "normal"."""

    print(f"🔍 正在采集 {today} 的情报...")
    response = call_grok(prompt, [{"type": "x_search"}, {"type": "web_search"}])
    text = extract_text(response)
    
    try:
        data = json.loads(text) if text else {}
        data["date"] = today
        data["collected_at"] = datetime.now().isoformat()
        return data
    except:
        return {
            "date": today,
            "collected_at": datetime.now().isoformat(),
            "error": "Failed to parse response",
            "raw_text": text[:500] if text else ""
        }

def save_intel(data: dict):
    """保存情报"""
    data_dir = Path("/Users/neo/.openclaw/workspace-cex-intelligence/data/intelligence")
    data_dir.mkdir(parents=True, exist_ok=True)
    
    filepath = data_dir / f"{data['date']}.json"
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"💾 已保存: {filepath}")
    return filepath

def load_intel(date: str) -> dict:
    """加载指定日期情报"""
    data_dir = Path("/Users/neo/.openclaw/workspace-cex-intelligence/data/intelligence")
    filepath = data_dir / f"{date}.json"
    
    if filepath.exists():
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

def format_briefing(data: dict) -> str:
    """格式化简报"""
    lines = []
    lines.append("🎯 **CEX 情报每日简报**")
    lines.append(f"📅 {data['date']} | ⏰ {data['collected_at'][:16]}")
    lines.append("")
    
    # 关键警报
    alerts = data.get("alerts", [])
    critical = [a for a in alerts if a.get("severity") == "critical"]
    high = [a for a in alerts if a.get("severity") == "high"]
    
    if critical:
        lines.append("🚨 **严重警报**")
        for a in critical:
            lines.append(f"🔴 **{a['exchange']}**: {a['title']}")
            lines.append(f"   {a.get('description', '')[:150]}...")
        lines.append("")
    
    if high:
        lines.append("⚠️ **高风险事件**")
        for a in high[:3]:
            lines.append(f"🟠 **{a['exchange']}**: {a['title']}")
        lines.append("")
    
    # 交易所状态
    lines.append("📊 **交易所状态**")
    status_emoji = {"normal": "✅", "warning": "⚠️", "critical": "🚨"}
    
    for ex, info in data.get("exchange_status", {}).items():
        emoji = status_emoji.get(info.get("status", "normal"), "⚪")
        notes = info.get("notes", "")
        if notes:
            lines.append(f"{emoji} **{ex}**: {notes[:60]}{'...' if len(notes) > 60 else ''}")
        else:
            lines.append(f"{emoji} **{ex}**: 正常")
    
    # FinTelegram
    ft = data.get("fintelegram_highlights", [])
    if ft:
        lines.append("")
        lines.append(f"🔍 **FinTelegram**: {len(ft)} 条关注")
        for item in ft[:2]:
            lines.append(f"   • {item[:80]}{'...' if len(item) > 80 else ''}")
    
    # 摘要
    if data.get("summary"):
        lines.append("")
        lines.append(f"💡 **摘要**: {data['summary']}")
    
    lines.append("")
    lines.append("—")
    lines.append("💬 回复 `详情 [交易所名]` 获取更多信息")
    
    return "\n".join(lines)

def generate_briefing():
    """生成每日简报主流程"""
    print("🚀 CEX 每日简报生成器")
    print("=" * 50)
    
    # 采集今日情报
    data = collect_daily_intel()
    
    # 保存
    save_intel(data)
    
    # 格式化输出
    briefing = format_briefing(data)
    
    # 输出到文件（便于读取）
    output_file = Path("/Users/neo/.openclaw/workspace-cex-intelligence/data/last_briefing.txt")
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(briefing)
    
    print("\n" + "=" * 50)
    print("✅ 简报生成完成")
    print(briefing)
    
    return briefing

if __name__ == "__main__":
    briefing = generate_briefing()
