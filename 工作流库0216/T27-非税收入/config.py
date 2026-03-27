# -*- coding: utf-8 -*-
"""
T27-非税收入 配置文件
"""
import os

# 数据库配置 - 使用环境变量获取敏感信息
DB_USER = os.environ.get('DB_USER', 'hz_work')
DB_PASSWORD = os.environ.get('DB_PASSWORD', 'Hzinsights2015')
DB_HOST = os.environ.get('DB_HOST', 'rm-uf6c8yi6zdq6ea7p1qo.mysql.rds.aliyuncs.com')
DB_PORT = os.environ.get('DB_PORT', '3306')
DB_NAME = os.environ.get('DB_NAME', 'yq')

# 数据库连接字符串
DATABASE_URL = f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'

# 文件路径配置
INPUT_FILE = '一般公共预算收入累计值等.xlsx'
OUTPUT_DIR = './output'

# 项目信息
PROJECT_NAME = '非税收入'
PROJECT_VERSION = '1.0.0'
