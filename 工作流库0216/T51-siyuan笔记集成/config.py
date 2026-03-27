# -*- coding: utf-8 -*-
"""
siyuan笔记集成 - 配置文件

该模块包含所有敏感配置信息，使用环境变量管理。
请将环境变量设置在系统环境或 .env 文件中。
"""

import os

# ==================== 通义千问API配置 ====================
DASHSCOPE_API_KEY = os.environ.get("DASHSCOPE_API_KEY", "your_api_key_here")
DASHSCOPE_API_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"

# ==================== 数据库配置 ====================
DB_USER = os.environ.get("DB_USER", "hz_work")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "")
DB_HOST = os.environ.get("DB_HOST", "rm-uf6c8yi6zdq6ea7p1qo.mysql.rds.aliyuncs.com")
DB_PORT = os.environ.get("DB_PORT", "3306")
DB_NAME = os.environ.get("DB_NAME", "yq")

# ==================== 思源笔记API配置 ====================
SIYUAN_API_BASE = os.environ.get("SIYUAN_API_BASE", "http://127.0.0.1:6806")

# ==================== 企业预警通API配置 ====================
QYWYT_TOKEN = os.environ.get("QYWYT_TOKEN", "")
QYWYT_API_BASE = "https://host.ratingdog.cn"

# ==================== 文件路径配置 ====================
# PDF文件下载目录
FOLDER_PATH = os.environ.get("FOLDER_PATH", r"D:\2024年\财报文件")

# ==================== 模型配置 ====================
MODEL_NAME = "qwen-long"  # 通义千问长上下文模型

# ==================== 日志配置 ====================
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


def get_db_connection_string():
    """
    获取数据库连接字符串

    返回:
        格式化的数据库连接字符串
    """
    return f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


def get_headers_dashscope():
    """
    获取通义千问API请求头

    返回:
        请求头字典
    """
    return {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {DASHSCOPE_API_KEY}"
    }


def get_headers_qywyt():
    """
    获取企业预警通API请求头

    返回:
        请求头字典
    """
    return {
        "Content-Type": "application/json",
        "Authorization": f"token {QYWYT_TOKEN}"
    }


# 配置验证
def validate_config():
    """
    验证配置是否完整

    返回:
        (bool, list): (是否有效, 缺失的配置项列表)
    """
    missing = []

    if DASHSCOPE_API_KEY == "your_api_key_here":
        missing.append("DASHSCOPE_API_KEY")

    if not DB_PASSWORD:
        missing.append("DB_PASSWORD")

    if not QYWYT_TOKEN:
        missing.append("QYWYT_TOKEN")

    return len(missing) == 0, missing


if __name__ == "__main__":
    is_valid, missing_items = validate_config()

    if is_valid:
        print("配置验证通过！")
    else:
        print(f"配置验证失败，缺少以下配置项: {', '.join(missing_items)}")
        print("请设置相应的环境变量。")
