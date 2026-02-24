#!/usr/bin/env python3
"""
CEX 每日简报生成器 - 中文版（改进版）
用于定时任务生成每日简报（中文+准确URL引用）
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
        "curl", "-s", "--max-time", "90",
        "https://api.x.ai/v1/responses",
        "-H", "Content-Type: application/json",
        "-H", f"Authorization: Bearer {api_key}",
        "-d", json.dumps(data, ensure_ascii=False)
    ]
    
    result = subprocess.run(curl_cmd, capture_output=True, text=True, timeout=95)
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

def is_generic_url(url: str) -> bool:
    """检查 URL 是否为通用链接（官网首页等）"""
    if not url:
        return True
    
    generic_patterns = [
        "twitter.com/home",
        "twitter.com",
        "x.com",
        "kucoin.com",
        "binance.com",
        "coinbase.com",
        "bitget.com",
        "kraken.com",
        "okx.com",
        "bybit.com",
        "fma.gv.at",
        "fintelegram.com",
        "coindesk.com",
        "cointelegraph.com"
    ]
    
    url_lower = url.lower().rstrip('/')
    for pattern in generic_patterns:
        if url_lower == f"https://{pattern}" or url_lower == f"http://{pattern}" or url_lower == f"https://www.{pattern}" or url_lower == f"http://www.{pattern}":
            return True
    
    return False

def collect_daily_intel() -> dict:
    """采集每日情报（中文版）"""
    exchanges = [
        # CER.live 按交易量前20
        "Binance", "MEXC", "Gate", "Bitget", "OKX", "HTX", "Bybit", "Coinbase",
        "CoinW", "BitMart", "Crypto.com", "DigiFinex", "LBank", "Upbit", "Toobit",
        "WEEX", "P2B", "XT.COM", "Tapbit", "Kraken",
        # CER.live 安全评分前列
        "KuCoin", "WhiteBIT", "Deribit"
    ]
    today = datetime.now().strftime("%Y-%m-%d")
    
    prompt = f"""搜索并生成CEX交易所情报简报（用中文回复）。

监控交易所: {', '.join(exchanges)}

搜索内容（最近24-48小时）:
1. 安全事件或黑客攻击
2. 提现/存款问题  
3. 监管行动或法律问题
4. 服务中断或技术故障
5. 诈骗警告或用户投诉
6. 重大公告

重要：对于每条情报，请提供：
- 具体的新闻文章URL（如 https://coindesk.com/.../article-name）
- 或具体的推文链接（如 https://twitter.com/username/status/1234567890）
- 不要使用交易所官网主页作为URL
- 如果没有找到具体的新闻链接，url字段留空
- tags字段：添加来源标签数组，可选值：
  * "twitter" - X/Twitter来源
  * "news" - 新闻媒体（CoinDesk, The Block等）
  * "official" - 交易所官方公告
  * "user_report" - 用户投诉/报告
  * "regulatory" - 监管机构
  * "security" - 安全公司/审计
  * "forum" - 论坛/Reddit

返回格式（中文JSON）：
{{
  "summary": "用中文写的整体摘要",
  "alerts": [
    {{
      "exchange": "交易所名称",
      "severity": "critical|high|medium|low", 
      "title": "中文标题",
      "description": "中文详细描述",
      "url": "具体的新闻或推文链接，如果没有则留空",
      "source_name": "来源名称（如CoinDesk、The Block、X用户@username）",
      "tags": ["twitter", "news", "official", "user_report"] // 标签数组
    }}
  ],
  "exchange_status": {{
    "Binance": {{"status": "normal|warning|critical", "notes": "中文说明", "url": "具体链接或空"}},
    "OKX": {{"status": "normal|warning|critical", "notes": "中文说明", "url": "具体链接或空"}},
    "Coinbase": {{"status": "normal|warning|critical", "notes": "中文说明", "url": "具体链接或空"}},
    "Bybit": {{"status": "normal|warning|critical", "notes": "中文说明", "url": "具体链接或空"}},
    "Bitget": {{"status": "normal|warning|critical", "notes": "中文说明", "url": "具体链接或空"}},
    "Kraken": {{"status": "normal|warning|critical", "notes": "中文说明", "url": "具体链接或空"}},
    "KuCoin": {{"status": "normal|warning|critical", "notes": "中文说明", "url": "具体链接或空"}}
  }},
  "fintelegram_highlights": [
    {{"content": "中文内容", "url": "具体文章链接或空", "source_name": "来源"}}
  ],
  "sources": [
    {{"name": "来源名称", "url": "具体链接", "type": "news|twitter|official"}}
  ]
}}

注意：
1. 所有文本必须用中文
2. URL 必须是具体的新闻文章或推文链接，不要用官网主页
3. 如果找不到具体来源，url 字段留空字符串""
4. 优先使用知名新闻源：CoinDesk, The Block, Cointelegraph, Decrypt等"""

    print(f"🔍 正在采集 {today} 的情报...")
    response = call_grok(prompt, [{"type": "x_search"}, {"type": "web_search"}])
    text = extract_text(response)
    
    try:
        data = json.loads(text) if text else {}
        
        # 过滤掉通用 URL
        if data.get("alerts"):
            for alert in data["alerts"]:
                if is_generic_url(alert.get("url", "")):
                    alert["url"] = ""
        
        if data.get("exchange_status"):
            for ex, info in data["exchange_status"].items():
                if is_generic_url(info.get("url", "")):
                    info["url"] = ""
        
        data["date"] = today
        data["collected_at"] = datetime.now().isoformat()
        return data
    except Exception as e:
        print(f"解析错误: {e}")
        return {
            "date": today,
            "collected_at": datetime.now().isoformat(),
            "error": str(e),
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

def generate_briefing():
    """生成每日简报主流程"""
    print("🚀 CEX 每日简报生成器（中文版 - 改进URL质量）")
    print("=" * 50)
    
    # 采集今日情报
    data = collect_daily_intel()
    
    # 保存
    save_intel(data)
    
    # 输出摘要
    print("\n" + "=" * 50)
    print("✅ 简报生成完成")
    print(f"📅 日期: {data['date']}")
    print(f"📊 警报数: {len(data.get('alerts', []))}")
    
    # 统计有URL的警报
    alerts_with_url = [a for a in data.get('alerts', []) if a.get('url')]
    print(f"🔗 有来源链接: {len(alerts_with_url)}")
    
    return data

if __name__ == "__main__":
    data = generate_briefing()
