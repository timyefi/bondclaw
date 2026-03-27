# -*- coding: utf-8 -*-
"""
T60-投资者行为 配置文件
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
INPUT_FILE = '20240514.xlsx'
OUTPUT_DIR = './output'

# 数据源配置
# 上交所
SSE_URL_TEMPLATE = "http://query.sse.com.cn/commonQuery.do?jsonCallBack=jsonpCallback73603&isPagination=false&sqlId=COMMON_BOND_SCSJ_SCTJ_TJYB_CYJG_L&TRADEDATE={trade_date}&_={timestamp}"

# 深交所
SZSE_URL_TEMPLATE = "https://bond.szse.cn/api/report/ShowReport/data?SHOWTYPE=JSON&CATALOGID=zqxqcyyb_after&TABKEY=tab1&jyrqStart={trade_date}&jyrqEnd=2016-01&random={random}"

# 中债
CCDC_URL = "https://www.chinabond.com.cn/cbiw/GetMonthReport/GetDataByte"

# 上清所
SHCH_URL = "https://www.shclearing.com.cn/shchapp/web/sdocClient/monthListPage"

# 项目信息
PROJECT_NAME = '投资者行为'
PROJECT_VERSION = '1.0.0'
