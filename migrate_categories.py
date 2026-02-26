#!/usr/bin/env python3
"""
数据迁移脚本 - 为历史数据添加 category 字段
"""

import json
from pathlib import Path

# 关键词映射
category_keywords = {
    'security_attack': [
        'hack', 'hacked', 'breach', 'exploit', 'stolen', 'drain', 'theft',
        'ddos', 'ransomware', 'malware', 'phishing',
        'vulnerability', 'bug', 'glitch', 'exploit',
        'unauthorized access', 'private key', 'wallet compromised',
        '黑客', '被盗', '漏洞', '攻击'
    ],
    'operational_risk': [
        'ceo arrested', 'founder detained', 'executive arrested',
        'bankruptcy', 'insolvency', 'liquidation',
        'withdrawal suspended', 'liquidity crisis', 'run on',
        'massive layoff', 'office closed', 'shutdown',
        'system down', 'maintenance', 'outage',
        '创始人被捕', '破产', '挤兑', '裁员', '跑路'
    ],
    'dispute_compliance': [
        'regulatory', 'compliance', 'fine', 'penalty', 'sanction',
        'license revoked', 'suspended', 'banned', 'blacklist',
        'aml', 'kyc', 'money laundering',
        'frozen', 'seized', 'confiscated',
        'lawsuit', 'legal action', 'investigation',
        'user complaint', 'controversy', 'fud',
        '牌照', '监管', '冻结', '合规', '诉讼', '争议'
    ]
}

def classify_alert(alert):
    """根据标题和描述自动分类"""
    text = (alert.get('title', '') + ' ' + alert.get('description', '')).lower()
    
    for category, keywords in category_keywords.items():
        for keyword in keywords:
            if keyword.lower() in text:
                return category
    
    # 默认为合规争议
    return 'dispute_compliance'

def migrate_data():
    """迁移数据文件"""
    data_dir = Path(__file__).parent / "web" / "data" / "intelligence"
    
    for json_file in data_dir.glob("*.json"):
        if json_file.stem.startswith('historical'):
            continue
            
        print(f"处理: {json_file.name}")
        
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 为每个警报添加分类
        if 'alerts' in data:
            for alert in data['alerts']:
                if 'category' not in alert:
                    alert['category'] = classify_alert(alert)
                # 添加子分类（简化版）
                if 'subcategory' not in alert:
                    alert['subcategory'] = ''
        
        # 保存
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"  ✓ 已更新 {len(data.get('alerts', []))} 条警报")

if __name__ == "__main__":
    migrate_data()
    print("\n✅ 数据迁移完成！")
