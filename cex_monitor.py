#!/usr/bin/env python3
"""
CEX 每日情报监控系统
- 采集主流交易所情报
- 与昨日数据比对
- 生成变更简报
"""

import os
import json
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Set
from dataclasses import dataclass, asdict, field


@dataclass
class IntelItem:
    """情报条目"""
    source: str  # x, web, fintelegram
    exchange: str
    title: str
    content: str
    url: str = ""
    timestamp: str = ""
    severity: str = "low"  # critical, high, medium, low
    category: str = ""  # security, regulatory, service, scam, announcement


@dataclass
class DailyIntel:
    """每日情报汇总"""
    date: str
    collected_at: str
    exchanges: List[str]
    items: List[IntelItem]
    summary: str = ""


class CEXMonitor:
    """CEX 情报监控器"""
    
    TARGET_EXCHANGES = ["Binance", "OKX", "Coinbase", "Bybit", "Bitget", "Kraken", "KuCoin", "Gate.io", "MEXC"]
    DATA_DIR = Path("/Users/neo/.openclaw/workspace-cex-intelligence/data/intelligence")
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("XAI_API_KEY")
        self.model = "grok-4-1-fast-reasoning"
        self.today = datetime.now().strftime("%Y-%m-%d")
        self.yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        
    def _call_grok(self, prompt: str, tools: List[Dict]) -> Dict:
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
            "-d", json.dumps(data, ensure_ascii=False)
        ]
        
        try:
            result = subprocess.run(curl_cmd, capture_output=True, text=True, timeout=90)
            return json.loads(result.stdout) if result.returncode == 0 else {"error": result.stderr}
        except Exception as e:
            return {"error": str(e)}
    
    def _extract_text(self, response: Dict) -> str:
        """从响应中提取文本"""
        try:
            for item in response.get("output", []):
                if item.get("type") == "message" or item.get("role") == "assistant":
                    for content in item.get("content", []):
                        if content.get("type") in ["text", "output_text"]:
                            return content.get("text", "")
        except:
            pass
        return ""
    
    def collect_exchange_intel(self, exchange: str) -> List[IntelItem]:
        """采集单个交易所情报"""
        items = []
        
        # X社区搜索
        x_prompt = f"""Search X (Twitter) for posts about {exchange} exchange from the last 24 hours.
Focus ONLY on: security incidents, withdrawal problems, account freezes, scams, regulatory actions, or major announcements.

Return JSON array:
[
  {{
    "title": "brief title",
    "content": "detailed content",
    "author": "username",
    "severity": "high|medium|low",
    "category": "security|regulatory|service|scam|announcement"
  }}
]
Return [] if nothing relevant found."""
        
        x_response = self._call_grok(x_prompt, [{"type": "x_search"}])
        x_text = self._extract_text(x_response)
        
        try:
            x_data = json.loads(x_text) if x_text else []
            for post in x_data:
                items.append(IntelItem(
                    source="x",
                    exchange=exchange,
                    title=post.get("title", ""),
                    content=f"@{post.get('author', 'unknown')}: {post.get('content', '')}",
                    severity=post.get("severity", "low"),
                    category=post.get("category", "")
                ))
        except:
            pass
        
        # Web搜索
        web_prompt = f"""Search web for news about {exchange} cryptocurrency exchange from the last 24-48 hours.
Focus ONLY on: security incidents, regulatory actions, service outages, or major announcements.

Return JSON array:
[
  {{
    "title": "article title",
    "content": "brief summary",
    "source": "source name",
    "url": "url if available",
    "severity": "high|medium|low",
    "category": "security|regulatory|service|announcement"
  }}
]
Return [] if nothing relevant found."""
        
        web_response = self._call_grok(web_prompt, [{"type": "web_search"}])
        web_text = self._extract_text(web_response)
        
        try:
            web_data = json.loads(web_text) if web_text else []
            for article in web_data:
                items.append(IntelItem(
                    source="web",
                    exchange=exchange,
                    title=article.get("title", ""),
                    content=article.get("content", ""),
                    url=article.get("url", ""),
                    severity=article.get("severity", "low"),
                    category=article.get("category", "")
                ))
        except:
            pass
        
        return items
    
    def collect_fintelegram(self) -> List[IntelItem]:
        """采集 FinTelegram 情报"""
        prompt = """Search FinTelegram.com and related crypto scam monitoring sources for recent articles exposing exchange issues or warnings.

Return JSON array:
[
  {
    "title": "article title",
    "content": "key findings",
    "exchange": "target exchange name",
    "severity": "high|medium|low",
    "url": "url"
  }
]
Return [] if nothing found."""
        
        response = self._call_grok(prompt, [{"type": "web_search"}])
        text = self._extract_text(response)
        
        items = []
        try:
            data = json.loads(text) if text else []
            for article in data:
                items.append(IntelItem(
                    source="fintelegram",
                    exchange=article.get("exchange", "General"),
                    title=article.get("title", ""),
                    content=article.get("content", ""),
                    url=article.get("url", ""),
                    severity=article.get("severity", "medium"),
                    category="scam"
                ))
        except:
            pass
        
        return items
    
    def run_collection(self) -> DailyIntel:
        """执行完整采集"""
        print(f"🎯 CEX 情报采集 | {self.today}")
        print("=" * 60)
        
        all_items = []
        
        # 采集各交易所
        for exchange in self.TARGET_EXCHANGES:
            print(f"🔍 采集 {exchange}...")
            items = self.collect_exchange_intel(exchange)
            all_items.extend(items)
            print(f"   发现 {len(items)} 条情报")
        
        # 采集 FinTelegram
        print("🔍 采集 FinTelegram...")
        ft_items = self.collect_fintelegram()
        all_items.extend(ft_items)
        print(f"   发现 {len(ft_items)} 条情报")
        
        # 生成摘要
        critical = len([i for i in all_items if i.severity == "critical"])
        high = len([i for i in all_items if i.severity == "high"])
        medium = len([i for i in all_items if i.severity == "medium"])
        
        summary = f"总计 {len(all_items)} 条情报 | 严重:{critical} 高:{high} 中:{medium}"
        
        intel = DailyIntel(
            date=self.today,
            collected_at=datetime.now().isoformat(),
            exchanges=self.TARGET_EXCHANGES,
            items=all_items,
            summary=summary
        )
        
        print(f"\n📊 {summary}")
        return intel
    
    def save_intel(self, intel: DailyIntel):
        """保存情报到本地"""
        self.DATA_DIR.mkdir(parents=True, exist_ok=True)
        
        filepath = self.DATA_DIR / f"{intel.date}.json"
        
        # 转换为可序列化格式
        data = {
            "date": intel.date,
            "collected_at": intel.collected_at,
            "exchanges": intel.exchanges,
            "items": [asdict(item) for item in intel.items],
            "summary": intel.summary
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"💾 已保存: {filepath}")
        return filepath
    
    def load_intel(self, date: str) -> Optional[DailyIntel]:
        """加载指定日期的情报"""
        filepath = self.DATA_DIR / f"{date}.json"
        
        if not filepath.exists():
            return None
        
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        items = [IntelItem(**item) for item in data.get("items", [])]
        
        return DailyIntel(
            date=data["date"],
            collected_at=data["collected_at"],
            exchanges=data["exchanges"],
            items=items,
            summary=data.get("summary", "")
        )
    
    def compare_with_yesterday(self, today_intel: DailyIntel) -> Dict:
        """与昨日数据比对，找出新增内容"""
        yesterday_intel = self.load_intel(self.yesterday)
        
        if not yesterday_intel:
            print(f"⚠️ 未找到昨日数据 ({self.yesterday})，全部视为新增")
            return {
                "new_items": today_intel.items,
                "resolved_items": [],
                "changes": [],
                "is_first_run": True
            }
        
        # 获取昨日内容指纹（标题+内容前50字符）
        yesterday_fingerprints = set()
        for item in yesterday_intel.items:
            fp = f"{item.exchange}:{item.title}:{item.content[:50]}"
            yesterday_fingerprints.add(fp)
        
        # 找出新增
        new_items = []
        for item in today_intel.items:
            fp = f"{item.exchange}:{item.title}:{item.content[:50]}"
            if fp not in yesterday_fingerprints:
                new_items.append(item)
        
        # 找出可能已解决的（昨日有，今日无）
        today_fingerprints = set()
        for item in today_intel.items:
            fp = f"{item.exchange}:{item.title}:{item.content[:50]}"
            today_fingerprints.add(fp)
        
        resolved_items = []
        for item in yesterday_intel.items:
            fp = f"{item.exchange}:{item.title}:{item.content[:50]}"
            if fp not in today_fingerprints:
                resolved_items.append(item)
        
        return {
            "new_items": new_items,
            "resolved_items": resolved_items,
            "changes": [],
            "is_first_run": False
        }
    
    def generate_briefing(self, today_intel: DailyIntel, comparison: Dict) -> str:
        """生成简报"""
        lines = []
        lines.append("=" * 60)
        lines.append("🎯 CEX 情报每日简报")
        lines.append(f"📅 {self.today}")
        lines.append(f"⏰ 采集时间: {today_intel.collected_at[:19]}")
        lines.append("=" * 60)
        
        # 关键警报
        critical_items = [i for i in today_intel.items if i.severity == "critical"]
        high_items = [i for i in today_intel.items if i.severity == "high"]
        
        if critical_items or high_items:
            lines.append("\n🚨 重要警报")
            for item in critical_items:
                lines.append(f"   🔴 [{item.exchange}] {item.title}")
                lines.append(f"      {item.content[:100]}...")
            for item in high_items[:3]:  # 最多显示3个高优先级
                lines.append(f"   🟠 [{item.exchange}] {item.title}")
        
        # 新增情报
        new_items = comparison.get("new_items", [])
        if new_items:
            lines.append(f"\n📈 今日新增 ({len(new_items)} 条)")
            
            # 按交易所分组
            by_exchange = {}
            for item in new_items:
                by_exchange.setdefault(item.exchange, []).append(item)
            
            for exchange, items in by_exchange.items():
                lines.append(f"\n   🏢 {exchange} ({len(items)} 条)")
                for item in items[:3]:  # 每个交易所最多3条
                    emoji = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}.get(item.severity, "⚪")
                    lines.append(f"      {emoji} [{item.category or 'general'}] {item.title}")
                    if item.content:
                        lines.append(f"         {item.content[:80]}...")
        else:
            lines.append("\n📈 今日新增: 无重大新情报")
        
        # 各交易所状态概览
        lines.append("\n📊 交易所状态概览")
        for exchange in self.TARGET_EXCHANGES[:6]:  # 前6个主要交易所
            ex_items = [i for i in today_intel.items if i.exchange == exchange]
            if not ex_items:
                lines.append(f"   ✅ {exchange}: 正常")
            else:
                max_severity = max([{"low": 1, "medium": 2, "high": 3, "critical": 4}.get(i.severity, 0) for i in ex_items])
                status = {4: "🔴", 3: "🟠", 2: "🟡", 1: "🟢"}.get(max_severity, "✅")
                lines.append(f"   {status} {exchange}: {len(ex_items)} 条情报")
        
        # FinTelegram
        ft_items = [i for i in today_intel.items if i.source == "fintelegram"]
        if ft_items:
            lines.append(f"\n🔍 FinTelegram: {len(ft_items)} 篇相关文章")
        
        lines.append("\n" + "=" * 60)
        lines.append("💡 提示: 使用 /intel history 查看历史数据")
        lines.append("=" * 60)
        
        return "\n".join(lines)
    
    def run(self) -> str:
        """执行完整监控流程"""
        print("🚀 启动 CEX 每日监控...\n")
        
        # 1. 采集今日情报
        today_intel = self.run_collection()
        
        # 2. 保存到本地
        self.save_intel(today_intel)
        
        # 3. 与昨日比对
        comparison = self.compare_with_yesterday(today_intel)
        print(f"\n📊 比对结果: 新增 {len(comparison['new_items'])} 条")
        
        # 4. 生成简报
        briefing = self.generate_briefing(today_intel, comparison)
        
        return briefing


