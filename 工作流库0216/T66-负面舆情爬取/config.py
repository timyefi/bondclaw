# -*- coding: utf-8 -*-
"""
T66-负面舆情爬取 配置文件
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

# Ratingdog API配置
RATINGDOG_LOGIN_URL = 'https://auth.ratingdog.cn/api/TokenAuth/Authenticate'
RATINGDOG_API_URL = 'https://host.ratingdog.cn/api/services/app/ResearchInfo'

# Ratingdog登录凭据
RATINGDOG_USERNAME = os.environ.get('RATINGDOG_USERNAME', '13918339361')
RATINGDOG_PHONE_CODE = os.environ.get('RATINGDOG_PHONE_CODE', '86')
RATINGDOG_PASSWORD = os.environ.get('RATINGDOG_PASSWORD', 'welcome@1')
RATINGDOG_TENANT_ID = os.environ.get('RATINGDOG_TENANT_ID', '114')

# 请求配置
REQUEST_TIMEOUT = 30
DEFAULT_PAGE_SIZE = 30

# 代码库路径（用于导入timai模块）
CODE_LIBRARY_PATH = r'C:\Users\Administrator\WPSDrive\389717562\WPS云盘\WPS\代码库'

# PDF下载目录
PDF_DOWNLOAD_DIR = r'D:\2024年\企业预警通\舆情PDF'

# OCR模型路径
OCR_DET_MODEL = './pretrain_models/ch_PP-OCRv3_det_infer/'
OCR_REC_MODEL = './pretrain_models/ch_ppocr_server_v2.0_rec_pre/best_accuracy'
OCR_CLS_MODEL = './pretrain_models/ch_ppocr_mobile_v2.0_cls_infer/'
