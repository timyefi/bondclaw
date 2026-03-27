# -*- coding: utf-8 -*-
"""
T54-产业高频跟踪 配置文件
"""
import os

# 数据库配置 - 使用环境变量
DB_HOST = os.environ.get('DB_HOST', 'rm-uf6c8yi6zdq6ea7p1qo.mysql.rds.aliyuncs.com')
DB_PORT = os.environ.get('DB_PORT', '3306')
DB_USER = os.environ.get('DB_USER', 'hz_work')
DB_PASSWORD = os.environ.get('DB_PASSWORD', 'Hzinsights2015')

# 数据库连接字符串
DB_BOND_URL = f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/bond'
DB_STOCK_URL = f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/stock'
DB_YQ_URL = f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/yq'

# PostgreSQL配置
PG_HOST = os.environ.get('PG_HOST', '139.224.107.113')
PG_PORT = os.environ.get('PG_PORT', '18032')
PG_USER = os.environ.get('PG_USER', 'postgres')
PG_PASSWORD = os.environ.get('PG_PASSWORD', 'hzinsights2015')
PG_DB = os.environ.get('PG_DB', 'tsdb')

PG_URL = f'postgresql://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{PG_DB}'

# 路径配置
import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
OUTPUT_DIR = os.path.join(BASE_DIR, 'output')
ASSETS_DIR = os.path.join(BASE_DIR, 'assets')

# 确保目录存在
for dir_path in [DATA_DIR, OUTPUT_DIR, ASSETS_DIR]:
    os.makedirs(dir_path, exist_ok=True)

# 产业跟踪配置
INDUSTRY_WINDOW_CONFIG = {
    '周期天数': 365,  # 默认周期天数
    '趋势天数': 90,   # 默认趋势天数
    'level': 3        # 小波分解层级
}
