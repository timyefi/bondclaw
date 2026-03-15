import subprocess
import sys
import time
import os
import json

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

SKILL_DIR = r'C:\Users\Administrator\.claude\skills\mineru'
CONFIG_FILE = os.path.join(SKILL_DIR, 'config.json')

# 1. 自动加载 config.json 中的 token
with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
    config = json.load(f)
os.environ['MINERU_TOKEN'] = config.get('token', '')

# 2. 配置参数
script = os.path.join(SKILL_DIR, 'scripts', 'mineru_stable.py')
input_path = r'C:\Users\Administrator\Desktop\项目\信用工作流\年报训练\恒隆地产2024年報.pdf'
output_dir = r'C:\Users\Administrator\Desktop\项目\信用工作流\年报训练\output\恒隆地产'
log_file = r'C:\Users\Administrator\Desktop\项目\信用工作流\年报训练\output\mineru.log'

# 3. 启动后台进程
process = subprocess.Popen(
    [sys.executable, script,
     '--file', input_path,
     '--output', output_dir,
     '--language', 'ch'],
    stdout=open(log_file, 'w', encoding='utf-8'),
    stderr=subprocess.STDOUT,
    text=True,
    cwd=os.path.dirname(script)
)

print(f"后台任务启动, PID: {process.pid}")

# 4. 轮询检查日志
max_wait = 3600
interval = 15
elapsed = 0

while elapsed < max_wait:
    time.sleep(interval)
    elapsed += interval

    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.strip().split('\n')
            print(f"[{elapsed}秒] {lines[-1] if lines else '...'}")

            if '✅ 成功:' in content:
                print("任务完成!")
                break
            if '❌ 失败:' in content:
                print("任务失败")
                break
    except FileNotFoundError:
        pass
