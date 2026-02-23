from flask import Flask, render_template, jsonify
from datetime import datetime, timedelta
from pathlib import Path
import json
import os
import pytz

app = Flask(__name__)

DATA_DIR = Path(__file__).parent / "data" / "intelligence"

def load_intel(date_str):
    """加载指定日期的情报数据"""
    filepath = DATA_DIR / f"{date_str}.json"
    if filepath.exists():
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

def get_available_dates():
    """获取可用的日期列表（最近30天）"""
    dates = []
    tz = pytz.timezone('Asia/Shanghai')
    now = datetime.now(tz)
    for i in range(30):
        date = (now - timedelta(days=i)).strftime("%Y-%m-%d")
        if (DATA_DIR / f"{date}.json").exists():
            dates.append(date)
    return dates

def get_severity_color(severity):
    """获取严重度对应的颜色"""
    colors = {
        "critical": "bg-red-600",
        "high": "bg-orange-500",
        "medium": "bg-yellow-500",
        "low": "bg-blue-500"
    }
    return colors.get(severity, "bg-gray-500")

def get_status_emoji(status):
    """获取状态对应的emoji"""
    emojis = {
        "normal": "✅",
        "warning": "⚠️",
        "critical": "🚨"
    }
    return emojis.get(status, "⚪")

def get_severity_score(severity):
    """获取严重度评分（用于计算）"""
    scores = {
        "critical": 4,
        "high": 3,
        "medium": 2,
        "low": 1
    }
    return scores.get(severity, 0)

def analyze_30_days():
    """分析最近30天的数据，生成摘要和交易所评分"""
    dates = get_available_dates()
    all_alerts = []
    exchange_stats = {}
    
    for date in dates:
        data = load_intel(date)
        if not data:
            continue
            
        # 收集所有警报
        if data.get("alerts"):
            for alert in data["alerts"]:
                alert["date"] = date
                all_alerts.append(alert)
                
                # 统计交易所数据
                ex = alert.get("exchange", "Unknown")
                if ex not in exchange_stats:
                    exchange_stats[ex] = {
                        "total_alerts": 0,
                        "critical": 0,
                        "high": 0,
                        "medium": 0,
                        "low": 0,
                        "score": 100  # 初始满分
                    }
                exchange_stats[ex]["total_alerts"] += 1
                severity = alert.get("severity", "low")
                if severity in exchange_stats[ex]:
                    exchange_stats[ex][severity] += 1
    
    # 计算交易所评分（满分100，根据严重事件扣分）
    for ex in exchange_stats:
        stats = exchange_stats[ex]
        # 扣分规则：critical -25, high -15, medium -5, low -2
        deduction = (stats["critical"] * 25 + 
                    stats["high"] * 15 + 
                    stats["medium"] * 5 + 
                    stats["low"] * 2)
        stats["score"] = max(0, 100 - deduction)
        
        # 确定状态
        if stats["critical"] > 0 or stats["score"] < 60:
            stats["status"] = "critical"
        elif stats["high"] > 0 or stats["score"] < 80:
            stats["status"] = "warning"
        else:
            stats["status"] = "normal"
    
    # 排序：按严重度排序警报
    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    all_alerts.sort(key=lambda x: (severity_order.get(x.get("severity", "low"), 4), x.get("date", "")))
    
    # 只返回最近30天内的高优先级警报
    significant_alerts = [a for a in all_alerts if a.get("severity") in ["critical", "high"]][:10]
    
    return {
        "significant_alerts": significant_alerts,
        "exchange_scores": exchange_stats,
        "total_days": len(dates),
        "total_alerts": len(all_alerts)
    }

@app.route("/")
def index():
    """首页 - 显示最新简报"""
    tz = pytz.timezone('Asia/Shanghai')
    today = datetime.now(tz).strftime("%Y-%m-%d")
    data = load_intel(today)
    
    if not data:
        # 尝试加载最近可用的数据
        for i in range(1, 7):
            date = (datetime.now(tz) - timedelta(days=i)).strftime("%Y-%m-%d")
            data = load_intel(date)
            if data:
                break
    
    if not data:
        return render_template("index.html", error="暂无数据", dates=[])
    
    dates = get_available_dates()
    
    return render_template("index.html", 
                          data=data, 
                          dates=dates,
                          get_severity_color=get_severity_color,
                          get_status_emoji=get_status_emoji)

@app.route("/dashboard")
def dashboard():
    """Dashboard - 整体状态显示"""
    # 获取今日数据
    tz = pytz.timezone('Asia/Shanghai')
    today = datetime.now(tz).strftime("%Y-%m-%d")
    today_data = load_intel(today)
    
    if not today_data:
        for i in range(1, 7):
            date = (datetime.now(tz) - timedelta(days=i)).strftime("%Y-%m-%d")
            today_data = load_intel(date)
            if today_data:
                break
    
    # 分析30天数据
    analysis = analyze_30_days()
    
    return render_template("dashboard.html",
                          today_data=today_data,
                          analysis=analysis,
                          get_severity_color=get_severity_color,
                          get_status_emoji=get_status_emoji,
                          today=datetime.now().strftime("%Y-%m-%d"))

