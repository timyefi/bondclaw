# -*- coding: utf-8 -*-
"""
T59-微信采集 配置文件
使用 os.environ.get() 处理敏感信息
"""
import os

# 数据库配置
DB_USER = os.environ.get('DB_USER', 'hz_work')
DB_PASSWORD = os.environ.get('DB_PASSWORD', 'Hzinsights2015')
DB_HOST = os.environ.get('DB_HOST', 'rm-uf6c8yi6zdq6ea7p1qo.mysql.rds.aliyuncs.com')
DB_PORT = os.environ.get('DB_PORT', '3306')
DB_NAME = os.environ.get('DB_NAME', 'yq')

# 同花顺iFinD配置
THS_USERNAME = os.environ.get('THS_USERNAME', 'nylc082')
THS_PASSWORD = os.environ.get('THS_PASSWORD', '491448')

# 数据库连接字符串
def get_db_connection_string():
    return f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'

# 微信采集配置
WECHAT_GROUPS_TO_MONITOR = ["华泰固收同业"]
WECHAT_CONTACTS_TO_MONITOR = ["银行"]
WECHAT_PUBLIC_ACCOUNTS_TO_MONITOR = ["公众号1", "公众号2"]

# 文件保存路径
OUTPUT_DIR = r'C:\Users\Administrator\iCloudDrive\quickinfo'
LIBRARY_DIR = r'C:\Users\Administrator\WPSDrive\389717562\WPS云盘\WPS\lib'
