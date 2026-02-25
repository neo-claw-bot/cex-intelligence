#!/usr/bin/env python3
"""
生成网站静态文件 + 今日简报
整合数据展示和简报内容
"""

import json
import shutil
from datetime import datetime
from pathlib import Path

# 读取最新数据
files = sorted(Path('data').glob('*.json'))
if not files:
    print('❌ 无数据文件')
    exit(1)

latest_file = files[-1]
with open(latest_file) as f:
    data = json.load(f)

# 创建 site 目录
Path('site').mkdir(exist_ok=True)

# 提取关键信息
timestamp = data.get('timestamp', 'N/A')
exchanges = data.get('exchanges', [])
key_alerts = data.get('key_alerts', [])
overall_summary = data.get('overall_summary', '')

# 统计信息
total_exchanges = len(exchanges)
alerted_exchanges = [e for e in exchanges if e.get('alert_level') != 'none']
critical_count = len([e for e in exchanges if e.get('alert_level') == 'critical'])
high_count = len([e for e in exchanges if e.get('alert_level') == 'high'])

# 生成简报内容
briefing_sections = []

# 1. 总体概况
briefing_sections.append(f"""
<div class="briefing-section">
<h2>📊 今日概况</h2>
<p><strong>监控时间:</strong> {timestamp}</p>
<p><strong>监控范围:</strong> {total_exchanges} 个交易所</p>
<p><strong>风险状况:</strong> {'🚨 发现 ' + str(len(key_alerts)) + ' 项警报' if key_alerts else '✅ 全部正常'}</p>
</div>
""")

# 2. 关键警报（如果有）
if key_alerts:
    alerts_html = "\n".join([f'<div class="alert-item">{alert}</div>' for alert in key_alerts])
    briefing_sections.append(f"""
<div class="briefing-section alert">
<h2>🚨 关键警报</h2>
{alerts_html}
</div>
""")

# 3. 交易所详情
exchange_cards = []
for e in exchanges:
    ex_name = e.get('exchange', 'Unknown')
    alert_level = e.get('alert_level', 'none')
    x_count = len(e.get('x_posts', []))
    web_count = len(e.get('web_articles', []))
    
    # X帖子详情
    x_posts_html = ""
    if e.get('x_posts'):
        x_posts_html = "<ul class='post-list'>" + "".join([
            f"<li><span class='sentiment {p.get('sentiment', 'neutral')}'>{p.get('sentiment', '⚪')}</span> @{p.get('author', '?')}: {p.get('content', '')[:80]}...</li>"
            for p in e.get('x_posts', [])[:3]
        ]) + "</ul>"
    
    # 新闻详情
    news_html = ""
    if e.get('web_articles'):
        news_html = "<ul class='news-list'>" + "".join([
            f"<li>[{a.get('category', '其他')}] {a.get('title', '')[:60]}... <small>({a.get('source', '?')})</small></li>"
            for a in e.get('web_articles', [])[:3]
        ]) + "</ul>"
    
    exchange_cards.append(f"""
<div class="exchange-card {alert_level}">
<div class="exchange-header">
<strong>{ex_name}</strong>
<span class="alert-badge {alert_level}">{alert_level.upper()}</span>
</div>
<div class="exchange-stats">
<span>🐦 X帖子: {x_count}</span>
<span>📰 新闻: {web_count}</span>
</div>
{x_posts_html}
{news_html}
</div>
""")

briefing_sections.append(f"""
<div class="briefing-section">
<h2>🏛️ 交易所详情</h2>
<div class="exchange-grid">
{''.join(exchange_cards)}
</div>
</div>
""")

