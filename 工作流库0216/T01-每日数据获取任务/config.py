"""
T01-每日数据获取任务 - 配置文件
任务ID: T01
创建时间: 2026-02-14

注意: 所有敏感信息通过环境变量读取，请先配置.env文件
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# 加载.env文件
env_path = Path(__file__).parent / '.env'
load_dotenv(env_path)

# ============================================
# 项目路径配置
# ============================================
PROJECT_ROOT = Path(__file__).parent
DATA_DIR = PROJECT_ROOT / 'data'
OUTPUT_DIR = PROJECT_ROOT / 'output'
SRC_DIR = PROJECT_ROOT / 'src'
ASSETS_DIR = PROJECT_ROOT / 'assets'

# 确保目录存在
for dir_path in [DATA_DIR, OUTPUT_DIR, SRC_DIR, ASSETS_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# ============================================
# MySQL 数据库配置
# ============================================
DB_HOST = os.environ.get('DB_HOST', 'localhost')
DB_PORT = int(os.environ.get('DB_PORT', 3306))
DB_USER = os.environ.get('DB_USER', 'your_username')
DB_PASSWORD = os.environ.get('DB_PASSWORD', 'your_password')
DB_NAME = os.environ.get('DB_NAME', 'bond')
DB_CHARSET = 'utf8'

# MySQL连接配置字典
MYSQL_CONFIG = {
    'host': DB_HOST,
    'port': DB_PORT,
    'user': DB_USER,
    'password': DB_PASSWORD,
    'database': DB_NAME,
    'charset': DB_CHARSET,
}

# SQLAlchemy连接字符串
MYSQL_URI = f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'

# ============================================
# PostgreSQL 数据库配置
# ============================================
POSTGRES_HOST = os.environ.get('POSTGRES_HOST', 'localhost')
POSTGRES_PORT = int(os.environ.get('POSTGRES_PORT', 5432))
POSTGRES_USER = os.environ.get('POSTGRES_USER', 'your_username')
POSTGRES_PASSWORD = os.environ.get('POSTGRES_PASSWORD', 'your_password')
POSTGRES_DB = os.environ.get('POSTGRES_DB', 'tsdb')

# PostgreSQL连接配置字典
POSTGRES_CONFIG = {
    'host': POSTGRES_HOST,
    'port': POSTGRES_PORT,
    'user': POSTGRES_USER,
    'password': POSTGRES_PASSWORD,
    'dbname': POSTGRES_DB,
}

# ============================================
# THS API 配置
# ============================================
THS_USER = os.environ.get('THS_USER', '')
THS_PASSWORD = os.environ.get('THS_PASSWORD', '')
THS_USER_2 = os.environ.get('THS_USER_2', '')
THS_PASSWORD_2 = os.environ.get('THS_PASSWORD_2', '')
THS_USER_3 = os.environ.get('THS_USER_3', '')
THS_PASSWORD_3 = os.environ.get('THS_PASSWORD_3', '')

# THS账户列表
THS_ACCOUNTS = [
    {'name': 'primary', 'user': THS_USER, 'password': THS_PASSWORD},
    {'name': 'backup1', 'user': THS_USER_2, 'password': THS_PASSWORD_2},
    {'name': 'backup2', 'user': THS_USER_3, 'password': THS_PASSWORD_3},
]

# ============================================
# 数据配置
# ============================================
DATA_START_DATE = os.environ.get('DATA_START_DATE', '2021-01-01')
DATA_END_DATE = os.environ.get('DATA_END_DATE', '2030-12-31')
API_TIMEOUT = int(os.environ.get('API_TIMEOUT', 30))
MAX_RETRIES = int(os.environ.get('MAX_RETRIES', 3))

# ============================================
# 可转债指标配置
# ============================================
CONVERTIBLE_BOND_INDICATORS = [
    {'name': 'ths_bond_close_cbond', 'param': '103', 'description': '收盘价'},
    {'name': 'ths_new_bond_amt_cbond', 'param': '', 'description': '成交额'},
    {'name': 'ths_pure_bond_premium_rate_cbond', 'param': '', 'description': '纯债溢价率'},
    {'name': 'ths_pure_bond_ytm_cbond', 'param': '', 'description': '纯债到期收益率'},
    {'name': 'ths_conversion_premium_rate_cbond', 'param': '', 'description': '转股溢价率'},
    {'name': 'ths_conver_pe_cbond', 'param': '', 'description': '转股市盈率'},
    {'name': 'ths_stock_pe_cbond', 'param': '', 'description': '正股市盈率'},
    {'name': 'ths_stock_pb_cbond', 'param': '', 'description': '正股市净率'},
    {'name': 'ths_conver_pb_cbond', 'param': '', 'description': '转股市净率'},
]

# ============================================
# 收益率曲线期限配置
# ============================================
TARGET_TERMS = [
    0.083333333,   # 1个月
    0.24999999899999997,  # 3个月
    0.49999999799999995,  # 6个月
    0.749999997,   # 9个月
    1.0,           # 1年
    1.75,          # 1.75年
    2.0,           # 2年
    3.0,           # 3年
    4.0,           # 4年
    5.0,           # 5年
    7.0,           # 7年
    10.0,          # 10年
    15.0,          # 15年
    20.0,          # 20年
    30.0,          # 30年
]

# ============================================
# 日志配置
# ============================================
LOG_LEVEL = 'INFO'
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
