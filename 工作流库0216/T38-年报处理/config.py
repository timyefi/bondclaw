# -*- coding: utf-8 -*-
"""
T38-年报处理 配置文件
使用环境变量管理敏感信息，避免硬编码密码
"""

import os
from dotenv import load_dotenv

# 加载.env文件中的环境变量
load_dotenv()

# ============================================================
# 数据库配置
# ============================================================

# 主数据库配置 (yq数据库)
DB_YQ_USER = os.getenv('DB_YQ_USER', 'hz_work')
DB_YQ_PASSWORD = os.getenv('DB_YQ_PASSWORD', '')
DB_YQ_HOST = os.getenv('DB_YQ_HOST', 'rm-uf6c8yi6zdq6ea7p1qo.mysql.rds.aliyuncs.com')
DB_YQ_PORT = os.getenv('DB_YQ_PORT', '3306')
DB_YQ_DATABASE = os.getenv('DB_YQ_DATABASE', 'yq')

# 备份数据库配置 (timinfo数据库)
DB_TIMINFO_USER = os.getenv('DB_TIMINFO_USER', 'root')
DB_TIMINFO_PASSWORD = os.getenv('DB_TIMINFO_PASSWORD', '')
DB_TIMINFO_HOST = os.getenv('DB_TIMINFO_HOST', 'bja.sealos.run')
DB_TIMINFO_PORT = os.getenv('DB_TIMINFO_PORT', '44525')
DB_TIMINFO_DATABASE = os.getenv('DB_TIMINFO_DATABASE', 'timinfo')


def get_yq_connection_string():
    """获取yq数据库连接字符串"""
    return f'mysql+pymysql://{DB_YQ_USER}:{DB_YQ_PASSWORD}@{DB_YQ_HOST}:{DB_YQ_PORT}/{DB_YQ_DATABASE}'


def get_timinfo_connection_string():
    """获取timinfo数据库连接字符串"""
    return f'mysql+pymysql://{DB_TIMINFO_USER}:{DB_TIMINFO_PASSWORD}@{DB_TIMINFO_HOST}:{DB_TIMINFO_PORT}/{DB_TIMINFO_DATABASE}'


# ============================================================
# API配置
# ============================================================

# 企业预警通API配置
QYYJT_BASE_URL = os.getenv('QYYJT_BASE_URL', 'https://www.qyyjt.cn')
QYYJT_API_URL = f'{QYYJT_BASE_URL}/getData.action'

# 通义千问API配置
QWEN_API_KEY = os.getenv('QWEN_API_KEY', '')
QWEN_BASE_URL = os.getenv('QWEN_BASE_URL', 'https://dashscope.aliyuncs.com/compatible-mode/v1')
QWEN_MODEL = os.getenv('QWEN_MODEL', 'qwen-long')

# 百度OCR API配置
BAIDU_OCR_API_KEY = os.getenv('BAIDU_OCR_API_KEY', '')
BAIDU_OCR_SECRET_KEY = os.getenv('BAIDU_OCR_SECRET_KEY', '')

# 巨潮资讯API配置
CNINFO_BASE_URL = os.getenv('CNINFO_BASE_URL', 'http://www.cninfo.com.cn')


# ============================================================
# 文件路径配置
# ============================================================

# PDF存储路径
PDF_STORAGE_PATH = os.getenv('PDF_STORAGE_PATH', r'D:\2024年\企业预警通')

# OCR待处理文件夹
OCR_PENDING_PATH = os.getenv('OCR_PENDING_PATH', r'D:\2024年\企业预警通\待ocr')

# 已处理文件夹
PROCESSED_PATH = os.getenv('PROCESSED_PATH', r'D:\2024年\年报扫描\已处理')

# 小文件存储路径
SMALL_FILE_PATH = os.getenv('SMALL_FILE_PATH', r'D:\2024年\小文件')


# ============================================================
# 年报处理配置
# ============================================================

