---
name: grok-search
description: "Use Grok AI (xAI) with x_search and web_search tools via curl. Use when: (1) Need to search X/Twitter posts in real-time, (2) Need to search web content, (3) Building tools that require Grok's search capabilities, (4) Quick intelligence gathering without Python SDK."
---

# Grok Search via curl

Use xAI's Grok with native search tools through simple curl commands.

## Setup API Key

**Option 1: Environment Variable (Recommended)**
```bash
export XAI_API_KEY="your-api-key"
```

**Option 2: .env File**
```bash
# Copy the example file
cp .env.example .env

# Edit .env and add your key
XAI_API_KEY=your-actual-api-key
```

Then load it in scripts:
```bash
export $(cat .env | xargs)
```

**⚠️ Security Warning:** Never commit .env files or expose API keys in chat messages!

## API Endpoint

```
POST https://api.x.ai/v1/responses
```

## Basic Request Structure

```bash
curl -s https://api.x.ai/v1/responses \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $XAI_API_KEY" \
  -d '{
    "model": "grok-4-1-fast-reasoning",
    "input": [
      {"role": "user", "content": "Your search query here"}
    ],
    "tools": ["x_search", "web_search"]
  }'
```

## Search X (Twitter)

Search recent X posts:

```bash
curl -s https://api.x.ai/v1/responses \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $XAI_API_KEY" \
  -d '{
    "model": "grok-4-1-fast-reasoning",
    "input": [
      {"role": "user", "content": "Search X for recent posts about Bitcoin price movement today"}
    ],
    "tools": ["x_search"]
  }' | jq .
```

**Best practices:**
- Be specific: "last 24 hours", "today", "recent"
- Mention X/Twitter explicitly in prompt for clarity
- Ask for structured output in prompt for easier parsing

## Search Web

Search web content:

```bash
curl -s https://api.x.ai/v1/responses \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $XAI_API_KEY" \
  -d '{
    "model": "grok-4-1-fast-reasoning",
    "input": [
      {"role": "user", "content": "Search web for latest cryptocurrency exchange security news"}
    ],
    "tools": ["web_search"]
  }' | jq .
```

## Combined Search

Use both tools together:

```bash
curl -s https://api.x.ai/v1/responses \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $XAI_API_KEY" \
  -d '{
    "model": "grok-4-1-fast-reasoning",
    "input": [
      {"role": "user", "content": "Find recent news and social media discussions about Binance"}
    ],
    "tools": ["x_search", "web_search"]
  }' | jq .
```

## Response Format

Grok returns a JSON response with:

```json
{
  "id": "resp_xxx",
  "model": "grok-4-1-fast-reasoning",
  "output": [
    {
      "role": "assistant",
      "content": [
        {
          "type": "text",
          "text": "Search results here..."
        }
      ]
    }
  ],
  "usage": {
    "prompt_tokens": 100,
    "completion_tokens": 500
  }
}
```

Extract the text content:

```bash
| jq '.output[0].content[0].text'
```

## Prompting for Structured Output

Request JSON for easier processing:

```bash
curl -s https://api.x.ai/v1/responses \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $XAI_API_KEY" \
  -d '{
    "model": "grok-4-1-fast-reasoning",
    "input": [
      {"role": "user", "content": "Search X for crypto exchange news. Return as JSON array with fields: source, content, sentiment"}
    ],
    "tools": ["x_search"]
  }'
```

## Models

| Model | Description |
|-------|-------------|
| `grok-4-1-fast-reasoning` | Fast reasoning with search tools |
| `grok-4-1` | Standard model |

## Available Tools

| Tool | Description |
|------|-------------|
| `x_search` | Search X/Twitter posts |
| `web_search` | Search web content |

## Error Handling

Check for errors:

```bash
curl -s ... | jq 'if has("error") then .error else "OK" end'
```

Common issues:
- 401: Invalid API key
- 429: Rate limit exceeded
- 500: Server error (retry)

## Python Example

```python
import subprocess
import json
import os

def grok_search(prompt: str, tools: list) -> dict:
    api_key = os.getenv("XAI_API_KEY")
    if not api_key:
        raise ValueError("XAI_API_KEY not set")
    
    data = {
        "model": "grok-4-1-fast-reasoning",
        "input": [{"role": "user", "content": prompt}],
        "tools": tools
    }
    
    result = subprocess.run(
        ["curl", "-s", "https://api.x.ai/v1/responses",
         "-H", "Content-Type: application/json",
         "-H", f"Authorization: Bearer {api_key}",
         "-d", json.dumps(data)],
        capture_output=True, text=True
    )
    
    return json.loads(result.stdout)

# Usage
result = grok_search(
    "Search X for Binance news today",
    ["x_search"]
)
```

## References

- xAI Docs: https://docs.x.ai/developers/tools/x-search
- Web Search: https://docs.x.ai/developers/tools/web-search
- API Reference: https://docs.x.ai/developers/quickstart
