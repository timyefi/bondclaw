"""
可转债数据采集 - 配置文件
任务ID: T24
创建时间: 2026-02-15
"""
import os
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent

# 数据目录
DATA_DIR = PROJECT_ROOT / 'data'

# 输出目录
OUTPUT_DIR = PROJECT_ROOT / 'output'

# 数据库配置（使用环境变量）
DB_HOST = os.environ.get('DB_HOST', 'localhost')
DB_PORT = int(os.environ.get('DB_PORT', 3306))
DB_USER = os.environ.get('DB_USER', 'your_username')
DB_PASSWORD = os.environ.get('DB_PASSWORD', 'your_password')
DB_NAME = os.environ.get('DB_NAME', 'bond')

# 同花顺数据接口配置（使用环境变量）
THS_USERNAME = os.environ.get('THS_USERNAME', '')
THS_PASSWORD = os.environ.get('THS_PASSWORD', '')

# 日志配置
LOG_DIR = PROJECT_ROOT / 'logs'
LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')

# 数据采集配置
BATCH_SIZE = int(os.environ.get('BATCH_SIZE', 100))
REQUEST_DELAY = float(os.environ.get('REQUEST_DELAY', 0.2))
MAX_RETRY = int(os.environ.get('MAX_RETRY', 3))

# 确保必要目录存在
DATA_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)