ANNUAL_REPORT_CONFIG = {
    # 数据源
    'data_sources': ['QYYJT', 'CNINFO', 'SSE', 'SZSE'],

    # 支持的文件格式
    'supported_formats': ['PDF'],

    # OCR提取方法
    'extraction_methods': ['pdfplumber', 'baidu_ocr', 'pymupdf'],

    # 财务报表类型
    'financial_statements': [
        '审计报告',
        '资产负债表',
        '利润表',
        '现金流量表',
        '所有者权益变动表'
    ],

    # 关键财务指标
    'key_indicators': [
        '营业收入',
        '净利润',
        '资产总计',
        '负债合计',
        '所有者权益合计',
        '销售毛利率',
        '净利率',
        '股东分红',
        '资本公积增加'
    ],

    # 年报文件匹配正则
    'report_patterns': {
        'include': r'审计报告|年度报告|年报|报表|财务',
        'exclude': r'专项审计|摘要|page|风险提示|提示性|补充公告|更正|鉴证报告|代理事务|增信|担保|监管|说明|英文|半年|三季度|一季度|债券|证券化|资产支持',
        'year': r'2023|2024'
    },

    # NLP分析任务
    'nlp_tasks': [
        'md_a_analysis',
        'risk_factor_extraction',
        'sentiment_analysis',
        'capital_reserve_extraction',
        'dividend_extraction'
    ],

    # 请求配置
    'request': {
        'timeout': 30,
        'retry_times': 3,
        'retry_delay': (0.5, 1.0),  # 随机延迟范围
        'page_size': 50
    },

    # 大模型提取Prompt
    'extraction_prompt': '''
作为高级财务信息筛选师，您的任务是依据严格的财务准则，精准提取并总结财务报表摘要中不同年份的两个核心财务板块信息：股东分红与资本公积增加。

## 股东分红
- **项目列：** 统一标记为"股东分红"
- **统计范围：** 分配、应付、提取、派发的股利、分配红利、分配现金股利、分配普通股股利、分配优先股股利、上缴收入、上缴利润、上缴股利、其他权益工具股利
- **不考虑：** 股票股利
- **特殊处理：** 永续债付息、永续债利息、可续期公司债利息（单独统计）

## 资本公积增加
- **项目列：** 统一为"资本公积增加"
- **统计范围：** 仅考虑资本公积增加、增长，不考虑减少
- **增加原因：** 政府现金拨款、股权无偿划转、资产评估增值、项目移交、其他
- **不包括：** 盈余公积、股本、注册资本、其他综合收益、其他收益、股权认缴、增资扩股、递延收益、其他权益工具

## 时间标识
- "2024年"（当期/当年/本年/今年）= 2024年度
- "2023年"（上一期/上年/去年/上期）= 2023年度

## 金额处理
- **原始金额：** 保留数字，例如：12345
- **原始金额单位：** 展示其原始单位，例如：元
- **金额列：** 转换为"亿"单位
  - 元 → 亿：除以100000000
  - 万 → 亿：除以10000
  - 百万 → 亿：除以100

## 输出格式
年份|项目|增加原因|金额|原始金额|原始金额单位
'''
}


# ============================================================
# 数据库表配置
# ============================================================

DATABASE_TABLES = {
    # 年报文件记录表
    'annual_report_files': 'yq.23年财报文件',

    # 年报提取结果表
    'extraction_results': 'yq.年报提取结果',

    # 资本公积表
    'capital_reserve': 'yq.资本公积',

    # 债券基础信息表
    'bond_basicinfo': 'bond.basicinfo_credit',

    # 债券代码临时表
    'trade_code_temp': 'financialinfo.trade_code_temp1'
}


# ============================================================
# 日志配置
# ============================================================

LOG_CONFIG = {
    'level': os.getenv('LOG_LEVEL', 'INFO'),
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'file': os.getenv('LOG_FILE', 'annual_report_processing.log')
}


# ============================================================
# 验证配置完整性
# ============================================================

def validate_config():
    """验证必要的配置是否完整"""
    required_vars = [
        ('DB_YQ_PASSWORD', DB_YQ_PASSWORD),
        ('QWEN_API_KEY', QWEN_API_KEY),
    ]

    missing = []
    for name, value in required_vars:
        if not value:
            missing.append(name)

    if missing:
        print(f"警告: 以下环境变量未设置: {', '.join(missing)}")
        print("请创建.env文件或设置相应的环境变量")

    return len(missing) == 0


if __name__ == '__main__':
    # 测试配置
    print("数据库连接字符串 (yq):", get_yq_connection_string())
    print("数据库连接字符串 (timinfo):", get_timinfo_connection_string())
    print("企业预警通API地址:", QYYJT_API_URL)
    print("通义千问API地址:", QWEN_BASE_URL)
    validate_config()
