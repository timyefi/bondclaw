# -*- coding: utf-8 -*-
"""
T65-自动总结文档内容 配置文件
使用 os.environ.get() 处理敏感信息
"""
import os

# 数据库配置 - 主数据库
DB_USER = os.environ.get('DB_USER', 'hz_work')
DB_PASSWORD = os.environ.get('DB_PASSWORD', 'Hzinsights2015')
DB_HOST = os.environ.get('DB_HOST', 'rm-uf6c8yi6zdq6ea7p1qo.mysql.rds.aliyuncs.com')
DB_PORT = os.environ.get('DB_PORT', '3306')
DB_NAME = os.environ.get('DB_NAME', 'yq')

# 数据库配置 - 信息库
INFO_DB_USER = os.environ.get('INFO_DB_USER', 'tim')
INFO_DB_PASSWORD = os.environ.get('INFO_DB_PASSWORD', 'abcd0513')
INFO_DB_HOST = os.environ.get('INFO_DB_HOST', '139.196.19.26')
INFO_DB_PORT = os.environ.get('INFO_DB_PORT', '51213')
INFO_DB_NAME = os.environ.get('INFO_DB_NAME', 'timinfo')

# 数据库连接字符串
def get_db_connection_string():
    return f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'

def get_info_db_connection_string():
    return f'mysql+pymysql://{INFO_DB_USER}:{INFO_DB_PASSWORD}@{INFO_DB_HOST}:{INFO_DB_PORT}/{INFO_DB_NAME}'

# 阿里云 Qwen-Long API 配置
QWEN_API_KEY = os.environ.get('QWEN_API_KEY', 'sk-f4f4de7b9a3f4dbcbab21012757d4fca')
QWEN_BASE_URL = os.environ.get('QWEN_BASE_URL', 'https://dashscope.aliyuncs.com/compatible-mode/v1')

# 邮件配置
SMTP_SERVER = os.environ.get('SMTP_SERVER', 'smtp.qq.com')
SMTP_PORT = int(os.environ.get('SMTP_PORT', '465'))
EMAIL_USER = os.environ.get('EMAIL_USER', '917952467@qq.com')
EMAIL_PASSWORD = os.environ.get('EMAIL_PASSWORD', 'ineaylzljuqdbgai')
RECIPIENT_EMAIL = os.environ.get('RECIPIENT_EMAIL', 'tim.ye@foxmail.com')

# 文件路径配置
INPUT_FOLDERS = [
    r'C:\Users\Administrator\iCloudDrive\quickinfo',
    r'C:\Users\Administrator\WPSDrive\389717562\WPS云盘\WPS\quick'
]
OUTPUT_FOLDER = r'C:\Users\Administrator\WPSDrive\389717562\WPS云盘\WPS\lib'
LIBRARY_FOLDER = r'C:\Users\Administrator\iCloudDrive\lib'

# 敏感词库文件路径
SENSITIVE_WORDS_FILE = r'C:\daily\sensitive_word_dict.txt'

# PaddleOCR模型路径
PADDLE_DET_MODEL = './pretrain_models/ch_PP-OCRv3_det_infer/'
PADDLE_REC_MODEL = './pretrain_models/ch_ppocr_server_v2.0_rec_pre/best_accuracy'
PADDLE_CLS_MODEL = './pretrain_models/ch_ppocr_mobile_v2.0_cls_infer/'
