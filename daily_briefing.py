#!/usr/bin/env python3
"""
CEX 每日简报生成器 - 中文版（分批采集版）
用于定时任务生成每日简报（中文+准确URL引用）
每天采集所有23个交易所的最新情报
"""

import os
import json
import subprocess
from datetime import datetime
from pathlib import Path

def call_grok(prompt: str, tools: list, timeout: int = 120) -> dict:
    """调用 Grok API"""
    api_key = os.getenv("XAI_API_KEY")
    if not api_key:
        print("❌ 错误: 未设置 XAI_API_KEY 环境变量")
        return {"error": "Missing API key"}
    
    data = {
        "model": "grok-4-1-fast-reasoning",
        "input": [{"role": "user", "content": prompt}],
        "tools": tools
    }
    
    curl_cmd = [
        "curl", "-s", "--max-time", str(timeout),
        "https://api.x.ai/v1/responses",
        "-H", "Content-Type: application/json",
        "-H", f"Authorization: Bearer {api_key}",
        "-d", json.dumps(data, ensure_ascii=False)
    ]
    
    try:
        result = subprocess.run(curl_cmd, capture_output=True, text=True, timeout=timeout+10)
        if result.returncode != 0:
            print(f"⚠️ curl 错误: {result.stderr}")
            return {"error": result.stderr}
        return json.loads(result.stdout)
    except Exception as e:
        print(f"⚠️ 请求错误: {e}")
        return {"error": str(e)}

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

def is_generic_url(url: str) -> bool:
    """检查 URL 是否为通用链接（官网首页等）"""
    if not url:
        return True
    
    generic_patterns = [
        "twitter.com/home", "twitter.com", "x.com",
        "kucoin.com", "binance.com", "coinbase.com",
        "bitget.com", "kraken.com", "okx.com", "bybit.com",
        "mexc.com", "gate.io", "htx.com", "crypto.com",
        "lbank.com", "upbit.com", "whitebit.com", "deribit.com",
        "fma.gv.at", "fintelegram.com",
        "coindesk.com", "cointelegraph.com"
    ]
    
    url_lower = url.lower().rstrip('/')
    for pattern in generic_patterns:
        if url_lower in [f"https://{pattern}", f"http://{pattern}", 
                        f"https://www.{pattern}", f"http://www.{pattern}"]:
            return True
    return False

def collect_exchange_batch(batch: list, batch_num: int, total_batches: int) -> dict:
    """采集一批交易所的情报"""
    print(f"\n🔍 [{batch_num}/{total_batches}] 采集: {', '.join(batch)}")
    
    prompt = f"""搜索以下交易所最近24-48小时的情报（用中文回复）：

交易所: {', '.join(batch)}

搜索：安全事件、提现问题、监管行动、服务中断、诈骗警告、重大公告

返回JSON：
{{
  "alerts": [
    {{
      "exchange": "交易所名",
      "severity": "critical|high|medium|low",
      "title": "中文标题",
      "description": "中文描述",
      "url": "具体链接或空",
      "source_name": "来源",
      "tags": ["twitter","news","regulatory","security","user_report"]
    }}
  ],
  "exchange_status": {{
    "交易所名": {{"status": "normal|warning|critical", "notes": "说明", "url": "链接"}}
  }},
  "sources": [{{"name": "来源", "url": "链接"}}]
}}

规则：
1. 无事件返回空数组
2. URL要具体文章，不要官网
3. 必须用中文
4. 每个交易所有独立状态"""
    
    response = call_grok(prompt, [{"type": "x_search"}, {"type": "web_search"}], timeout=100)
    text = extract_text(response)
    
    try:
        data = json.loads(text) if text else {}
        alerts = data.get("alerts", [])
        print(f"   ✅ 发现 {len(alerts)} 条警报")
        return data
    except Exception as e:
        print(f"   ⚠️ 解析失败: {e}")
        return {}

