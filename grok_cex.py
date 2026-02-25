#!/usr/bin/env python3
"""
Grok CEX 情报采集器 - 极简版
使用 xAI Responses API + curl
"""

import os
import json
import subprocess
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict


@dataclass
class XPost:
    author: str
    content: str
    sentiment: str
    significance: str


@dataclass
class WebArticle:
    title: str
    source: str
    category: str
    summary: str


@dataclass
class ExchangeIntel:
    exchange: str
    x_posts: List[XPost]
    web_articles: List[WebArticle]
    alert_level: str


class GrokCollector:
    """Grok 情报采集器"""
    
    # CER.live 所有监控的交易所 (30个)
    EXCHANGES = [
        "Binance", "MEXC", "Gate", "Bitget", "OKX", "HTX", "Bybit",
        "Coinbase Exchange", "CoinW", "BitMart", "Crypto.com", "DigiFinex",
        "LBank", "Upbit", "Toobit", "WEEX", "P2B", "XT.COM", "Tapbit",
        "Kraken", "KuCoin", "Bumba", "WhiteBIT", "Deribit", "OFZA",
        "Flipster", "BingX", "HashKey Exchange", "Nami.Exchange", "Bitstamp"
    ]
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("XAI_API_KEY")
        if not self.api_key:
            raise ValueError("需要 XAI_API_KEY")
        self.model = "grok-4-1-fast-reasoning"
    
    def _call_grok(self, prompt: str, tools: List[str]) -> Dict:
        """调用 Grok API"""
        data = {
            "model": self.model,
            "input": [{"role": "user", "content": prompt}],
            "tools": tools
        }
        
        curl_cmd = [
            "curl", "-s", "https://api.x.ai/v1/responses",
            "-H", "Content-Type: application/json",
            "-H", f"Authorization: Bearer {self.api_key}",
            "-d", json.dumps(data)
        ]
        
        try:
            result = subprocess.run(curl_cmd, capture_output=True, text=True, timeout=60)
            return json.loads(result.stdout) if result.returncode == 0 else {"error": result.stderr}
        except Exception as e:
            return {"error": str(e)}
    
    def search_x(self, exchange: str) -> List[XPost]:
        """搜索 X 社区"""
        prompt = f"""Search X (Twitter) for recent posts about {exchange} exchange in the last 24-48 hours.
Focus on: security issues, withdrawal problems, user complaints, or official announcements.

Return ONLY a JSON array like this:
[
  {{"author": "username", "content": "post summary", "sentiment": "negative", "significance": "withdrawal issues reported"}}
]
If no relevant posts found, return empty array []."""
        
        response = self._call_grok(prompt, ["x_search"])
        
        try:
            # 提取输出内容
            output = response.get("output", [])
            for item in output:
                if item.get("role") == "assistant":
                    content = item.get("content", [])
                    for part in content:
                        if part.get("type") == "text":
                            text = part.get("text", "[]")
                            data = json.loads(text)
                            return [XPost(**p) for p in data] if isinstance(data, list) else []
            return []
        except Exception as e:
            print(f"⚠️ X搜索解析失败 ({exchange}): {e}")
            return []
    
    def search_web(self, exchange: str) -> List[WebArticle]:
        """搜索网页新闻"""
        prompt = f"""Search web for recent news about {exchange} cryptocurrency exchange.
Focus on: security incidents, regulatory actions, service issues, or major announcements.

Return ONLY a JSON array like this:
[
  {{"title": "News Title", "source": "CoinDesk", "category": "security", "summary": "brief summary"}}
]
If no relevant news found, return empty array []."""
        
        response = self._call_grok(prompt, ["web_search"])
        
        try:
            output = response.get("output", [])
            for item in output:
                if item.get("role") == "assistant":
                    content = item.get("content", [])
                    for part in content:
                        if part.get("type") == "text":
                            text = part.get("text", "[]")
                            data = json.loads(text)
                            return [WebArticle(**a) for a in data] if isinstance(data, list) else []
            return []
        except Exception as e:
            print(f"⚠️ 网页搜索解析失败 ({exchange}): {e}")
            return []
    
    def check_fintelegram(self) -> List[Dict]:
        """检查 FinTelegram"""
        prompt = """Search FinTelegram.com for recent articles exposing cryptocurrency exchange scams or warnings.

Return ONLY a JSON array like this:
[
  {"title": "Article Title", "exchange": "Exchange Name", "severity": "high", "summary": "key findings"}
]
If no articles found, return empty array []."""
        
        response = self._call_grok(prompt, ["web_search"])
        
        try:
            output = response.get("output", [])
            for item in output:
                if item.get("role") == "assistant":
                    content = item.get("content", [])
                    for part in content:
                        if part.get("type") == "text":
                            return json.loads(part.get("text", "[]"))
            return []
        except:
            return []
    
    def analyze(self, exchange: str) -> ExchangeIntel:
        """分析单个交易所"""
        print(f"🔍 采集 {exchange}...")
        
        x_posts = self.search_x(exchange)
        web_articles = self.search_web(exchange)
        
        # 确定警报级别
        alert = "none"
        for p in x_posts:
            if "hack" in p.significance.lower() or "security" in p.significance.lower():
                alert = "critical"
                break
        if alert == "none" and any(a.category in ["security", "regulatory"] for a in web_articles):
            alert = "high"
        elif alert == "none" and len([p for p in x_posts if p.sentiment == "negative"]) >= 2:
            alert = "medium"
        elif x_posts or web_articles:
            alert = "low"
        
        return ExchangeIntel(exchange, x_posts, web_articles, alert)
    
    def run(self, focus: str = "all") -> Dict:
        """执行完整采集"""
        exchanges = self.EXCHANGES if focus == "all" else [focus]
        
        print(f"🎯 CEX 情报采集开始 | 模型: {self.model}")
        print("-" * 60)
        
        results = []
        for ex in exchanges:
            intel = self.analyze(ex)
            results.append(intel)
        
        # FinTelegram
        print("🔍 检查 FinTelegram...")
        ft_reports = self.check_fintelegram()
        
        # 关键警报
        alerts = []
        for r in results:
            if r.alert_level == "critical":
                alerts.append(f"🚨 {r.exchange}: 严重安全问题")
            elif r.alert_level == "high":
                alerts.append(f"⚠️ {r.exchange}: 高风险事件")
        
        return {
            "timestamp": datetime.now().isoformat(),
            "model": self.model,
            "focus": focus,
            "exchanges": [asdict(r) for r in results],
            "fintelegram": ft_reports,
            "alerts": alerts,
        }


