# -*- coding: utf-8 -*-
"""
T61-指标库整理 配置文件
"""
import os

# MySQL数据库配置 - 使用环境变量获取敏感信息
DB_USER = os.environ.get('DB_USER', 'hz_work')
DB_PASSWORD = os.environ.get('DB_PASSWORD', 'Hzinsights2015')
DB_HOST = os.environ.get('DB_HOST', 'rm-uf6c8yi6zdq6ea7p1qo.mysql.rds.aliyuncs.com')
DB_PORT = os.environ.get('DB_PORT', '3306')
DB_NAME = os.environ.get('DB_NAME', 'bond')

# MySQL数据库连接字符串
DATABASE_URL = f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'

# PostgreSQL配置
PG_USER = os.environ.get('PG_USER', 'postgres')
PG_PASSWORD = os.environ.get('PG_PASSWORD', 'hzinsights2015')
PG_HOST = os.environ.get('PG_HOST', '139.224.107.113')
PG_PORT = os.environ.get('PG_PORT', '18032')
PG_NAME = os.environ.get('PG_NAME', 'tsdb')

POSTGRESQL_URL = f'postgresql://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{PG_NAME}'

# 文件路径配置
OUTPUT_DIR = './output'

# 融资成本计算参数
FINANCING_COST_MIN = 2.0  # 融资成本最小值(%)
FINANCING_COST_MAX = 8.0  # 融资成本最大值(%)
BOND_COST_MAX = 20.0  # 债券融资成本最大值(%)

# 项目信息
PROJECT_NAME = '指标库整理'
PROJECT_VERSION = '1.0.0'