def collect_daily_intel() -> dict:
    """采集每日情报 - 分批采集所有23个交易所"""
    exchanges = [
        "Binance", "MEXC", "Gate", "Bitget", "OKX", "HTX", "Bybit", "Coinbase",
        "CoinW", "BitMart", "Crypto.com", "DigiFinex", "LBank", "Upbit", "Toobit",
        "WEEX", "P2B", "XT.COM", "Tapbit", "Kraken",
        "KuCoin", "WhiteBIT", "Deribit"
    ]
    today = datetime.now().strftime("%Y-%m-%d")
    
    print("=" * 70)
    print(f"🚀 CEX 每日情报采集启动 | {today}")
    print(f"📊 目标: {len(exchanges)} 个交易所")
    print("=" * 70)
    
    # 分批采集（每批5-6个，避免超时）
    batch_size = 6
    batches = [exchanges[i:i+batch_size] for i in range(0, len(exchanges), batch_size)]
    
    all_alerts = []
    all_exchange_status = {}
    all_sources = []
    
    for i, batch in enumerate(batches, 1):
        data = collect_exchange_batch(batch, i, len(batches))
        
        # 合并警报
        if data.get("alerts"):
            for alert in data["alerts"]:
                if is_generic_url(alert.get("url", "")):
                    alert["url"] = ""
                all_alerts.append(alert)
        
        # 合并状态
        if data.get("exchange_status"):
            for ex, info in data["exchange_status"].items():
                if is_generic_url(info.get("url", "")):
                    info["url"] = ""
                all_exchange_status[ex] = info
        
        # 合并来源
        if data.get("sources"):
            all_sources.extend(data["sources"])
    
    # 确保所有交易所有状态记录
    for ex in exchanges:
        if ex not in all_exchange_status:
            all_exchange_status[ex] = {"status": "normal", "notes": "", "url": ""}
    
    # 生成摘要
    summary = generate_summary(all_alerts)
    
    final_data = {
        "date": today,
        "collected_at": datetime.now().isoformat(),
        "summary": summary,
        "alerts": all_alerts,
        "exchange_status": all_exchange_status,
        "fintelegram_highlights": [],
        "sources": all_sources,
        "total_exchanges": len(exchanges),
        "total_batches": len(batches)
    }
    
    print("\n" + "=" * 70)
    print(f"✅ 采集完成")
    print(f"📊 总计: {len(all_alerts)} 条情报")
    print(f"🏢 覆盖: {len(all_exchange_status)} 个交易所")
    print(f"📝 摘要: {summary[:60]}...")
    print("=" * 70)
    
    return final_data

def generate_summary(alerts: list) -> str:
    """根据警报生成摘要"""
    if not alerts:
        return "过去24-48小时内，所有监控的23个交易所运营正常，未发现重大安全事件、监管行动或用户投诉。"
    
    critical = len([a for a in alerts if a.get("severity") == "critical"])
    high = len([a for a in alerts if a.get("severity") == "high"])
    exchanges = list(set(a.get("exchange", "") for a in alerts))[:3]
    
    if critical > 0:
        return f"过去24-48小时发现{critical}起严重事件，涉及{', '.join(exchanges)}等交易所，建议立即关注并采取防范措施。"
    elif high > 0:
        return f"过去24-48小时发现{high}起高风险事件，涉及{', '.join(exchanges)}等交易所，需要密切关注动态。"
    else:
        return f"过去24-48小时发现{len(alerts)}起一般性事件，涉及{', '.join(exchanges)}等交易所，整体风险可控。"

def save_intel(data: dict):
    """保存情报到文件"""
    # 项目目录
    data_dir = Path("/Users/neo/.openclaw/workspace-cex-intelligence/data/intelligence")
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # web 目录（用于部署）
    web_data_dir = Path("/Users/neo/.openclaw/workspace-cex-intelligence/web/data/intelligence")
    web_data_dir.mkdir(parents=True, exist_ok=True)
    
    date = data['date']
    
    # 保存到两个位置
    for dir_path in [data_dir, web_data_dir]:
        filepath = dir_path / f"{date}.json"
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"💾 已保存: {filepath}")
    
    # 同时保存为最新简报
    briefing_file = Path("/Users/neo/.openclaw/workspace-cex-intelligence/data/last_briefing.txt")
    with open(briefing_file, 'w', encoding='utf-8') as f:
        f.write(format_discord_message(data))
    
    return filepath

def format_discord_message(data: dict) -> str:
    """格式化为 Discord 消息"""
    lines = [f"## 🎯 CEX 情报每日简报\n📅 {data['date']}\n"]
    
    alerts = data.get("alerts", [])
    critical = [a for a in alerts if a.get("severity") == "critical"]
    high = [a for a in alerts if a.get("severity") == "high"]
    
    if critical:
        lines.append("🚨 **严重警报**")
        for a in critical[:2]:
            lines.append(f"🔴 **{a['exchange']}**: {a['title']}")
    
    if high:
        lines.append("\n⚠️ **高风险事件**")
        for a in high[:3]:
            lines.append(f"🟠 **{a['exchange']}**: {a['title']}")
    
    lines.append("\n📊 **交易所状态概览**")
    for ex, info in list(data.get("exchange_status", {}).items())[:5]:
        emoji = {"normal": "🟢", "warning": "🟡", "critical": "🔴"}.get(info.get("status"), "⚪")
        notes = info.get("notes", "")[:30]
        lines.append(f"{emoji} **{ex}**: {notes if notes else '正常'}")
    
    lines.append(f"\n💡 **摘要**: {data.get('summary', '')[:100]}...")
    lines.append("\n—")
    lines.append("🔗 查看详情: https://cex-intelligence-production.up.railway.app")
    
    return "\n".join(lines)

def main():
    """主入口"""
    print("🚀 CEX Intelligence - 每日情报采集系统")
    print("📝 采集所有23个交易所的最新情报\n")
    
    # 采集数据
    data = collect_daily_intel()
    
    # 保存
    save_intel(data)
    
    print("\n✅ 完成！数据已保存并准备发布。")
    print(f"📊 共采集 {len(data.get('alerts', []))} 条情报")
    print(f"🌐 网站: https://cex-intelligence-production.up.railway.app")

if __name__ == "__main__":
    main()
