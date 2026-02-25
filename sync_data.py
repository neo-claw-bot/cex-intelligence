#!/usr/bin/env python3
"""
数据同步脚本
将采集的数据同步到网站目录
"""

import json
import shutil
from datetime import datetime
from pathlib import Path

def sync_data():
    """同步数据到网站目录"""
    
    # 源数据目录 (根目录)
    source_dir = Path(__file__).parent / "data"
    
    # 目标目录 (web应用)
    web_data_dir = Path(__file__).parent / "web" / "data" / "intelligence"
    web_data_dir.mkdir(parents=True, exist_ok=True)
    
    # 找到最新的数据文件
    files = sorted(source_dir.glob("daily_*.json"))
    if not files:
        print("❌ 无数据文件")
        return False
    
    latest = files[-1]
    print(f"📂 读取源数据: {latest}")
    
    # 读取并转换格式
    with open(latest, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 生成日期格式的文件名 (YYYY-MM-DD.json)
    today = datetime.now().strftime("%Y-%m-%d")
    target_file = web_data_dir / f"{today}.json"
    
    # 转换数据格式以适应网站模板
    exchanges_list = []
    for e in data.get("exchanges", []):
        # 构建警报列表
        alerts = []
        if e.get("fintelegram_reports"):
            for report in e.get("fintelegram_reports"):
                alerts.append({
                    "type": "fintelegram",
                    "title": report,
                    "severity": "high",
                    "description": report,
                    "source": "FinTelegram"
                })
        
        exchange_data = {
            "name": e.get("exchange"),
            "status": "warning" if e.get("alert_level") in ["high", "critical"] else "normal",
            "severity": e.get("alert_level", "none"),
            "alerts_count": len(alerts),
            "alerts": alerts,
            "twitter_sentiment": "neutral",
            "news_count": len(e.get("web_articles", [])),
            "sources": ["FinTelegram"] if alerts else []
        }
        exchanges_list.append(exchange_data)
    
    # 构建关键警报列表（用于网站模板显示）
    alerts_list = []
    for e in data.get("exchanges", []):
        if e.get("alert_level") in ["high", "critical"]:
            # 处理 FinTelegram 报告（可能是字符串或字典）
            reports = e.get("fintelegram_reports", [])
            urls = []
            descriptions = []
            
            for r in reports:
                if isinstance(r, dict):
                    descriptions.append(f"{r.get('date', '')}: {r.get('title', '')}")
                    if r.get('url'):
                        urls.append(r.get('url'))
                else:
                    descriptions.append(r)
            
            # 默认URL列表（如果reports中没有URL）
            if not urls:
                urls = ["https://fintelegram.com"]
            
            # 构建警报详情
            alert_info = {
                "exchange": e.get("exchange"),
                "severity": e.get("alert_level"),
                "title": f"{e.get('exchange')} - {e.get('alert_level').upper()} 风险警报",
                "description": "; ".join(descriptions) if descriptions else "发现风险信号",
                "source": "FinTelegram" if reports else "Monitor",
                "url": urls[0] if urls else "https://fintelegram.com",  # 主URL
                "urls": urls,  # 所有URL列表
                "tags": ["security"] if reports else []
            }
            alerts_list.append(alert_info)
    
    # 转换数据格式以适应网站
    web_data = {
        "date": today,
        "timestamp": data.get("timestamp", ""),
        "collected_at": data.get("timestamp", ""),  # 模板使用这个字段
        "summary": {
            "total_exchanges": len(data.get("exchanges", [])),
            "alerted_exchanges": len([e for e in data.get("exchanges", []) if e.get("alert_level") != "none"]),
            "critical_alerts": len([e for e in data.get("exchanges", []) if e.get("alert_level") == "critical"]),
            "high_alerts": len([e for e in data.get("exchanges", []) if e.get("alert_level") == "high"])
        },
        "exchanges": data.get("exchanges", []),
        "exchanges_list": exchanges_list,  # 模板使用这个格式
        "key_alerts": alerts_list,  # 关键警报
        "alerts": alerts_list  # 网站模板使用这个字段显示警报
    }
    
    # 保存到网站目录
    with open(target_file, 'w', encoding='utf-8') as f:
        json.dump(web_data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 数据已同步: {latest} → {target_file}")
    
    # 同时复制到 site/ 目录用于静态访问
    site_data_dir = Path(__file__).parent / "site"
    site_data_dir.mkdir(exist_ok=True)
    
    # 生成网站专用数据文件
    with open(site_data_dir / "latest.json", 'w', encoding='utf-8') as f:
        json.dump(web_data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 静态数据已更新: site/latest.json")
    
    return True

if __name__ == "__main__":
    sync_data()
