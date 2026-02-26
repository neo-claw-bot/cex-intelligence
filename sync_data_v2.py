#!/usr/bin/env python3
"""
数据同步脚本 v2
处理带分类的新数据结构
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
    
    # 找到最新的数据文件（只读 daily_*.json）
    files = sorted(source_dir.glob("daily_*.json"))
    if not files:
        print("❌ 无数据文件")
        return False
    
    latest = files[-1]
    print(f"📂 读取源数据: {latest}")
    
    # 读取数据
    with open(latest, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 生成日期格式的文件名
    today = datetime.now().strftime("%Y-%m-%d")
    target_file = web_data_dir / f"{today}.json"
    
    # 处理警报数据，确保每个都有 category
    all_alerts = data.get('all_alerts', data.get('alerts', []))
    
    # 为没有 category 的警报添加默认值
    for alert in all_alerts:
        if 'category' not in alert:
            # 基于关键词简单分类
            title_desc = (alert.get('title', '') + ' ' + alert.get('description', '')).lower()
            if any(k in title_desc for k in ['hack', 'stolen', 'breach', 'ddos', '漏洞', '攻击']):
                alert['category'] = 'security_attack'
            elif any(k in title_desc for k in ['破产', '被捕', '挤兑', '宕机']):
                alert['category'] = 'operational_risk'
            else:
                alert['category'] = 'dispute_compliance'
        
        # 确保有 discovered_at
        if 'discovered_at' not in alert:
            alert['discovered_at'] = data.get('timestamp', datetime.now().isoformat())
    
    # 按分类统计
    categories = {
        'security_attack': [],
        'dispute_compliance': [],
        'operational_risk': []
    }
    
    for alert in all_alerts:
        cat = alert.get('category', 'dispute_compliance')
        if cat in categories:
            categories[cat].append(alert)
    
    # 构建 web 数据格式
    web_data = {
        'date': today,
        'timestamp': data.get('timestamp', datetime.now().isoformat()),
        'collected_at': data.get('timestamp', datetime.now().isoformat()),
        'discovered_at': datetime.now().isoformat(),
        'summary': {
            'total_exchanges': 30,
            'total_alerts': len(all_alerts),
            'alerted_exchanges': len(set(a.get('exchange') for a in all_alerts)),
            'critical_alerts': len([a for a in all_alerts if a.get('severity') == 'critical']),
            'high_alerts': len([a for a in all_alerts if a.get('severity') == 'high'])
        },
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
        'alerts': all_alerts,
        'key_alerts': all_alerts,  # 兼容旧模板
        'exchanges': data.get('exchanges', [])
    }
    
    # 保存到网站目录
    with open(target_file, 'w', encoding='utf-8') as f:
        json.dump(web_data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 数据已同步: {latest} → {target_file}")
    print(f"📊 统计:")
    print(f"   总警报: {len(all_alerts)}")
    print(f"   🔴 攻击事件: {len(categories['security_attack'])}")
    print(f"   🟠 合规争议: {len(categories['dispute_compliance'])}")
    print(f"   🟡 运营风险: {len(categories['operational_risk'])}")
    
    # 同时复制到 site/ 目录
    site_data_dir = Path(__file__).parent / "site"
    site_data_dir.mkdir(exist_ok=True)
    
    with open(site_data_dir / "latest.json", 'w', encoding='utf-8') as f:
        json.dump(web_data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 静态数据已更新: site/latest.json")
    
    # 生成简报文本
    generate_briefing(web_data, site_data_dir)
    
    return True


def generate_briefing(data: dict, output_dir: Path):
    """生成简报文本"""
    
    summary = data.get('summary', {})
    categories = data.get('categories', {})
    
    briefing = f"""🎯 CEX 每日简报 - {data.get('date', datetime.now().strftime('%Y-%m-%d'))}

📊 今日概况
• 监控交易所: {summary.get('total_exchanges', 30)} 个
• 风险交易所: {summary.get('alerted_exchanges', 0)} 个
• 总情报数: {summary.get('total_alerts', 0)} 条

📈 分类统计
• 🔴 网络攻击事件: {categories.get('security_attack', {}).get('count', 0)} 条
• 🟠 合规争议问题: {categories.get('dispute_compliance', {}).get('count', 0)} 条
• 🟡 运营风险事件: {categories.get('operational_risk', {}).get('count', 0)} 条

"""
    
    # 添加关键警报
    alerts = data.get('alerts', [])
    critical_high = [a for a in alerts if a.get('severity') in ['critical', 'high']]
    
    if critical_high:
        briefing += "🚨 重点关注\n"
        for alert in critical_high[:5]:
            cat_emoji = {
                'security_attack': '🔴',
                'dispute_compliance': '🟠',
                'operational_risk': '🟡'
            }.get(alert.get('category'), '⚪')
            briefing += f"{cat_emoji} [{alert.get('exchange')}] {alert.get('title', '')}\n"
    else:
        briefing += "✅ 今日无重大风险事件\n"
    
    briefing += f"""
⏰ 生成时间: {data.get('timestamp', datetime.now().isoformat())}
🔗 详细报告: https://cex-intelligence-production.up.railway.app
"""
    
    with open(output_dir / "briefing.txt", 'w', encoding='utf-8') as f:
        f.write(briefing)
    
    print(f"✅ 简报已生成: site/briefing.txt")


if __name__ == "__main__":
    sync_data()