@app.route("/date/<date_str>")
def date_view(date_str):
    """查看指定日期的简报"""
    data = load_intel(date_str)
    dates = get_available_dates()
    
    if not data:
        return render_template("index.html", 
                              error=f"未找到 {date_str} 的数据", 
                              dates=dates)
    
    return render_template("index.html", 
                          data=data, 
                          dates=dates,
                          current_date=date_str,
                          get_severity_color=get_severity_color,
                          get_status_emoji=get_status_emoji)

@app.route("/api/latest")
def api_latest():
    """API: 获取最新简报数据"""
    tz = pytz.timezone('Asia/Shanghai')
    today = datetime.now(tz).strftime("%Y-%m-%d")
    data = load_intel(today)
    
    if not data:
        for i in range(1, 7):
            date = (datetime.now(tz) - timedelta(days=i)).strftime("%Y-%m-%d")
            data = load_intel(date)
            if data:
                break
    
    if data:
        return jsonify(data)
    return jsonify({"error": "No data available"}), 404

@app.route("/api/dates")
def api_dates():
    """API: 获取可用日期列表"""
    return jsonify(get_available_dates())

@app.route("/api/<date_str>")
def api_date(date_str):
    """API: 获取指定日期数据"""
    data = load_intel(date_str)
    if data:
        return jsonify(data)
    return jsonify({"error": "Date not found"}), 404

@app.route("/api/dashboard")
def api_dashboard():
    """API: 获取Dashboard数据"""
    analysis = analyze_30_days()
    return jsonify(analysis)


def get_exchange_history(exchange_name):
    """获取指定交易所的所有历史数据"""
    dates = get_available_dates()
    history = []
    stats = {
        "total_alerts": 0,
        "critical": 0,
        "high": 0,
        "medium": 0,
        "low": 0,
        "first_seen": None,
        "last_seen": None
    }
    
    for date in dates:
        data = load_intel(date)
        if not data:
            continue
            
        # 检查该交易所的警报
        if data.get("alerts"):
            for alert in data["alerts"]:
                if alert.get("exchange", "").lower() == exchange_name.lower():
                    alert_copy = alert.copy()
                    alert_copy["date"] = date
                    history.append(alert_copy)
                    
                    # 统计
                    stats["total_alerts"] += 1
                    severity = alert.get("severity", "low")
                    if severity in stats:
                        stats[severity] += 1
                    
                    # 时间范围
                    if stats["first_seen"] is None:
                        stats["first_seen"] = date
                    stats["last_seen"] = date
        
        # 检查该交易所的状态记录
        if data.get("exchange_status") and exchange_name in data.get("exchange_status", {}):
            status_info = data["exchange_status"][exchange_name]
            if status_info.get("notes"):
                history.append({
                    "date": date,
                    "exchange": exchange_name,
                    "title": "状态更新",
                    "description": status_info["notes"],
                    "severity": "low",
                    "category": "status",
                    "status": status_info.get("status", "normal"),
                    "url": status_info.get("url", "")
                })
    
    # 按日期排序（最新的在前）
    history.sort(key=lambda x: x.get("date", ""), reverse=True)
    
    # 计算安全评分
    score = 100
    score -= stats["critical"] * 25
    score -= stats["high"] * 15
    score -= stats["medium"] * 5
    score -= stats["low"] * 2
    stats["score"] = max(0, score)
    
    # 确定总体状态
    if stats["critical"] > 0:
        stats["overall_status"] = "critical"
    elif stats["high"] > 0:
        stats["overall_status"] = "warning"
    else:
        stats["overall_status"] = "normal"
    
    return history, stats


@app.route("/exchange/<exchange_name>")
def exchange_detail(exchange_name):
    """交易所详情页 - 显示该交易所的所有历史事件"""
    history, stats = get_exchange_history(exchange_name)
    
    # 获取该交易所的最新状态
    tz = pytz.timezone('Asia/Shanghai')
    today = datetime.now(tz).strftime("%Y-%m-%d")
    today_data = load_intel(today)
    current_status = None
    
    if today_data and today_data.get("exchange_status"):
        current_status = today_data["exchange_status"].get(exchange_name)
    
    # 如果没有今日数据，尝试获取最近的状态
    if not current_status:
        for i in range(1, 7):
            date = (datetime.now(tz) - timedelta(days=i)).strftime("%Y-%m-%d")
            data = load_intel(date)
            if data and data.get("exchange_status"):
                current_status = data["exchange_status"].get(exchange_name)
                if current_status:
                    break
    
    return render_template("exchange.html",
                          exchange_name=exchange_name,
                          history=history,
                          stats=stats,
                          current_status=current_status,
                          get_severity_color=get_severity_color,
                          get_status_emoji=get_status_emoji)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
