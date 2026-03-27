# -*- coding: utf-8 -*-
"""
T64-用益信托 配置文件
使用 os.environ.get() 处理敏感信息
"""
import os

# 数据库配置
DB_USER = os.environ.get('DB_USER', 'hz_work')
DB_PASSWORD = os.environ.get('DB_PASSWORD', 'Hzinsights2015')
DB_HOST = os.environ.get('DB_HOST', 'rm-uf6c8yi6zdq6ea7p1qo.mysql.rds.aliyuncs.com')
DB_PORT = os.environ.get('DB_PORT', '3306')
DB_NAME = os.environ.get('DB_NAME', 'yq')

# 数据库连接字符串
def get_db_connection_string():
    return f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'

# 用益信托API配置
USETRUST_BASE_URL = 'https://www.usetrust.com'
USETRUST_API_URL = f'{USETRUST_BASE_URL}/Action/AjaxAction.ashx'
USETRUST_DETAIL_URL = f'{USETRUST_BASE_URL}/Studio/Details.aspx'

# 请求配置
REQUEST_TIMEOUT = 20
DEFAULT_PAGE_SIZE = 10
DEFAULT_PARENT_ID = '1050240046'  # 标品信托相关分类ID

# 请求头配置
def get_request_headers():
    return {
        'Accept': '*/*',
        'Accept-Encoding': 'gzip, deflate, br, zstd',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
        'Connection': 'keep-alive',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'Host': 'www.usetrust.com',
        'Origin': 'https://www.usetrust.com',
        'Referer': 'https://www.usetrust.com/studio/',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'X-Requested-With': 'XMLHttpRequest'
    }
