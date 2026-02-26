from flask import Flask, render_template, jsonify, request, session, redirect, url_for
from datetime import datetime, timedelta
from pathlib import Path
import json
import os
import pytz
from functools import wraps

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'cex-intelligence-default-key-change-in-production')

# 配置访问密码
ACCESS_PASSWORD = os.environ.get('ACCESS_PASSWORD', 'cex2024')

DATA_DIR = Path(__file__).parent / "data" / "intelligence"

# CER.live 30个交易所列表
CER_LIVE_EXCHANGES = [
    "Binance", "MEXC", "Gate", "Bitget", "OKX", "HTX", "Bybit",
    "Coinbase Exchange", "CoinW", "BitMart", "Crypto.com", "DigiFinex",
    "LBank", "Upbit", "Toobit", "WEEX", "P2B", "XT.COM", "Tapbit",
    "Kraken", "KuCoin", "Bumba", "WhiteBIT", "Deribit", "OFZA",
    "Flipster", "BingX", "HashKey Exchange", "Nami.Exchange", "Bitstamp"
]

def login_required(f):
    """登录验证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('authenticated') != True:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def load_intel(date_str):
    """加载指定日期的情报数据"""
    filepath = DATA_DIR / f"{date_str}.json"
    if filepath.exists():
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

def get_available_dates():
    """获取可用的日期列表（按时间倒序，最新的在前）"""
    dates = []
    if DATA_DIR.exists():
        # 获取所有json文件，排除历史数据文件
        json_files = [f for f in DATA_DIR.glob("*.json") 
                      if f.stem not in ['historical-2025', 'historical-2025-detailed']]
        # 按文件名倒序（日期格式YYYY-MM-DD可以直接字符串排序）
        for f in sorted(json_files, reverse=True):
            dates.append(f.stem)
    return dates[:30]

def get_exchange_alerts(exchange_name, days=30):
    """获取指定交易所的所有历史警报（去重）"""
    alerts = []
    seen_titles = set()  # 用于去重
    dates = get_available_dates()
    
    for date_str in dates[:days]:
        data = load_intel(date_str)
        # 只从alerts获取，避免与key_alerts重复
        if data and data.get('alerts'):
            for alert in data['alerts']:
                if alert.get('exchange') == exchange_name:
                    title = alert.get('title', '')
                    # 根据标题去重
                    if title not in seen_titles:
                        alert['date'] = date_str
                        alerts.append(alert)
                        seen_titles.add(title)
    
    return sorted(alerts, key=lambda x: x.get('date', ''), reverse=True)

def get_exchange_current_status(exchange_name):
    """获取交易所当前最新状态"""
    dates = get_available_dates()
    
    for date_str in dates[:7]:  # 查最近7天
        data = load_intel(date_str)
        if data and data.get('alerts'):
            for alert in data.get('alerts', []):
                if alert.get('exchange') == exchange_name:
                    return alert.get('severity', 'none')
    return 'none'

def get_all_exchange_status():
    """获取所有交易所的当前状态"""
    status = {}
    for exchange in CER_LIVE_EXCHANGES:
        status[exchange] = get_exchange_current_status(exchange)
    return status

def get_problematic_exchanges(days=7):
    """获取近期负面舆论和争议较多的交易所列表（包含分类）"""
    problematic = {}
    dates = get_available_dates()
    
    # 统计最近N天内各交易所的高/严重风险警报
    for date_str in dates[:days]:
        data = load_intel(date_str)
        if data and data.get('alerts'):
            for alert in data.get('alerts', []):
                if alert.get('severity') in ['high', 'critical']:
                    ex = alert.get('exchange')
                    category = alert.get('category', 'dispute_compliance')
                    if ex:
                        if ex not in problematic:
                            problematic[ex] = {
                                'name': ex,
                                'severity': alert.get('severity'),
                                'category': category,
                                'latest_alert': alert.get('title', ''),
                                'alert_count': 0,
                                'latest_date': date_str
                            }
                        problematic[ex]['alert_count'] += 1
                        # 更新最新日期和严重程度
                        if alert.get('severity') == 'critical':
                            problematic[ex]['severity'] = 'critical'
                        # 优先显示攻击类
                        if category == 'security_attack':
                            problematic[ex]['category'] = category
    
    # 转换为列表，按警报数量排序
    result = list(problematic.values())
    result.sort(key=lambda x: (-x['alert_count'], x['latest_date']), reverse=False)
    
    return result

def get_significant_alerts(days=7):
    """获取值得关注的情报（高/严重风险）"""
    alerts = []
    dates = get_available_dates()
    
    for date_str in dates[:days]:
        data = load_intel(date_str)
        if data and data.get('alerts'):
            for alert in data['alerts']:
                if alert.get('severity') in ['high', 'critical']:
                    alert['date'] = date_str
                    alerts.append(alert)
    
    return sorted(alerts, key=lambda x: x.get('date', ''), reverse=True)[:10]

def get_severity_color(severity):
    """获取严重度对应的颜色"""
    colors = {
        "critical": "bg-red-600 text-white",
        "high": "bg-orange-500 text-white",
        "medium": "bg-yellow-500 text-black",
        "low": "bg-blue-500 text-white",
        "none": "bg-gray-500 text-white"
    }
    return colors.get(severity, "bg-gray-500 text-white")

def get_severity_badge(severity):
    """获取严重度徽章样式"""
    badges = {
        "critical": "🔴 严重",
        "high": "🟠 高危",
        "medium": "🟡 中等",
        "low": "🔵 低危",
        "none": "🟢 正常"
    }
    return badges.get(severity, "⚪ 未知")

# ==================== 路由 ====================

@app.route("/login", methods=['GET', 'POST'])
def login():
    """登录页面"""
    error = None
    if request.method == 'POST':
        password = request.form.get('password', '')
        if password == ACCESS_PASSWORD:
            session['authenticated'] = True
            next_url = request.args.get('next') or url_for('dashboard')
            return redirect(next_url)
        else:
            error = '密码错误'
    return render_template("login.html", error=error)

@app.route("/logout")
def logout():
    """退出登录"""
    session.pop('authenticated', None)
    return redirect(url_for('login'))

@app.route("/")
@login_required
def index():
    """首页重定向到 Dashboard"""
    return redirect(url_for('dashboard'))

@app.route("/dashboard")
@login_required
def dashboard():
    """Dashboard - 首页，按分类展示情报"""
    # 获取最近7天的数据
    dates = get_available_dates()
    
    # 分类统计
    security_attacks = []
    dispute_compliance = []
    operational_risks = []
    
    for date_str in dates[:7]:
        data = load_intel(date_str)
        if data and data.get('alerts'):
            for alert in data['alerts']:
                alert['date'] = date_str
                category = alert.get('category', 'dispute_compliance')
                if category == 'security_attack':
                    security_attacks.append(alert)
                elif category == 'operational_risk':
                    operational_risks.append(alert)
                else:
                    dispute_compliance.append(alert)
    
    # 获取有问题的交易所（包含分类信息）
    problematic = get_problematic_exchanges()
    
    # 统计信息
    stats = {
        'total_exchanges': 30,
        'total_alerts': len(security_attacks) + len(dispute_compliance) + len(operational_risks),
        'security_attack': len(security_attacks),
        'dispute_compliance': len(dispute_compliance),
        'operational_risk': len(operational_risks),
        'monitoring_days': len(get_available_dates())
    }
    
    # 获取所有交易所的当前状态
    exchange_status = get_all_exchange_status()
    
    return render_template("dashboard.html",
                          security_attacks=security_attacks[:10],
                          dispute_compliance=dispute_compliance[:10],
                          operational_risks=operational_risks[:10],
                          problematic=problematic,
                          stats=stats,
                          cer_live_exchanges=CER_LIVE_EXCHANGES,
                          exchange_status=exchange_status,
                          get_severity_color=get_severity_color,
                          get_severity_badge=get_severity_badge)

@app.route("/exchange/<exchange_name>")
@login_required
def exchange_detail(exchange_name):
    """交易所详情页 - 显示该所的时间线争议事件"""
    # 获取该交易所的所有历史警报
    alerts = get_exchange_alerts(exchange_name, days=30)
    
    # 获取今日状态
    today = datetime.now().strftime("%Y-%m-%d")
    today_data = load_intel(today)
    current_status = 'none'
    
    if today_data:
        for alert in today_data.get('alerts', []):
            if alert.get('exchange') == exchange_name:
                current_status = alert.get('severity', 'none')
                break
    
    # 统计
    stats = {
        'total_alerts': len(alerts),
        'high_alerts': len([a for a in alerts if a.get('severity') == 'high']),
        'critical_alerts': len([a for a in alerts if a.get('severity') == 'critical']),
        'last_alert': alerts[0].get('date') if alerts else None
    }
    
    # 获取所有交易所的当前状态
    exchange_status = get_all_exchange_status()
    
    return render_template("exchange_detail.html",
                          exchange_name=exchange_name,
                          alerts=alerts,
                          current_status=current_status,
                          stats=stats,
                          cer_live_exchanges=CER_LIVE_EXCHANGES,
                          exchange_status=exchange_status,
                          get_severity_color=get_severity_color,
                          get_severity_badge=get_severity_badge)

@app.route("/date/<date_str>")
@login_required
def date_view(date_str):
    """查看指定日期的简报"""
    data = load_intel(date_str)
    dates = get_available_dates()
    
    if not data:
        return render_template("error.html", 
                              message=f"未找到 {date_str} 的数据",
                              dates=dates)
    
    # 获取所有交易所的当前状态
    exchange_status = get_all_exchange_status()
    
    return render_template("date_view.html",
                          data=data,
                          date=date_str,
                          dates=dates,
                          cer_live_exchanges=CER_LIVE_EXCHANGES,
                          exchange_status=exchange_status,
                          get_severity_color=get_severity_color,
                          get_severity_badge=get_severity_badge)

@app.route("/alerts")
@login_required
def alerts_list():
    """所有警报列表"""
    all_alerts = []
    dates = get_available_dates()
    
    for date_str in dates[:30]:
        data = load_intel(date_str)
        if data and data.get('alerts'):
            for alert in data['alerts']:
                alert['date'] = date_str
                all_alerts.append(alert)
    
    # 按日期排序
    all_alerts = sorted(all_alerts, key=lambda x: x.get('date', ''), reverse=True)
    
    # 获取所有交易所的当前状态
    exchange_status = get_all_exchange_status()

    return render_template("alerts.html",
                          alerts=all_alerts,
                          cer_live_exchanges=CER_LIVE_EXCHANGES,
                          exchange_status=exchange_status,
                          get_severity_color=get_severity_color,
                          get_severity_badge=get_severity_badge)

# API 路由
@app.route("/api/exchange/<exchange_name>")
@login_required
def api_exchange(exchange_name):
    """API: 获取指定交易所的数据"""
    alerts = get_exchange_alerts(exchange_name, days=30)
    return jsonify({
        'exchange': exchange_name,
        'alerts': alerts,
        'alert_count': len(alerts)
    })

@app.route("/api/dates")
@login_required
def api_dates():
    """API: 获取可用日期列表"""
    return jsonify(get_available_dates())

if __name__ == "__main__":
    app.run(debug=True)
