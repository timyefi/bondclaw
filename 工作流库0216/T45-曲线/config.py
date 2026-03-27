# -*- coding: utf-8 -*-
"""
T45-曲线 配置文件
债券收益率曲线计算系统配置
"""

import os

# ============================================================
# 数据库连接配置（使用环境变量）
# ============================================================

# MySQL数据库配置
DB_HOST = os.environ.get('DB_HOST', 'rm-uf6c8yi6zdq6ea7p1qo.mysql.rds.aliyuncs.com')
DB_PORT = int(os.environ.get('DB_PORT', 3306))
DB_USER = os.environ.get('DB_USER', 'hz_work')
DB_PASSWORD = os.environ.get('DB_PASSWORD', 'Hzinsights2015')
DB_NAME = os.environ.get('DB_NAME', 'bond')

# PostgreSQL数据库配置（可选）
POSTGRES_HOST = os.environ.get('POSTGRES_HOST', '139.224.107.113')
POSTGRES_PORT = int(os.environ.get('POSTGRES_PORT', 18032))
POSTGRES_USER = os.environ.get('POSTGRES_USER', 'postgres')
POSTGRES_PASSWORD = os.environ.get('POSTGRES_PASSWORD', 'hzinsights2015')
POSTGRES_DBNAME = os.environ.get('POSTGRES_DBNAME', 'tsdb')


def get_mysql_connection_string():
    """获取MySQL连接字符串"""
    return f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'


def get_postgres_connection_config():
    """获取PostgreSQL连接配置"""
    return {
        'host': POSTGRES_HOST,
        'user': POSTGRES_USER,
        'password': POSTGRES_PASSWORD,
        'dbname': POSTGRES_DBNAME,
        'port': POSTGRES_PORT
    }


# ============================================================
# 标准期限点定义（18个）
# ============================================================
# 期限单位：年
# 0: 即时利率
# 0.0833...: 1个月（30/365）
# 0.25: 3个月（90/365）
# 0.5: 6个月（180/365）
# 0.75: 9个月（270/365）
# 1-10: 1-10年
# 15, 20, 30: 长期限

STANDARD_TERMS = [
    0,                  # 即时利率
    0.083333333,        # 1个月
    0.24999999899999997,  # 3个月
    0.49999999799999995,  # 6个月
    0.749999997,        # 9个月
    1,                  # 1年
    2,                  # 2年
    3,                  # 3年
    4,                  # 4年
    5,                  # 5年
    6,                  # 6年
    7,                  # 7年
    8,                  # 8年
    9,                  # 9年
    10,                 # 10年
    15,                 # 15年
    20,                 # 20年
    30                  # 30年
]

# 常用目标期限点
TARGET_TERMS = [0.5, 1.0, 1.75, 2.0, 3.0, 4.0, 5.0]

# ============================================================
# 曲线分类配置
# ============================================================

# 债券大类
BOND_CATEGORIES = ['城投', '产业', '金融', 'ABS']

# 发行方式
ISSUE_METHODS = ['公募', '私募']

# 是否永续/二永
PERPETUAL_OPTIONS = ['是', '否']

# 隐含评级
RATING_LEVELS = ['AAA+', 'AAA', 'AAA-', 'AA+', 'AA', 'AA(2)', 'AA-']

# ============================================================
# 插值参数配置
# ============================================================

# 插值精度（小数位数）
INTERPOLATION_PRECISION = 4

# 期限差异容忍度（年）
TERM_DIFFERENCE_TOLERANCE = 2

# ============================================================
# 数据筛选配置
# ============================================================

# 有效评级列表
VALID_RATINGS = ['AA', 'AA-', 'AA+', 'AA(2)', 'AAA-', 'AAA+', 'AAA']

# 最小收益率阈值
MIN_YIELD_THRESHOLD = 0

# ============================================================
# 期限映射配置
# ============================================================
# 用于将久期映射到标准期限点

def get_term_from_duration(duration):
    """
    根据久期获取对应的标准期限点

    Parameters:
    -----------
    duration : float
        债券久期

    Returns:
    --------
    float
        对应的标准期限点
    """
    if duration < 0.125:
        return 0.083
    elif duration < 0.375:
        return 0.25
    elif duration < 0.625:
        return 0.5
    elif duration < 0.875:
        return 0.75
    elif duration < 1.5:
        return 1
    elif duration < 2.5:
        return 2
    elif duration < 3.5:
        return 3
    elif duration < 4.5:
        return 4
    elif duration < 6:
        return 5
    elif duration < 8.5:
        return 7
    elif duration < 12.5:
        return 10
    elif duration < 17.5:
        return 15
    elif duration < 25:
        return 20
    else:
        return 30
