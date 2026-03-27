# -*- coding: utf-8 -*-
"""
T56-企业预警通新闻爬取 配置文件
"""
import os

# 数据库配置 - 使用环境变量
DB_HOST = os.environ.get('DB_HOST', 'rm-uf6c8yi6zdq6ea7p1qo.mysql.rds.aliyuncs.com')
DB_PORT = os.environ.get('DB_PORT', '3306')
DB_USER = os.environ.get('DB_USER', 'hz_work')
DB_PASSWORD = os.environ.get('DB_PASSWORD', 'Hzinsights2015')

# 数据库连接字符串
DB_YQ_URL = f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/yq'

# 企业预警通API配置
QYYJT_BASE_URL = os.environ.get('QYYJT_BASE_URL', 'https://www.qyyjt.cn')
QYYJT_PC_USS = os.environ.get('QYYJT_PC_USS', '')  # 登录token

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
    'request_delay_min': 0.5,    # 最小请求间隔(秒)
    'request_delay_max': 2.0,    # 最大请求间隔(秒)
    'max_retries': 3,            # 最大重试次数
    'timeout': 30,               # 请求超时时间(秒)
    'batch_size': 100            # 批量保存大小
}

# 新闻爬取配置
NEWS_CONFIG = {
    'table_name': '地方政策新闻',
    'default_pagesize': 15,
    'topic_types': {
        'areaNews': '地方政策新闻',
        'bondMarket': '债券市场新闻',
        'policyDynamic': '政策动态'
    }
}
