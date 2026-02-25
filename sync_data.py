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
    
    # 使用独立的 key_alerts 作为警报列表（每个争议一个独立警报）
    key_alerts = data.get("key_alerts", [])
    
    # 为每个警报添加标签
    for alert in key_alerts:
        alert["tags"] = ["security", "fintelegram"]
        # 确保有 url 字段（兼容旧模板）
        if "url" not in alert and "urls" in alert:
            alert["url"] = alert["urls"][0] if alert["urls"] else "https://fintelegram.com"
    
    # 转换数据格式以适应网站
    web_data = {
        "date": today,
        "timestamp": data.get("timestamp", ""),
        "collected_at": data.get("timestamp", ""),
        "summary": {
            "total_exchanges": len(data.get("exchanges", [])),
            "alerted_exchanges": len([e for e in data.get("exchanges", []) if e.get("alert_level") != "none"]),
            "critical_alerts": len([a for a in key_alerts if a.get("severity") == "critical"]),
            "high_alerts": len([a for a in key_alerts if a.get("severity") == "high"])
        },
        "exchanges": data.get("exchanges", []),
        "key_alerts": key_alerts,  # 独立的警报列表
        "alerts": key_alerts  # 网站模板使用这个字段
    }
    
    # 保存到网站目录
    with open(target_file, 'w', encoding='utf-8') as f:
        json.dump(web_data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 数据已同步: {latest} → {target_file}")
    print(f"📊 独立警报数量: {len(key_alerts)}")
    
    # 同时复制到 site/ 目录
    site_data_dir = Path(__file__).parent / "site"
    site_data_dir.mkdir(exist_ok=True)
    
    with open(site_data_dir / "latest.json", 'w', encoding='utf-8') as f:
        json.dump(web_data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 静态数据已更新: site/latest.json")
    
    return True

if __name__ == "__main__":
    sync_data()
