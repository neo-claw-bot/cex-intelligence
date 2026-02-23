# CEX 情报监控配置

## 监控目标交易所

### Tier 1 (核心监控)
- Binance
- OKX
- Coinbase
- Bybit
- Bitget

### Tier 2 (次级监控)
- Kraken
- KuCoin
- Gate.io
- MEXC

## 信息源配置

### 主要采集工具
1. **Grok/X 搜索** - Twitter/X 社区讨论（优先）
   - 文档: https://docs.x.ai/developers/tools/x-search
   - 能力: 实时推特搜索、趋势分析

2. **Web 搜索** - 浏览器 + Grok web_search
   - 文档: https://docs.x.ai/developers/tools/x-search
   - 覆盖: 新闻、公告、分析报告

3. **FinTelegram** - 真相披露媒体（重点关注）
   - 网站: https://fintelegram.com
   - 特点: 专门曝光交易所问题、骗局、监管事件

### 辅助信息源
- 官方 Twitter 账号
- CoinDesk, CoinTelegraph
- The Block
- 各国监管动态

## 采集频率

| 时段 | 时间 | 重点 |
|------|------|------|
| 白天扫描 | ~12:00 | 隔夜新闻、亚洲市场动态 |
| 晚间扫描 | ~21:00 | 欧美市场、当日汇总 |

## 事件分级

| 级别 | 描述 | 响应时间 |
|------|------|----------|
| 🚨 Critical | 交易所被盗、跑路、监管查封 | 即时 |
| ⚠️ High | 大额资金异常流出、CEO被捕、大规模故障 | 15分钟内 |
| 📊 Medium | 上新币、费率调整、小范围故障 | 1小时内 |
| 📝 Low | 常规公告、营销动态 | 每日汇总 |

## 汇报渠道

**Discord 频道:** #web3交易所情报观察 (当前频道)

## 输出格式

```
🚨 [交易所] - [事件类型]
━━━━━━━━━━━━━━━━━━━━━━━
时间: [UTC+8]
来源: [链接]
摘要: [一句话总结]
影响: [用户/市场/资金]
建议: [行动建议]
```
