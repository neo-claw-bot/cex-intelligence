# Grok CLI

极简的 Grok CLI 工具，默认启用 `web_search` 和 `x_search` 功能。

## 两种使用方式

### 方式 1: 极简 Bash 脚本（推荐）

只需一个 bash 脚本 + curl，无需任何依赖！

```bash
# 赋予执行权限
chmod +x grok

# 使用
./grok "What is xAI?"
```

**依赖要求:**
- `curl` (系统自带)
- `jq` (用于解析 JSON，可选)

如果没有 `jq`，可以安装：
```bash
# macOS
brew install jq

# Ubuntu/Debian
sudo apt-get install jq
```

### 方式 2: Python 版本（功能更丰富）

使用官方 xai-sdk，支持更多功能。

```bash
# 安装依赖
uv sync

# 使用
uv run grok "What is xAI?"
```

## 配置

在项目根目录创建 `.env` 文件，添加你的 xAI API Key：

```bash
XAI_API_KEY=your_api_key_here
```

或直接设置环境变量：

```bash
export XAI_API_KEY=your_api_key_here
```

获取 API Key：访问 [xAI API Console](https://console.x.ai/) 创建。

## 使用示例

### Bash 版本

```bash
# 基本使用
./grok "What is xAI?"

# 搜索最新信息
./grok "What are the latest developments in AI?"

# 查询 X/Twitter 动态
./grok "What are people saying about xAI on X?"

# 结合两种搜索
./grok "Compare web news and X posts about the latest SpaceX launch"
```

### Python 版本

```bash
# 直接传入提示词
uv run grok "What is xAI?"

# 从标准输入读取
echo "What are people saying about AI on X?" | uv run grok

# 自定义模型
uv run grok "Explain quantum computing" --model grok-4-1-fast-reasoning

# 禁用搜索工具
uv run grok "Hello" --no-web-search --no-x-search
```

## Python 版本命令行参数

```
positional arguments:
  prompt                要发送给 Grok 的提示词

options:
  -h, --help            显示帮助信息
  -m MODEL, --model MODEL
                        使用的模型 (默认: grok-4-1-fast-reasoning)
  --no-web-search       禁用 web_search 工具
  --no-x-search         禁用 x_search 工具
```

## 技术栈

### Bash 版本
- Bash
- curl
- jq (可选，用于 JSON 解析)

### Python 版本
- Python 3.10+
- [uv](https://github.com/astral-sh/uv) - 快速的 Python 包管理器
- [xai-sdk](https://github.com/xai-org/xai-sdk-python) - xAI 官方 Python SDK
- grok-4-1-fast-reasoning - xAI 的推理模型

## 参考文档

- [xAI 快速开始](https://docs.x.ai/docs/tutorial)
- [Agent Tools API 概览](https://docs.x.ai/docs/guides/tools/overview)
- [Web Search 工具](https://docs.x.ai/docs/guides/live-search)
- [X Search 工具](https://docs.x.ai/developers/tools/x-search)
- [结构化输出](https://docs.x.ai/developers/model-capabilities/text/structured-outputs)