def format_report(data: Dict) -> str:
    """格式化报告"""
    lines = []
    lines.append("=" * 60)
    lines.append("🎯 CEX 情报采集报告")
    lines.append(f"⏰ {data['timestamp']}")
    lines.append(f"🤖 {data['model']}")
    lines.append("=" * 60)
    
    if data["alerts"]:
        lines.append("\n🚨 关键警报")
        for a in data["alerts"]:
            lines.append(f"  {a}")
    
    for ex in data["exchanges"]:
        emoji = {"critical": "🚨", "high": "⚠️", "medium": "📊", "low": "📝", "none": "✅"}.get(ex["alert_level"], "⚪")
        lines.append(f"\n{emoji} {ex['exchange']}")
        
        if ex["x_posts"]:
            lines.append(f"  🐦 X社区: {len(ex['x_posts'])} 条")
            for p in ex["x_posts"][:2]:
                se = {"positive": "🟢", "negative": "🔴", "neutral": "⚪"}.get(p["sentiment"], "⚪")
                lines.append(f"    {se} @{p['author']}: {p['content'][:50]}...")
        
        if ex["web_articles"]:
            lines.append(f"  📰 新闻: {len(ex['web_articles'])} 篇")
            for a in ex["web_articles"][:2]:
                lines.append(f"    [{a['category']}] {a['title'][:45]}...")
    
    if data["fintelegram"]:
        lines.append(f"\n🔍 FinTelegram: {len(data['fintelegram'])} 篇")
    
    lines.append("\n" + "=" * 60)
    return "\n".join(lines)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Grok CEX Collector")
    parser.add_argument("--focus", default="all", help="all 或指定交易所")
    parser.add_argument("--output", "-o", help="输出 JSON 文件")
    parser.add_argument("--api-key", help="xAI API Key")
    
    args = parser.parse_args()
    
    collector = GrokCollector(api_key=args.api_key)
    result = collector.run(focus=args.focus)
    
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"\n✅ 已保存: {args.output}")
    
    print(format_report(result))
