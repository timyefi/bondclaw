# -*- coding: utf-8 -*-
"""
T57-企业预警通爬取 配置文件
"""
import os

# 数据库配置 - 使用环境变量
DB_HOST = os.environ.get('DB_HOST', 'rm-uf6c8yi6zdq6ea7p1qo.mysql.rds.aliyuncs.com')
DB_PORT = os.environ.get('DB_PORT', '3306')
DB_USER = os.environ.get('DB_USER', 'hz_work')
DB_PASSWORD = os.environ.get('DB_PASSWORD', 'Hzinsights2015')

# 数据库连接字符串
DB_YQ_URL = f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/yq'

# 企业预警通配置
QYYJT_BASE_URL = os.environ.get('QYYJT_BASE_URL', 'https://www.qyyjt.cn')
QYYJT_USERNAME = os.environ.get('QYYJT_USERNAME', '')  # 登录用户名
QYYJT_PASSWORD = os.environ.get('QYYJT_PASSWORD', '')  # 登录密码

# 路径配置
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
OUTPUT_DIR = os.path.join(BASE_DIR, 'output')
ASSETS_DIR = os.path.join(BASE_DIR, 'assets')

# 确保目录存在
for dir_path in [DATA_DIR, OUTPUT_DIR, ASSETS_DIR]:
    os.makedirs(dir_path, exist_ok=True)

# 爬虫配置
SPIDER_CONFIG = {
    'request_delay_min': 0.5,
    'request_delay_max': 2.0,
    'max_retries': 3,
    'timeout': 30,
    'use_selenium': False  # 是否使用Selenium
}

# 数据模块配置
DATA_MODULES = {
    'market_entity': {
        'name': '市场化经营主体',
        'url': '/bond/newExitTopic/mark',
        'dataid': '578'
    },
    'exit_platform': {
        'name': '退出平台',
        'url': '/bond/newExitTopic/exit',
        'dataid': '579'
    },
    'market_operation': {
        'name': '市场化经营',
        'url': '/bond/newExitTopic/mark',
        'dataid': '580'
    }
}
