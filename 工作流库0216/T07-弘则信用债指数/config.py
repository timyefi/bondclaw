# -*- coding: utf-8 -*-
"""
T07 - 弘则信用债指数 配置文件

本配置文件包含数据库连接信息、指数参数和其他配置项。
敏感信息通过环境变量获取，避免硬编码密码。
"""

import os

# ============================================================
# PostgreSQL 数据库配置 (tsdb)
# ============================================================
PG_CONFIG = {
    'host': os.environ.get('PG_HOST', '139.224.107.113'),
    'port': int(os.environ.get('PG_PORT', 18032)),
    'user': os.environ.get('PG_USER', 'postgres'),
    'password': os.environ.get('PG_PASSWORD', ''),  # 从环境变量获取密码
    'database': os.environ.get('PG_DATABASE', 'tsdb')
}

# ============================================================
# MySQL 数据库配置 (bond)
# ============================================================
MYSQL_CONFIG = {
    'host': os.environ.get('MYSQL_HOST', 'rm-uf6c8yi6zdq6ea7p1qo.mysql.rds.aliyuncs.com'),
    'port': int(os.environ.get('MYSQL_PORT', 3306)),
    'user': os.environ.get('MYSQL_USER', 'hz_work'),
    'password': os.environ.get('MYSQL_PASSWORD', ''),  # 从环境变量获取密码
    'database': os.environ.get('MYSQL_DATABASE', 'bond')
}

# ============================================================
# 指数配置
# ============================================================
INDEX_CONFIG = {
    'target_term': 3,           # 目标期限（年）
    'percentile_groups': 10,     # 分位数组数
    'bond_types': ['credit', 'finance'],  # 债券类型
    'price_types': ['full', 'net'],       # 价格类型
    'min_bonds_per_group': 5,   # 每组最少债券数
    'update_frequency': 'daily' # 更新频率
}

# ============================================================
# 目录配置
# ============================================================
import pathlib

# 项目根目录
PROJECT_ROOT = pathlib.Path(__file__).parent.absolute()

# 缓存目录
CACHE_DIR = str(PROJECT_ROOT / 'cache')

# 输出目录
OUTPUT_DIR = str(PROJECT_ROOT / 'output')

# 数据目录
DATA_DIR = str(PROJECT_ROOT / 'data')

# 资源目录
ASSETS_DIR = str(PROJECT_ROOT / 'assets')

# ============================================================
# 可视化配置
# ============================================================
VIZ_CONFIG = {
    'style': 'plotly',
    'height': 800,
    'width': 1200,
    'color_palette': {
        'credit': 'blue',
        'finance': 'red',
        'full': 'solid',
        'net': 'dashed'
    },
    'date_ranges': {
        '1m': 'months',
        '3m': 'months',
        '6m': 'months',
        '1y': 'year',
        'all': None
    }
}

# ============================================================
# 数据库表配置
# ============================================================
DB_TABLES = {
    # PostgreSQL 表
    'pg': {
        'yield_curve': 'hzcurve_credit',
        'credit_basic_info': 'basicinfo_credit',
        'finance_basic_info': 'basicinfo_finance'
    },
    # MySQL 表
    'mysql': {
        'credit_market_info': 'marketinfo_credit',
        'finance_market_info': 'marketinfo_finance',
        'bond_indices': 'bond_indices',
        'bond_index_constituents': 'bond_index_constituents'
    }
}

# ============================================================
# 查询模板
# ============================================================
QUERY_TEMPLATES = {
    'credit_bonds': """
        SELECT trade_code
        FROM basicinfo_credit
        WHERE ths_is_issuing_failure_bond != '是'
    """,
    'finance_bonds': """
        SELECT trade_code
        FROM basicinfo_finance
        WHERE ths_is_issuing_failure_bond != '是'
    """,
    'yield_data': """
        SELECT dt, trade_code, stdyield, balance
        FROM hzcurve_credit
        WHERE dt >= '{start_date}' AND dt <= '{end_date}'
        AND target_term = {target_term}
        AND stdyield IS NOT NULL
        ORDER BY dt, stdyield DESC
    """,
    'price_data': """
        SELECT DT, TRADE_CODE, ths_bond_balance_bond,
               ths_valuate_full_price_cb_bond, ths_evaluate_net_price_cb_bond
        FROM {table_name}
        WHERE DT >= '{start_date}' AND DT <= '{end_date}'
        AND ths_bond_balance_bond IS NOT NULL
        AND ths_valuate_full_price_cb_bond IS NOT NULL
        AND ths_evaluate_net_price_cb_bond IS NOT NULL
        ORDER BY DT, TRADE_CODE
    """
}

# ============================================================
# 工具函数
# ============================================================
def ensure_directories():
    """确保所有必要的目录都存在"""
    directories = [CACHE_DIR, OUTPUT_DIR, DATA_DIR, ASSETS_DIR]
    for directory in directories:
        pathlib.Path(directory).mkdir(parents=True, exist_ok=True)
    return True

def get_connection_strings():
    """获取数据库连接字符串"""
    pg_conn_str = f"postgresql://{PG_CONFIG['user']}:{PG_CONFIG['password']}@{PG_CONFIG['host']}:{PG_CONFIG['port']}/{PG_CONFIG['database']}"
    mysql_conn_str = f"mysql+pymysql://{MYSQL_CONFIG['user']}:{MYSQL_CONFIG['password']}@{MYSQL_CONFIG['host']}:{MYSQL_CONFIG['port']}/{MYSQL_CONFIG['database']}"
    return pg_conn_str, mysql_conn_str

def print_config():
    """打印当前配置（隐藏密码）"""
    print("=== T07 Configuration ===")
    print(f"PostgreSQL: {PG_CONFIG['host']}:{PG_CONFIG['port']}/{PG_CONFIG['database']}")
    print(f"MySQL: {MYSQL_CONFIG['host']}:{MYSQL_CONFIG['port']}/{MYSQL_CONFIG['database']}")
    print(f"Index Config: {INDEX_CONFIG}")
    print(f"Cache Dir: {CACHE_DIR}")
    print(f"Output Dir: {OUTPUT_DIR}")

if __name__ == "__main__":
    ensure_directories()
    print_config()
