#!/usr/bin/env python3
"""
Discord 简报发送器
读取 site/briefing.txt 并发送到 Discord
"""

import os
import sys
from pathlib import Path

# 读取简报文件
briefing_file = Path(__file__).parent / "site" / "briefing.txt"

if not briefing_file.exists():
    print("❌ 错误: site/briefing.txt 不存在")
    print("请先运行: python3 generate_site.py")
    sys.exit(1)

with open(briefing_file, 'r', encoding='utf-8') as f:
    briefing_content = f.read()

# 输出简报内容（用于管道传递到 Discord）
print(briefing_content)

# 同时输出到文件供其他工具使用
output_file = Path(__file__).parent / "site" / "discord_message.txt"
with open(output_file, 'w', encoding='utf-8') as f:
    f.write(briefing_content)

print(f"\n✅ 简报已准备好发送到 Discord")
print(f"📄 文件位置: {briefing_file}")
print(f"📄 消息文件: {output_file}")
