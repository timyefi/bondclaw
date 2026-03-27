# -*- coding: utf-8 -*-
"""
T55-企业预警通导入重点指标 配置文件
"""
import os

# 数据库配置 - 使用环境变量
DB_HOST = os.environ.get('DB_HOST', 'rm-uf6c8yi6zdq6ea7p1qo.mysql.rds.aliyuncs.com')
DB_PORT = os.environ.get('DB_PORT', '3306')
DB_USER = os.environ.get('DB_USER', 'hz_work')
DB_PASSWORD = os.environ.get('DB_PASSWORD', 'Hzinsights2015')

# 数据库连接字符串
DB_BOND_URL = f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/bond'

# PostgreSQL配置
PG_HOST = os.environ.get('PG_HOST', '139.224.107.113')
PG_PORT = os.environ.get('PG_PORT', '18032')
PG_USER = os.environ.get('PG_USER', 'postgres')
PG_PASSWORD = os.environ.get('PG_PASSWORD', 'hzinsights2015')
PG_DB = os.environ.get('PG_DB', 'tsdb')

PG_URL = f'postgresql://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{PG_DB}'

# 路径配置
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
OUTPUT_DIR = os.path.join(BASE_DIR, 'output')
ASSETS_DIR = os.path.join(BASE_DIR, 'assets')

# 确保目录存在
for dir_path in [DATA_DIR, OUTPUT_DIR, ASSETS_DIR]:
    os.makedirs(dir_path, exist_ok=True)

# 数据导入配置
IMPORT_CONFIG = {
    'target_table': '指标数据1',  # 目标表名
    'batch_size': 1000,           # 批量导入大小
    'skip_errors': True           # 是否跳过错误继续导入
}
