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
    
    # 读取并转换格式
    with open(latest, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 生成日期格式的文件名 (YYYY-MM-DD.json)
    today = datetime.now().strftime("%Y-%m-%d")
    target_file = web_data_dir / f"{today}.json"
    
    # 转换数据格式以适应网站
    web_data = {
        "date": today,
        "timestamp": data.get("timestamp", ""),
        "summary": {
            "total_exchanges": len(data.get("exchanges", [])),
            "alerted_exchanges": len([e for e in data.get("exchanges", []) if e.get("alert_level") != "none"]),
            "critical_alerts": len([e for e in data.get("exchanges", []) if e.get("alert_level") == "critical"]),
            "high_alerts": len([e for e in data.get("exchanges", []) if e.get("alert_level") == "high"])
        },
        "exchanges": data.get("exchanges", []),
        "key_alerts": data.get("key_alerts", [])
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
