#!/usr/bin/env python3
"""
Grok CEX 情报采集器 v2.1
支持自动情报分类：攻击、合规、运营
"""

import os
import json
import subprocess
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class IntelligenceAlert:
    """情报警报对象"""
    exchange: str
    category: str  # security_attack, dispute_compliance, operational_risk
    subcategory: str
    severity: str  # critical, high, medium, low
    title: str
    description: str
    event_date: str
    source: str
    url: str = ""
    discovered_at: str = ""


class GrokCEXCollectorV2:
    """Grok CEX 情报采集器 v2 - 支持自动分类"""
    
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
            "tools": [{"type": t} for t in tools]
        }
        
        curl_cmd = [
            "curl", "-s", "https://api.x.ai/v1/responses",
            "-H", "Content-Type: application/json",
            "-H", f"Authorization: Bearer {self.api_key}",
            "-d", json.dumps(data, ensure_ascii=False)
        ]
        
        try:
            result = subprocess.run(curl_cmd, capture_output=True, text=True, timeout=60)
            return json.loads(result.stdout) if result.returncode == 0 else {"error": result.stderr}
        except Exception as e:
            return {"error": str(e)}
    
    def _extract_content(self, response: Dict) -> str:
        """从响应中提取文本"""
        try:
            for item in response.get("output", []):
                if item.get("role") == "assistant":
                    for part in item.get("content", []):
                        if part.get("type") == "text":
                            return part.get("text", "")
        except:
            pass
        return ""
    
    def search_exchange_intelligence(self, exchange: str) -> List[IntelligenceAlert]:
        """
        搜索指定交易所的情报，自动分类
        
        分类标准：
        - security_attack: 黑客攻击、资金被盗、系统入侵、DDoS、漏洞
        - dispute_compliance: 监管处罚、牌照问题、用户资产冻结、合规违规、舆论争议
        - operational_risk: 管理层被捕、流动性危机、系统宕机、破产风险
        """
        prompt = f"""Search for recent news and discussions about {exchange} cryptocurrency exchange in the last 48 hours.

Categorize each finding into one of these three categories:

1. **security_attack** - Cyber attacks and security breaches:
   - Exchange hacked, funds stolen
   - Wallet compromised (hot/cold)
   - DDoS attacks causing downtime
   - API vulnerabilities exploited
   - Smart contract bugs
   - Key phrases: hack, breach, exploit, stolen, drain, DDoS, vulnerability

2. **dispute_compliance** - Regulatory and compliance issues:
   - License revoked or suspended by regulators
   - Fined by regulatory authorities
   - User assets frozen or withdrawal blocked
   - AML/KYC violations
   - Money laundering allegations
   - Mass user complaints
   - Key phrases: regulatory, compliance, license, frozen, seized, AML, investigation, lawsuit

3. **operational_risk** - Operational and management risks:
   - CEO/founder arrested
   - Liquidity crisis or bank run
   - Extended system outage (>2 hours)
   - Bankruptcy or insolvency rumors
   - Massive layoffs
   - Key phrases: arrested, bankruptcy, liquidity, outage, downtime, insolvency

For each finding, return a JSON object with:
- category: "security_attack", "dispute_compliance", or "operational_risk"
- subcategory: specific type (e.g., "fund_theft", "regulatory_action", "leadership_crisis")
- severity: "critical", "high", "medium", or "low"
- title: brief headline (max 50 chars)
- description: detailed description (100-200 chars)
- event_date: when the event occurred (YYYY-MM-DD format, or approximate)
- source: news source name
- url: source URL if available

Return as a JSON array. If no intelligence found, return empty array [].

Be objective and factual. Do not speculate or add information not in the sources."""

        response = self._call_grok(prompt, ["web_search", "x_search"])
        text = self._extract_content(response)
        
        alerts = []
        discovered_at = datetime.now().isoformat()
        
        try:
            data = json.loads(text)
            if isinstance(data, list):
                for item in data:
                    alert = IntelligenceAlert(
                        exchange=exchange,
                        category=item.get('category', 'dispute_compliance'),
                        subcategory=item.get('subcategory', ''),
                        severity=item.get('severity', 'medium'),
                        title=item.get('title', ''),
                        description=item.get('description', ''),
                        event_date=item.get('event_date', datetime.now().strftime('%Y-%m-%d')),
                        source=item.get('source', 'Unknown'),
                        url=item.get('url', ''),
                        discovered_at=discovered_at
                    )
                    alerts.append(alert)
        except json.JSONDecodeError:
            # 如果解析失败，尝试从文本中提取
            print(f"⚠️ JSON解析失败 ({exchange}), 尝试文本提取")
        
        return alerts
    
    def check_fintelegram(self) -> List[IntelligenceAlert]:
        """检查 FinTelegram 的曝光信息"""
        prompt = """Search FinTelegram.com for recent articles exposing cryptocurrency exchange scams, hacks, or investigations.

FinTelegram focuses on:
- Exchange scams and frauds
- Regulatory warnings
- Security incidents
- Compliance violations

Categorize findings into:
- security_attack: if about hacks or security breaches
- dispute_compliance: if about regulatory issues or user complaints
- operational_risk: if about bankruptcy or leadership issues

Return as JSON array with fields: category, subcategory, severity, title, description, event_date, exchange_targeted, source, url."""

        response = self._call_grok(prompt, ["web_search"])
        text = self._extract_content(response)
        
        alerts = []
        discovered_at = datetime.now().isoformat()
        
        try:
            data = json.loads(text)
            if isinstance(data, list):
                for item in data:
                    exchange = item.get('exchange_targeted', item.get('exchange', 'Unknown'))
                    alert = IntelligenceAlert(
                        exchange=exchange,
                        category=item.get('category', 'dispute_compliance'),
                        subcategory=item.get('subcategory', 'fintelegram_report'),
                        severity=item.get('severity', 'high'),
                        title=item.get('title', ''),
                        description=item.get('summary', item.get('description', '')),
                        event_date=item.get('date', item.get('event_date', datetime.now().strftime('%Y-%m-%d'))),
                        source='FinTelegram',
                        url=item.get('url', 'https://fintelegram.com'),
                        discovered_at=discovered_at
                    )
                    alerts.append(alert)
        except:
            pass
        
        return alerts
    
    def collect_all(self, focus: str = "all") -> Dict:
        """
        执行完整采集
        
        Returns:
            {
                "timestamp": str,
                "total_alerts": int,
                "categories": {
                    "security_attack": {"count": int, "alerts": [...]},
                    "dispute_compliance": {"count": int, "alerts": [...]},
                    "operational_risk": {"count": int, "alerts": [...]}
                },
                "all_alerts": [...]
            }
        """
        all_alerts = []
        
        # 确定监控范围
        if focus == "all":
            exchanges = self.EXCHANGES
        elif focus == "tier1":
            exchanges = self.EXCHANGES[:10]
        else:
            exchanges = [focus]
        
        print(f"🎯 开始采集 {len(exchanges)} 个交易所情报...")
        print("=" * 60)
        
        # 采集各交易所情报
        for exchange in exchanges:
            print(f"\n🔍 采集 {exchange}...")
            alerts = self.search_exchange_intelligence(exchange)
            all_alerts.extend(alerts)
            print(f"   ✅ 发现 {len(alerts)} 条情报")
            for alert in alerts:
                print(f"      [{alert.category}] {alert.severity}: {alert.title[:50]}...")
        
        # 检查 FinTelegram
        print("\n🔍 检查 FinTelegram 曝光...")
        ft_alerts = self.check_fintelegram()
        # 去重：避免与已采集的重复
        existing_exchanges = {a.exchange for a in all_alerts}
        for alert in ft_alerts:
            if alert.exchange not in existing_exchanges:
                all_alerts.append(alert)
        print(f"   ✅ FinTelegram 新增 {len([a for a in ft_alerts if a.exchange not in existing_exchanges])} 条")
        
        # 按分类统计
        categories = {
            'security_attack': [],
            'dispute_compliance': [],
            'operational_risk': []
        }
        
        for alert in all_alerts:
            cat = alert.category
            if cat in categories:
                categories[cat].append(asdict(alert))
            else:
                # 默认为合规争议
                categories['dispute_compliance'].append(asdict(alert))
        
        result = {
            'timestamp': datetime.now().isoformat(),
            'model': self.model,
            'focus': focus,
            'total_alerts': len(all_alerts),
            'exchanges_monitored': len(exchanges),
            'categories': {
                'security_attack': {
                    'count': len(categories['security_attack']),
                    'alerts': categories['security_attack']
                },
                'dispute_compliance': {
                    'count': len(categories['dispute_compliance']),
                    'alerts': categories['dispute_compliance']
                },
                'operational_risk': {
                    'count': len(categories['operational_risk']),
                    'alerts': categories['operational_risk']
                }
            },
            'all_alerts': [asdict(a) for a in all_alerts]
        }
        
        print("\n" + "=" * 60)
        print("📊 采集完成:")
        print(f"   总情报: {len(all_alerts)} 条")
        print(f"   🔴 攻击事件: {len(categories['security_attack'])} 条")
        print(f"   🟠 合规争议: {len(categories['dispute_compliance'])} 条")
        print(f"   🟡 运营风险: {len(categories['operational_risk'])} 条")
        
        return result


def main():
    """CLI 入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Grok CEX Intelligence Collector v2")
    parser.add_argument("--focus", default="all", help="监控范围: all/tier1/具体交易所")
    parser.add_argument("--output", "-o", help="输出 JSON 文件路径")
    
    args = parser.parse_args()
    
    collector = GrokCEXCollectorV2()
    result = collector.collect_all(focus=args.focus)
    
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"\n✅ 结果已保存: {args.output}")
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
