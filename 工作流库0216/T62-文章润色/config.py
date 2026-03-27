# -*- coding: utf-8 -*-
"""
T62-文章润色 配置文件
使用环境变量管理敏感信息
"""

import os

# 阿里云 Qwen API 配置
DASHSCOPE_API_KEY = os.environ.get("DASHSCOPE_API_KEY", "")
DASHSCOPE_BASE_URL = os.environ.get("DASHSCOPE_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")

# 模型配置
MODEL_NAME = os.environ.get("MODEL_NAME", "qwen-max")
MAX_TOKENS = int(os.environ.get("MAX_TOKENS", "2000"))
TEMPERATURE = float(os.environ.get("TEMPERATURE", "0.1"))

# 默认路径配置
DATA_DIR = "data"
OUTPUT_DIR = "output"
ASSETS_DIR = "assets"

# 润色提示词
REFINE_SYSTEM_PROMPT = "You are a helpful assistant."
REFINE_USER_PROMPT_TEMPLATE = "将下列段落进行润色，同时保持其原有的结构和风格：{paragraph}"
