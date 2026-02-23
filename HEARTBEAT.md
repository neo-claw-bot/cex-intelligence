# Heartbeat Tasks - CEX Intelligence Monitoring

## 特殊事件处理

### CEX情报简报事件
当收到 systemEvent: "CEX情报简报:生成并发送每日简报" 时:
1. 运行 `python3 daily_briefing.py` 采集情报
2. 读取生成的简报文件 `data/last_discord_msg.txt`
3. 将简报内容发送给用户

## 监控清单 (每次心跳检查)

- [ ] 检查关键新闻源 (CoinDesk, Cointelegraph)
- [ ] 扫描 Twitter 趋势和官方账号
- [ ] 检查是否有重大安全事件
- [ ] 查看监管动态
- [ ] 更新情报日志

## 执行频率

- 高频检查 (每 15-30 分钟): Twitter/X, 安全事件
- 中频检查 (每 1-2 小时): 新闻源, 公告
- 低频汇总 (每日): 常规动态, 情绪分析

## 状态追踪

使用 `memory/heartbeat-state.json` 记录最后检查时间。