# 4. 生成完整 HTML
html_content = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CEX Intelligence - 今日简报</title>
    <style>
        :root {{
            --color-critical: #ff5252;
            --color-high: #ff9800;
            --color-medium: #ffc107;
            --color-low: #4caf50;
            --color-none: #9e9e9e;
            --bg-primary: #0a0e1a;
            --bg-secondary: #12172b;
            --text-primary: #e0e0e0;
            --text-secondary: #9e9e9e;
        }}
        
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            line-height: 1.6;
            min-height: 100vh;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }}
        
        header {{
            text-align: center;
            padding: 40px 20px;
            background: linear-gradient(135deg, #1a237e 0%, #0d47a1 100%);
            border-radius: 16px;
            margin-bottom: 30px;
        }}
        
        header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
            background: linear-gradient(90deg, #64b5f6, #90caf9);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        
        .timestamp {{
            color: var(--text-secondary);
            font-size: 14px;
        }}
        
        .briefing-section {{
            background: var(--bg-secondary);
            border-radius: 12px;
            padding: 24px;
            margin-bottom: 20px;
            border: 1px solid rgba(255,255,255,0.05);
        }}
        
        .briefing-section h2 {{
            color: #64b5f6;
            margin-bottom: 16px;
            font-size: 1.3em;
        }}
        
        .briefing-section.alert {{
            border-left: 4px solid var(--color-critical);
            background: rgba(255, 82, 82, 0.1);
        }}
        
        .alert-item {{
            background: rgba(255, 82, 82, 0.2);
            padding: 12px;
            border-radius: 8px;
            margin: 8px 0;
            border-left: 3px solid var(--color-critical);
        }}
        
        .exchange-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
            gap: 16px;
        }}
        
        .exchange-card {{
            background: rgba(255,255,255,0.03);
            border-radius: 10px;
            padding: 16px;
            border: 1px solid rgba(255,255,255,0.05);
        }}
        
        .exchange-card.critical {{ border-left: 3px solid var(--color-critical); }}
        .exchange-card.high {{ border-left: 3px solid var(--color-high); }}
        .exchange-card.medium {{ border-left: 3px solid var(--color-medium); }}
        .exchange-card.low {{ border-left: 3px solid var(--color-low); }}
        .exchange-card.none {{ border-left: 3px solid var(--color-none); }}
        
        .exchange-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }}
        
        .exchange-header strong {{
            font-size: 1.1em;
            color: #fff;
        }}
        
        .alert-badge {{
            font-size: 11px;
            padding: 4px 10px;
            border-radius: 20px;
            text-transform: uppercase;
            font-weight: bold;
        }}
        
        .alert-badge.critical {{ background: var(--color-critical); color: white; }}
        .alert-badge.high {{ background: var(--color-high); color: black; }}
        .alert-badge.medium {{ background: var(--color-medium); color: black; }}
        .alert-badge.low {{ background: var(--color-low); color: white; }}
        .alert-badge.none {{ background: var(--color-none); color: white; }}
        
        .exchange-stats {{
            display: flex;
            gap: 20px;
            color: var(--text-secondary);
            font-size: 13px;
            margin-bottom: 12px;
        }}
        
        .post-list, .news-list {{
            list-style: none;
            font-size: 13px;
        }}
        
        .post-list li, .news-list li {{
            padding: 6px 0;
            border-bottom: 1px solid rgba(255,255,255,0.05);
        }}
        
        .sentiment {{
            display: inline-block;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 11px;
            margin-right: 8px;
        }}
        
        .sentiment.positive {{ background: #4caf50; }}
        .sentiment.negative {{ background: #f44336; }}
        .sentiment.neutral {{ background: #757575; }}
        
        footer {{
            text-align: center;
            padding: 30px;
            color: var(--text-secondary);
            font-size: 12px;
            border-top: 1px solid rgba(255,255,255,0.05);
            margin-top: 40px;
        }}
        
        @media (max-width: 768px) {{
            .exchange-grid {{ grid-template-columns: 1fr; }}
            header h1 {{ font-size: 1.8em; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🎯 CEX Intelligence</h1>
            <p>中心化交易所情报监控</p>
            <p class="timestamp">⏰ 生成时间: {timestamp}</p>
        </header>
        
        {''.join(briefing_sections)}
        
        <footer>
            <p>🤖 由 Grok AI 驱动 | 🔄 每日 09:00 自动更新</p>
            <p>数据来源: X(Twitter), Web, FinTelegram</p>
        </footer>
    </div>
</body>
</html>'''

# 写入文件
with open('site/index.html', 'w', encoding='utf-8') as f:
    f.write(html_content)

# 复制 JSON 数据
shutil.copy(latest_file, 'site/data.json')

# 同时生成一个简报文本文件供 Discord 使用
briefing_text = f"""🎯 CEX 每日简报 - {datetime.now().strftime('%Y-%m-%d')}

📊 今日概况
• 监控交易所: {total_exchanges} 个
• 风险状况: {'🚨 发现 ' + str(len(key_alerts)) + ' 项警报' if key_alerts else '✅ 全部正常'}
• Critical: {critical_count} | High: {high_count}

{'🚨 关键警报:\n' + chr(10).join(['• ' + a for a in key_alerts]) if key_alerts else '✅ 今日无重大风险事件'}

🏛️ 交易所状态
{chr(10).join([f"• {e.get('exchange')}: {e.get('alert_level', 'none').upper()} (X:{len(e.get('x_posts',[]))} 新闻:{len(e.get('web_articles',[]))})" for e in exchanges])}

⏰ 生成时间: {timestamp}
🔗 详细报告: https://cex-intelligence.up.railway.app
"""

with open('site/briefing.txt', 'w', encoding='utf-8') as f:
    f.write(briefing_text)

print('✅ 网站文件已生成:')
print(f'  - site/index.html (包含今日简报)')
print(f'  - site/data.json (原始数据)')
print(f'  - site/briefing.txt (Discord简报)')
print(f'\n📊 简报摘要:')
print(f'  • 交易所: {total_exchanges} 个')
print(f'  • 警报: {len(alerted_exchanges)} 个')
print(f'  • Critical/High: {critical_count}/{high_count}')
