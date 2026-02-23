# CEX Intelligence Dashboard

实时监控主流Web3中心化交易所的情报、争议和安全风险。

## 技术栈
- **后端**: Python Flask
- **前端**: HTML + Tailwind CSS
- **数据**: JSON 静态文件
- **部署**: Railway

## 监控交易所
- Binance, OKX, Coinbase, Bybit, Bitget, Kraken, KuCoin

## 本地运行
```bash
pip install -r requirements.txt
python app.py
```

## 数据更新
每日 09:00、15:00、21:00 (北京时间) 自动采集并更新。
