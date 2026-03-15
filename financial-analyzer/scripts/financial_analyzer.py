#!/usr/bin/env python3
"""
兼容入口，转发到开放式财务分析引擎。
"""

import runpy
import sys
from pathlib import Path


if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass


def main():
    target = Path(__file__).with_name("financial_analyzer_v3.py")
    runpy.run_path(str(target), run_name="__main__")


if __name__ == "__main__":
    main()
