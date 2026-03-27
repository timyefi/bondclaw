#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图表复制工作流配置文件

该模块包含数据库连接配置、计算参数和其他配置项。
所有敏感信息通过环境变量获取，避免硬编码。
"""

import os
import sqlalchemy
from sqlalchemy import create_engine

# =============================================================================
# 数据库配置
# =============================================================================

# 数据库连接参数（从环境变量获取，提供默认值）
DB_HOST = os.environ.get('DB_HOST', 'rm-uf6c8yi6zdq6ea7p1qo.mysql.rds.aliyuncs.com')
DB_PORT = os.environ.get('DB_PORT', '3306')
DB_USER = os.environ.get('DB_USER', 'hz_work')
DB_PASSWORD = os.environ.get('DB_PASSWORD', '')  # 密码必须通过环境变量设置
DB_NAME = os.environ.get('DB_NAME', 'yq')

# =============================================================================
# 计算参数
# =============================================================================

# 基准日期
BASE_DATE = '2020-11-12'

# 目标基准值
TARGET_BASE_VALUE = 0.09427710843373494

# 交易代码列表
TRADE_CODES = [
    'CRB CMDT Index',      # CRB商品指数
    'FLOT US Equity',      # 美国股票指数
    '.EARNREV G Index'     # 盈利修正指数
]

# 目标表名
TARGET_TABLE_NAME = '全球实物资产比金融资产'

# =============================================================================
# 图像处理配置
# =============================================================================

# 默认数据点频率 ('week', 'month', 'year')
DEFAULT_FREQUENCY = 'week'

# 样本点缓存文件路径
SAMPLE_POINTS_CACHE_FILE = 'sample_points_cache.json'

# 结果图像输出路径
DETECTED_POINTS_OUTPUT = 'detected_points.png'

# =============================================================================
# 工具函数
# =============================================================================

def get_database_engine():
    """
    创建并返回数据库引擎

    返回:
        sqlalchemy.engine: 数据库引擎实例
    """
    if not DB_PASSWORD:
        raise ValueError(
            "数据库密码未设置。请设置环境变量 DB_PASSWORD 或在代码中提供密码。"
        )

    connection_string = f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'

    engine = create_engine(
        connection_string,
        poolclass=sqlalchemy.pool.NullPool,
        pool_recycle=3600  # 1小时后回收连接，防止超时
    )

    return engine


def get_database_config():
    """
    获取数据库配置字典

    返回:
        dict: 数据库配置信息
    """
    return {
        'host': DB_HOST,
        'port': DB_PORT,
        'user': DB_USER,
        'password': DB_PASSWORD,
        'database': DB_NAME
    }


def validate_config():
    """
    验证配置是否完整

    返回:
        tuple: (is_valid, missing_items)
    """
    missing = []

    if not DB_PASSWORD:
        missing.append('DB_PASSWORD')

    return len(missing) == 0, missing


# =============================================================================
# 配置验证
# =============================================================================

if __name__ == '__main__':
    print("=" * 50)
    print("图表复制工作流配置信息")
    print("=" * 50)
    print(f"数据库主机: {DB_HOST}")
    print(f"数据库端口: {DB_PORT}")
    print(f"数据库用户: {DB_USER}")
    print(f"数据库名称: {DB_NAME}")
    print(f"数据库密码: {'已设置' if DB_PASSWORD else '未设置'}")
    print(f"基准日期: {BASE_DATE}")
    print(f"目标基准值: {TARGET_BASE_VALUE}")
    print(f"交易代码: {TRADE_CODES}")
    print(f"目标表名: {TARGET_TABLE_NAME}")
    print("=" * 50)

    # 验证配置
    is_valid, missing = validate_config()
    if is_valid:
        print("配置验证通过")
    else:
        print(f"配置缺失项: {missing}")
        print("请设置相应的环境变量")
