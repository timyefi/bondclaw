#!/usr/bin/env python3
"""
Mineru Wrapper - 自动读取配置文件中的 API Token
"""
import json
import os
import sys
from pathlib import Path

# 获取技能目录
SCRIPT_DIR = Path(__file__).parent.parent
CONFIG_FILE = SCRIPT_DIR / "config.json"

def load_config():
    """加载配置文件"""
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def main():
    # 读取配置
    config = load_config()
    
    # 如果配置中有 token，设置环境变量
    if "token" in config:
        os.environ["MINERU_TOKEN"] = config["token"]
        print("[OK] MinerU Token loaded from config file")
    
    # 传递所有参数给主脚本
    from mineru_v2 import main as v2_main
    from mineru_stable import main as stable_main
    
    # 根据调用方式选择主脚本
    script_name = Path(sys.argv[0]).stem
    
    if script_name == "mineru" or (len(sys.argv) > 1 and sys.argv[1] == "v2"):
        sys.argv[0] = str(SCRIPT_DIR / "mineru_v2.py")
        v2_main()
    elif script_name == "mineru_stable":
        sys.argv[0] = str(SCRIPT_DIR / "mineru_stable.py")
        stable_main()
    else:
        # 默认使用 v2
        sys.argv[0] = str(SCRIPT_DIR / "mineru_v2.py")
        v2_main()

if __name__ == "__main__":
    main()
