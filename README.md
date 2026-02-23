# Grok CEX 情报采集工具

基于 xAI 官方 SDK 的中心化交易所情报采集系统。

## 特性

- ✅ 使用 xai_sdk 官方 SDK
- ✅ 原生支持 web_search 和 x_search 工具
- ✅ grok-4-1-fast-reasoning 模型
- ✅ Pydantic 结构化输出
- ✅ uv 包管理
- ✅ 支持自定义 prompt

## 快速开始

### 1. 安装 uv (如果还没有)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. 设置环境

```bash
# 克隆/进入项目
cd grok-cex-collector

# 创建虚拟环境并安装依赖
uv sync

# 激活环境
source .venv/bin/activate  # Linux/Mac
# 或
.venv\Scripts\activate  # Windows
```

### 3. 配置 API Key

```bash
cp .env.example .env
# 编辑 .env 填入你的 xAI API Key
```

### 4. 运行

```bash
# 全量监控
python -m cex_collector

# 仅核心交易所
python -m cex_collector --focus tier1

# 检查 FinTelegram
python -m cex_collector --fintelegram

# 自定义查询
python -m cex_collector --query "Binance withdrawal issues"
```

## 项目结构

```
.
├── pyproject.toml          # uv 项目配置
├── .env.example           # 环境变量模板
├── README.md
└── src/
    └── cex_collector/
        ├── __init__.py
        ├── __main__.py       # CLI 入口
        ├── collector.py      # 核心采集逻辑
        ├── models.py         # Pydantic 结构化模型
        └── prompts.py        # 默认 prompt 模板
```

## 监控范围

**Tier 1 (核心):** Binance, OKX, Coinbase, Bybit, Bitget

**Tier 2 (次级):** Kraken, KuCoin, Gate.io, MEXC

## 参考文档

- [xAI Quickstart](https://docs.x.ai/developers/quickstart)
- [Generate Text](https://docs.x.ai/developers/model-capabilities/text/generate-text)
- [Reasoning](https://docs.x.ai/developers/model-capabilities/text/reasoning)
- [Structured Outputs](https://docs.x.ai/developers/model-capabilities/text/structured-outputs)
- [Web Search Tool](https://docs.x.ai/developers/tools/web-search)
- [X Search Tool](https://docs.x.ai/developers/tools/x-search)
