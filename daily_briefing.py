#!/usr/bin/env python3
"""
CEX 每日简报生成器 - 中文版
用于定时任务生成每日简报（中文+URL引用）
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
    """采集每日情报（中文版）"""
    exchanges = ["Binance", "OKX", "Coinbase", "Bybit", "Bitget", "Kraken", "KuCoin"]
    today = datetime.now().strftime("%Y-%m-%d")
    
    prompt = f"""生成一份综合的CEX交易所每日情报简报（用中文回复）。

监控交易所: {', '.join(exchanges)}

搜索内容（最近24-48小时）:
1. 安全事件或黑客攻击
2. 提现/存款问题
3. 监管行动或法律问题
4. 服务中断或技术故障
5. 诈骗警告或用户投诉
6. 重大公告

请用中文返回结构化JSON报告，包含URL引用：
{{
  "summary": "用中文写的整体摘要",
  "alerts": [
    {{
      "exchange": "交易所名称",
      "severity": "critical|high|medium|low",
      "title": "中文标题",
      "description": "中文详细描述",
      "url": "相关新闻或推文链接"
    }}
  ],
  "exchange_status": {{
    "Binance": {{"status": "normal|warning|critical", "notes": "中文说明", "url": ""}},
    "OKX": {{"status": "normal|warning|critical", "notes": "中文说明", "url": ""}},
    "Coinbase": {{"status": "normal|warning|critical", "notes": "中文说明", "url": ""}},
    "Bybit": {{"status": "normal|warning|critical", "notes": "中文说明", "url": ""}},
    "Bitget": {{"status": "normal|warning|critical", "notes": "中文说明", "url": ""}},
    "Kraken": {{"status": "normal|warning|critical", "notes": "中文说明", "url": ""}},
    "KuCoin": {{"status": "normal|warning|critical", "notes": "中文说明", "url": ""}}
  }},
  "fintelegram_highlights": [
    {{"content": "中文内容", "url": "原文链接"}}
  ],
  "sources": [
    {{"name": "来源名称", "url": "链接"}}
  ]
}}

注意：
1. 所有文本字段必须用中文
2. 尽可能为每条情报提供来源URL
3. 如果没有某交易所的消息，status设为normal，notes为空
4. 如果没有相关情报，返回空数组"""

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
            "error": "解析失败",
            "summary": "数据采集异常，请稍后重试",
            "alerts": [],
            "exchange_status": {ex: {"status": "normal", "notes": "", "url": ""} for ex in exchanges},
            "fintelegram_highlights": [],
            "sources": []
        }

def save_intel(data: dict):
    """保存情报"""
    # 保存到项目目录
    data_dir = Path("/Users/neo/.openclaw/workspace-cex-intelligence/data/intelligence")
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # 保存到 web 目录（用于部署）
    web_data_dir = Path("/Users/neo/.openclaw/workspace-cex-intelligence/web/data/intelligence")
    web_data_dir.mkdir(parents=True, exist_ok=True)
    
    filepath = data_dir / f"{data['date']}.json"
    web_filepath = web_data_dir / f"{data['date']}.json"
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    with open(web_filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"💾 已保存: {filepath}")
    return filepath

def format_briefing(data: dict) -> str:
    """格式化为Discord消息（中文）"""
    lines = []
    lines.append("## 🎯 CEX 情报每日简报")
    lines.append(f"📅 {data['date']}")
    lines.append("")
    
    # 关键警报
    alerts = data.get("alerts", [])
    critical = [a for a in alerts if a.get("severity") == "critical"]
    high = [a for a in alerts if a.get("severity") == "high"]
    
    if critical:
        lines.append("🚨 **严重警报**")
        for a in critical:
            lines.append(f"🔴 **{a['exchange']}**: {a['title']}")
            if a.get('url'):
                lines.append(f"   [来源]({a['url']})")
        lines.append("")
    
    if high:
        lines.append("⚠️ **高风险事件**")
        for a in high[:3]:
            lines.append(f"🟠 **{a['exchange']}**: {a['title']}")
            if a.get('url'):
                lines.append(f"   [来源]({a['url']})")
        lines.append("")
    
    # 交易所状态
    lines.append("📊 **交易所状态**")
    for ex, info in data.get("exchange_status", {}).items():
        emoji = {"normal": "🟢", "warning": "🟡", "critical": "🔴"}.get(info.get("status"), "⚪")
        notes = info.get("notes", "")
        url = info.get("url", "")
        if notes:
            line = f"{emoji} **{ex}**: {notes[:60]}"
            if url:
                line += f" [🔗]({url})"
            lines.append(line)
        else:
            lines.append(f"{emoji} **{ex}**: 正常")
    
    # FinTelegram
    ft = data.get("fintelegram_highlights", [])
    if ft:
        lines.append("")
        lines.append(f"🔍 **FinTelegram**: {len(ft)} 条关注")
        for item in ft[:2]:
            content = item.get("content", item) if isinstance(item, dict) else item
            url = item.get("url", "") if isinstance(item, dict) else ""
            line = f"   • {content[:80]}"
            if url:
                line += f" [🔗]({url})"
            lines.append(line)
    
    # 摘要
    if data.get("summary"):
        lines.append("")
        lines.append(f"💡 **摘要**: {data['summary'][:200]}")
    
    # 数据来源
    sources = data.get("sources", [])
    if sources:
        lines.append("")
        lines.append("📚 **数据来源**:")
        for src in sources[:3]:
            name = src.get("name", "未知")
            url = src.get("url", "")
            if url:
                lines.append(f"   • [{name}]({url})")
            else:
                lines.append(f"   • {name}")
    
    lines.append("")
    lines.append("—")
    lines.append("💬 回复 `详情 [交易所名]` 获取更多信息")
    
    return "\n".join(lines)

def generate_briefing():
    """生成每日简报主流程"""
    print("🚀 CEX 每日简报生成器（中文版）")
    print("=" * 50)
    
    # 采集今日情报
    data = collect_daily_intel()
    
    # 保存
    save_intel(data)
    
    # 格式化输出
    briefing = format_briefing(data)
    
    # 输出到文件
    output_file = Path("/Users/neo/.openclaw/workspace-cex-intelligence/data/last_briefing.txt")
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(briefing)
    
    # 同时保存到 web 目录
    web_output_file = Path("/Users/neo/.openclaw/workspace-cex-intelligence/web/data/last_briefing.txt")
    with open(web_output_file, 'w', encoding='utf-8') as f:
        f.write(briefing)
    
    print("\n" + "=" * 50)
    print("✅ 简报生成完成")
    print(briefing)
    
    return briefing

if __name__ == "__main__":
    briefing = generate_briefing()