def main():
    """主入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description="CEX Daily Monitor")
    parser.add_argument("--run", action="store_true", help="执行完整监控流程")
    parser.add_argument("--collect-only", action="store_true", help="仅采集数据")
    parser.add_argument("--history", action="store_true", help="查看历史数据")
    parser.add_argument("--date", help="查看指定日期数据 (YYYY-MM-DD)")
    
    args = parser.parse_args()
    
    monitor = CEXMonitor()
    
    if args.run:
        briefing = monitor.run()
        print("\n" + briefing)
    elif args.collect_only:
        intel = monitor.run_collection()
        monitor.save_intel(intel)
    elif args.history:
        # 列出最近7天的数据
        print("📚 最近7天数据:")
        for i in range(7):
            date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            filepath = monitor.DATA_DIR / f"{date}.json"
            status = "✅" if filepath.exists() else "❌"
            print(f"   {status} {date}")
    elif args.date:
        intel = monitor.load_intel(args.date)
        if intel:
            print(f"📅 {args.date} 数据:")
            print(f"   采集时间: {intel.collected_at}")
            print(f"   情报数量: {len(intel.items)}")
            print(f"   摘要: {intel.summary}")
            for item in intel.items[:10]:
                print(f"   - [{item.exchange}] {item.title}")
        else:
            print(f"❌ 未找到 {args.date} 的数据")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
