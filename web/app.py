from flask import Flask, render_template, jsonify
from datetime import datetime, timedelta
from pathlib import Path
import json
import os

app = Flask(__name__)

DATA_DIR = Path(__file__).parent.parent / "data" / "intelligence"

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
    for i in range(30):
        date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
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

@app.route("/")
def index():
    """首页 - 显示最新简报"""
    today = datetime.now().strftime("%Y-%m-%d")
    data = load_intel(today)
    
    if not data:
        # 尝试加载最近可用的数据
        for i in range(1, 7):
            date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
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
    today = datetime.now().strftime("%Y-%m-%d")
    data = load_intel(today)
    
    if not data:
        for i in range(1, 7):
            date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
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

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
