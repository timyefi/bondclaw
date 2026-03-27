# -*- coding: utf-8 -*-
"""MinerU 执行器 - 启动后台进程"""
import subprocess
import sys
import os
import json
from pathlib import Path

# Windows UTF-8 编码
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

SKILL_DIR = Path(__file__).parent.parent
CONFIG_FILE = SKILL_DIR / 'config.json'

# 1. 自动加载 token
if CONFIG_FILE.exists():
    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        config = json.load(f)
    token = config.get('token', '')
    if token:
        os.environ['MINERU_TOKEN'] = token
        print(f"✅ 已加载 Token")

# 2. 解析参数
import argparse
parser = argparse.ArgumentParser()
parser.add_argument('--file', required=True)
parser.add_argument('--output', required=True)
parser.add_argument('--workers', type=int, default=5)
args = parser.parse_args()

# 3. 准备路径
script = Path(__file__).parent / 'mineru_stable.py'
output_dir = Path(args.output)
output_dir.mkdir(parents=True, exist_ok=True)
log_file = output_dir / 'mineru.log'

# 4. 启动后台进程
print(f"📄 输入: {args.file}")
print(f"📁 输出: {args.output}")
print(f"📝 日志: {log_file}")

process = subprocess.Popen(
    [sys.executable, str(script),
     '--file', args.file,
     '--output', str(output_dir),
     '--language', 'ch'],
    stdout=open(log_file, 'w', encoding='utf-8'),
    stderr=subprocess.STDOUT,
    text=True,
    cwd=str(script.parent)
)

print(f"✅ 后台进程已启动, PID: {process.pid}")
print(f"请使用以下命令查看日志:")
print(f"  Get-Content '{log_file}' -Tail 20")
