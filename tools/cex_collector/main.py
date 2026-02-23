#!/usr/bin/env python3
"""
极简的 Grok CLI 工具
默认启用 web_search 和 x_search
"""
import os
import sys
import argparse
from dotenv import load_dotenv
from xai_sdk import Client
from xai_sdk.chat import user, system
from xai_sdk.tools import web_search, x_search


def main():
    # 加载环境变量
    load_dotenv()
    
    # 解析命令行参数
    parser = argparse.ArgumentParser(
        description="极简的 Grok CLI 工具，默认启用 web_search 和 x_search"
    )
    parser.add_argument(
        "prompt",
        nargs="?",
        help="要发送给 Grok 的提示词"
    )
    parser.add_argument(
        "-m", "--model",
        default="grok-4-1-fast-reasoning",
        help="使用的模型 (默认: grok-4-1-fast-reasoning)"
    )
    parser.add_argument(
        "--no-web-search",
        action="store_true",
        help="禁用 web_search 工具"
    )
    parser.add_argument(
        "--no-x-search",
        action="store_true",
        help="禁用 x_search 工具"
    )
    
    args = parser.parse_args()
    
    # 检查 API key
    api_key = os.getenv("XAI_API_KEY")
    if not api_key:
        print("错误: 未找到 XAI_API_KEY 环境变量")
        print("请在 .env 文件中设置: XAI_API_KEY=your_api_key")
        sys.exit(1)
    
    # 获取提示词
    if args.prompt:
        prompt_text = args.prompt
    else:
        # 从标准输入读取
        if sys.stdin.isatty():
            print("请输入提示词 (Ctrl+D 结束):")
        prompt_text = sys.stdin.read().strip()
        if not prompt_text:
            parser.print_help()
            sys.exit(1)
    
    # 配置工具
    tools = []
    if not args.no_web_search:
        tools.append(web_search())
    if not args.no_x_search:
        tools.append(x_search())
    
    # 创建客户端
    client = Client(
        api_key=api_key,
        timeout=3600
    )
    
    try:
        # 创建聊天
        chat = client.chat.create(
            model=args.model,
            tools=tools if tools else None,
        )
        
        chat.append(system("你是 Grok，一个高度智能、乐于助人的 AI 助手。"))
        chat.append(user(prompt_text))
        
        # 流式输出
        print()
        
        for response, chunk in chat.stream():
            # 显示工具调用
            if hasattr(chunk, 'tool_calls') and chunk.tool_calls:
                for tool_call in chunk.tool_calls:
                    print(f"\n🔧 调用工具: {tool_call.function.name}")
                    print(f"   参数: {tool_call.function.arguments}\n")
            
            # 显示内容
            if chunk.content:
                print(chunk.content, end="", flush=True)
        
        # 显示引用
        if hasattr(response, 'citations') and response.citations:
            print("\n\n📚 引用:")
            for i, citation in enumerate(response.citations, 1):
                print(f"{i}. {citation}")
        
        print("\n")
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        print("\n提示: 请确保:")
        print("  1. 已安装最新版本的 xai-sdk: uv sync")
        print("  2. 使用支持 Agent Tools 的模型，如 grok-4-1-fast-reasoning")
        print("  3. API Key 有效且有足够的额度")
        sys.exit(1)


if __name__ == "__main__":
    main()
