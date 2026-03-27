# -*- coding: utf-8 -*-
"""
T02-每日脚本任务 - 配置文件
任务ID: T02
创建时间: 2026-02-14
描述: 每日脚本任务的配置参数，包含数据库、API等配置
"""

import os
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent

# 数据目录
DATA_DIR = PROJECT_ROOT / 'data'

# 输出目录
OUTPUT_DIR = PROJECT_ROOT / 'output'

# 源代码备份目录
SRC_DIR = PROJECT_ROOT / 'src'

# ==================== 数据库配置 ====================
# 使用环境变量，禁止硬编码敏感信息
DB_HOST = os.environ.get('DB_HOST', 'localhost')
DB_PORT = int(os.environ.get('DB_PORT', 3306))
DB_USER = os.environ.get('DB_USER', 'your_username')
DB_PASSWORD = os.environ.get('DB_PASSWORD', 'your_password')
DB_NAME = os.environ.get('DB_NAME', 'bond')

# SQLAlchemy连接字符串
def get_db_connection_string():
    """获取数据库连接字符串"""
    return f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'

# ==================== THS API配置 ====================
THS_USERNAME = os.environ.get('THS_USERNAME', '')
THS_PASSWORD = os.environ.get('THS_PASSWORD', '')

# ==================== 代理配置 ====================
PROXY_ENABLED = os.environ.get('PROXY_ENABLED', 'false').lower() == 'true'
PROXY_API_URL = os.environ.get('PROXY_API_URL', '')

# ==================== 脚本执行配置 ====================
# 各脚本默认执行时间配置
SCRIPT_SCHEDULE = {
    'td.py': ['01:00'],
    'thslc.py': ['09:00', '19:30'],
    'tzzxw.py': ['19:30', '23:30'],
    'xyzgm.py': ['02:00', '20:00'],
    'yyxt.py': ['06:00'],
    'zhaishiguimo.py': ['06:00', '20:00', '21:00'],
    'zqdq.py': ['20:30', '21:00'],
    'cind.py': ['11:00'],
    'cyhs.py': ['03:30'],
    'jrzyq.py': ['23:30', '23:59'],
    'qxqyb.py': ['06:00'],
    'yhzf.py': ['18:00', '19:00'],
    'yjfxct.py': ['17:00', '18:30', '20:00', '21:00'],
    'yuqing.py': ['05:30', '20:00', '21:00', '21:30'],
    'yycjqb.py': ['22:00-23:00'],  # 每10分钟
    'licaishouyi.py': ['09:00', '15:00', '19:00', '20:00', '21:00'],
    'zqfx.py': ['20:30', '21:00'],
}

# ==================== 超时和重试配置 ====================
REQUEST_TIMEOUT = int(os.environ.get('REQUEST_TIMEOUT', 30))
MAX_RETRY_COUNT = int(os.environ.get('MAX_RETRY_COUNT', 3))
RETRY_DELAY = int(os.environ.get('RETRY_DELAY', 5))

# ==================== 日志配置 ====================
LOG_DIR = PROJECT_ROOT / 'logs'
LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# ==================== 其他配置 ====================
# 土地数据API
LAND_API_BASE_URL = 'https://api.landchina.com/tGdxm'

# 理财数据表名
LICAI_TABLE_NAME = '理财期限跟踪1'

print(f"配置加载完成 - 项目目录: {PROJECT_ROOT}")
