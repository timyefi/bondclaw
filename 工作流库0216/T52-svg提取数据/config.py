# -*- coding: utf-8 -*-
"""
SVG数据提取配置文件

该模块包含SVG数据提取项目的配置信息
"""

import os
import sqlalchemy
import sqlalchemy.pool


def get_database_config():
    """
    获取数据库配置

    从环境变量读取数据库连接信息

    返回:
        dict: 数据库配置字典
    """
    return {
        'host': os.environ.get('DB_HOST', ''),
        'port': int(os.environ.get('DB_PORT', 3306)),
        'user': os.environ.get('DB_USER', ''),
        'password': os.environ.get('DB_PASSWORD', ''),
        'database': os.environ.get('DB_NAME', ''),
    }


def get_database_engine():
    """
    创建并返回数据库引擎

    返回:
        SQLAlchemy Engine: 数据库连接引擎
    """
    config = get_database_config()
    connection_string = 'mysql+pymysql://{user}:{password}@{host}:{port}/{database}'.format(
        user=config['user'],
        password=config['password'],
        host=config['host'],
        port=config['port'],
        database=config['database'],
    )
    return sqlalchemy.create_engine(connection_string, poolclass=sqlalchemy.pool.NullPool)


def get_known_points():
    """
    获取已知点配置

    已知点用于SVG坐标到实际数值的线性插值
    格式: [(svg_y, actual_y), ...]

    返回:
        list: 已知点列表
    """
    return [
        (-68, -18.6),   # 最小值点
        (83, 22.7),     # 中间值点
        (186, 51.1)     # 最大值点
    ]


def get_x_axis_config():
    """
    获取X轴配置

    返回:
        dict: X轴配置字典
    """
    return {
        'start_year': 1968,
        'start_month': 5,
        'end_year': 2024,
        'end_month': 5,
    }


# 数据库连接（向后兼容）
def get_legacy_connection():
    """
    获取旧版数据库连接

    不推荐使用，建议使用get_database_engine()

    返回:
        SQLAlchemy Connection: 数据库连接
    """
    engine = get_database_engine()
    return engine.connect()


# 默认已知点（向后兼容）
KNOWN_POINTS = get_known_points()

# 默认X轴配置（向后兼容）
X_AXIS_CONFIG = get_x_axis_config()
