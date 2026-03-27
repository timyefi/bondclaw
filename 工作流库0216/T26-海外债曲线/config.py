# -*- coding: utf-8 -*-
"""
T26-海外债曲线 配置文件
"""
import os

# 数据库配置 - 使用环境变量获取敏感信息
DB_USER = os.environ.get('DB_USER', 'hz_work')
DB_PASSWORD = os.environ.get('DB_PASSWORD', 'Hzinsights2015')
DB_HOST = os.environ.get('DB_HOST', 'rm-uf6c8yi6zdq6ea7p1qo.mysql.rds.aliyuncs.com')
DB_PORT = os.environ.get('DB_PORT', '3306')
DB_NAME = os.environ.get('DB_NAME', 'bond')

# 数据库连接字符串
DATABASE_URL = f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'

# PostgreSQL配置
PG_USER = os.environ.get('PG_USER', 'postgres')
PG_PASSWORD = os.environ.get('PG_PASSWORD', 'hzinsights2015')
PG_HOST = os.environ.get('PG_HOST', '139.224.107.113')
PG_PORT = os.environ.get('PG_PORT', '18032')
PG_NAME = os.environ.get('PG_NAME', 'tsdb')

POSTGRESQL_URL = f'postgresql://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{PG_NAME}'

# 文件路径配置
DATA_FILE = 'basicinfo_hk.xlsx'
OUTPUT_DIR = './output'

# 项目信息
PROJECT_NAME = '海外债曲线'
PROJECT_VERSION = '1.0.0'
