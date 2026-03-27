# -*- coding: utf-8 -*-
"""
T58-图片提取数据 配置文件
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
OUTPUT_DIR = './output'

# 图像处理参数
COLOR_TOLERANCE = 25  # 颜色容差范围
MIN_GRAY_VALUE = 150  # 最小灰度值
MAX_GRAY_VALUE = 200  # 最大灰度值

# 项目信息
PROJECT_NAME = '图片提取数据'
PROJECT_VERSION = '1.0.0'
